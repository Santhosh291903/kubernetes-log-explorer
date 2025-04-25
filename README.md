# Kubernetes Log Viewer

A simple Flask-based web application to view and fetch logs from Kubernetes pods. This tool integrates with the Kubernetes API and allows you to dynamically select namespaces, pods, and log outputs through a user-friendly interface.

## Features

- **View logs from any pod**: Fetch logs from selected Kubernetes pods.
- **Namespace and pod selection**: Select namespaces and pods dynamically from the UI.
- **Adjustable log output**: Choose the number of log lines to fetch (20, 50, 100, 200, 500, 1000).
- **Error handling**: Handles errors gracefully and shows appropriate messages.
- **Real-time log fetching**: Displays logs dynamically and updates the log output area as new logs are fetched.

## Prerequisites

Before using this tool, ensure the following:

- You have access to a Kubernetes cluster.
- The `kubeconfig` file is correctly set up on your system to authenticate with the cluster.
- Python 3.6+ and the necessary Python packages installed.

## Installation

### 1. Clone the repository


git clone https://github.com/yourusername/k8s-log-viewer.git

cd k8s-log-viewer

2. Install dependencies
Create a virtual environment and install the necessary dependencies:


python3 -m venv venv

source venv/bin/activate  # On Windows, use venv\Scripts\activate
pip install -r requirements.txt

3. Configure Kubernetes
Ensure your kubeconfig file is set up correctly. The tool will use the kubeconfig file to interact with your Kubernetes cluster.

The default path is /home/icanio-10155/.kube/config. You can change this in the init_kubernetes() function in the app.py file if needed.

4. Run the application
To start the Flask app, run:

python app.py
This will start the application at http://localhost:5000. You can access it in your web browser.

Usage
Once the app is running, you will be presented with a web interface where you can:

Select a namespace from the dropdown.

Once a namespace is selected, pods will be loaded dynamically in the next dropdown.

Select the log lines to display from a list of options (20, 50, 100, etc.).

Click on Get Logs to fetch logs for the selected pod, and the log output will be displayed in the main section of the page.



