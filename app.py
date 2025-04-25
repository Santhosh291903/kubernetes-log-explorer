from flask import Flask, render_template, request, jsonify
from kubernetes import client, config
from kubernetes.client import ApiException
import os

app = Flask(__name__)

# Configure Kubernetes client
try:
    config.load_incluster_config()  # For running in-cluster
except config.ConfigException:
    try:
        config.load_kube_config()  # For local development
    except config.ConfigException:
        raise Exception("Could not configure Kubernetes python client")

v1 = client.CoreV1Api()

@app.route('/')
def index():
    try:
        contexts, active_context = config.list_kube_config_contexts()
        namespaces = v1.list_namespace()
        namespace_list = [ns.metadata.name for ns in namespaces.items]
        
        return render_template('index.html',
                            current_context=active_context['name'],
                            namespaces=namespace_list)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/get_pods', methods=['POST'])
def get_pods():
    try:
        namespace = request.form['namespace']
        pods = v1.list_namespaced_pod(namespace=namespace)
        pod_list = [{'name': pod.metadata.name, 'status': pod.status.phase} for pod in pods.items]
        return jsonify({'pods': pod_list})
    except ApiException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_logs', methods=['POST'])
def get_logs():
    try:
        namespace = request.form['namespace']
        pod_name = request.form['pod_name']
        tail_lines = int(request.form.get('tail_lines', 20))
        
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines
        )
        
        return jsonify({
            'logs': logs,
            'pod': pod_name,
            'namespace': namespace,
            'tail_lines': tail_lines
        })
    except ApiException as e:
        return jsonify({'error': str(e)}), 500

def create_templates():
    os.makedirs('templates', exist_ok=True)
    
    # index.html
    with open('templates/index.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Log Viewer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f5f5f5; padding: 20px; }
        .log-container {
            background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #444;
            border-radius: 5px; padding: 15px; font-family: 'Courier New', monospace;
            white-space: pre-wrap; height: 70vh; overflow-y: auto; margin-top: 20px;
            font-size: 14px; line-height: 1.5;
        }
        .form-container {
            background-color: #fff; border-radius: 5px; padding: 20px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        .log-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .log-title { font-weight: bold; color: #333; }
        .log-info { color: #666; font-size: 0.9em; }
        .form-label { font-weight: 500; }
        .btn-refresh { margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="mb-4">Kubernetes Log Viewer</h1>
        <div class="row">
            <div class="col-md-4">
                <div class="form-container">
                    <form id="logForm">
                        <div class="mb-3">
                            <label for="context" class="form-label">Cluster Context</label>
                            <select class="form-select" id="context" disabled>
                                <option>{{ current_context }}</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="namespace" class="form-label">Namespace</label>
                            <select class="form-select" id="namespace" required>
                                {% for ns in namespaces %}
                                <option value="{{ ns }}">{{ ns }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="pod" class="form-label">Pod</label>
                            <select class="form-select" id="pod" required disabled>
                                <option value="">Select a namespace first</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="tail_lines" class="form-label">Log Lines to Show</label>
                            <select class="form-select" id="tail_lines">
                                <option value="20">20 lines</option>
                                <option value="50">50 lines</option>
                                <option value="100">100 lines</option>
                                <option value="200">200 lines</option>
                                <option value="500">500 lines</option>
                                <option value="1000">1000 lines</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Get Logs</button>
                    </form>
                </div>
            </div>
            <div class="col-md-8">
                <div class="log-header">
                    <div>
                        <span class="log-title">Log Output</span>
                        <button id="refreshBtn" class="btn btn-sm btn-secondary btn-refresh" disabled>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
                                <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
                            </svg>
                        </button>
                    </div>
                    <span class="log-info" id="logInfo"></span>
                </div>
                <div class="log-container" id="logOutput">
                    Select a pod and click "Get Logs" to view logs here...
                </div>
            </div>
        </div>
    </div>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        $(document).ready(function() {
            let currentPod = null;
            let currentNamespace = null;
            let currentTailLines = null;
            
            $('#namespace').change(function() {
                const namespace = $(this).val();
                if (namespace) {
                    $('#pod').prop('disabled', true).html('<option value="">Loading pods...</option>');
                    $.post('/get_pods', {namespace: namespace}, function(data) {
                        if (data.error) {
                            $('#pod').html(`<option value="">Error: ${data.error}</option>`);
                        } else {
                            let options = '<option value="">Select a pod</option>';
                            data.pods.forEach(pod => {
                                options += `<option value="${pod.name}">${pod.name} (${pod.status})</option>`;
                            });
                            $('#pod').html(options).prop('disabled', false);
                        }
                    }).fail(function() {
                        $('#pod').html('<option value="">Error loading pods</option>');
                    });
                }
            });
            
            function fetchLogs() {
                if (!currentNamespace || !currentPod) return;
                $('#logOutput').html('<div class="text-center py-5">Loading logs...</div>');
                $('#logInfo').text('');
                $.post('/get_logs', {
                    namespace: currentNamespace,
                    pod_name: currentPod,
                    tail_lines: currentTailLines
                }, function(data) {
                    if (data.error) {
                        $('#logOutput').html(`<div class="text-danger">Error: ${data.error}</div>`);
                        $('#refreshBtn').prop('disabled', true);
                    } else {
                        $('#logOutput').text(data.logs);
                        $('#logInfo').text(`Showing last ${data.tail_lines} lines from ${data.namespace}/${data.pod}`);
                        document.getElementById('logOutput').scrollTop = document.getElementById('logOutput').scrollHeight;
                        $('#refreshBtn').prop('disabled', false);
                    }
                }).fail(function() {
                    $('#logOutput').html('<div class="text-danger">Error fetching logs</div>');
                    $('#refreshBtn').prop('disabled', true);
                });
            }
            
            $('#logForm').submit(function(e) {
                e.preventDefault();
                currentNamespace = $('#namespace').val();
                currentPod = $('#pod').val();
                currentTailLines = $('#tail_lines').val();
                if (!currentNamespace || !currentPod) return;
                fetchLogs();
            });
            
            $('#refreshBtn').click(function() {
                if (currentNamespace && currentPod) {
                    fetchLogs();
                }
            });
            
            $('#namespace').trigger('change');
        });
    </script>
</body>
</html>''')

    # error.html
    with open('templates/error.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container py-5">
        <div class="alert alert-danger">
            <h4 class="alert-heading">Error</h4>
            <p>{{ error }}</p>
        </div>
    </div>
</body>
</html>''')

if __name__ == '__main__':
    create_templates()
    app.run(host='0.0.0.0', port=5000)
