import os
import subprocess
import logging
import socket
import webbrowser
from flask import Flask, jsonify, render_template, request, send_from_directory

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, static_folder='static')

# Configuration with better defaults
DEFAULT_IMAGE_DIR = os.path.expanduser('~/Pictures')
DEFAULT_TARGET_DIR = os.path.expanduser('~/Desktop')

def FindAvailablePort(StartPort=5000, MaxAttempts=20):
    """Find an available port starting from StartPort"""
    for Port in range(StartPort, StartPort + MaxAttempts):
        try:
            TestSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            TestSocket.bind(('127.0.0.1', Port))
            TestSocket.close()
            return Port
        except OSError:
            continue
    raise RuntimeError("No available ports found")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/browse')
def browse():
    browse_type = request.args.get('type', 'image')
    if browse_type == 'image':
        initial_path = DEFAULT_IMAGE_DIR
    else:
        initial_path = DEFAULT_TARGET_DIR

    path = request.args.get('path', initial_path)
    if not os.path.isdir(path):
        return jsonify(error=f"Directory not found: {path}"), 404

    dirs = []
    files = []
    for item in sorted(os.listdir(path)):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            dirs.append(item)
        else:
            files.append(item)

    return jsonify(path=path, dirs=dirs, files=files)

@app.route('/api/images')
def get_images():
    image_dir = request.args.get('dir', DEFAULT_IMAGE_DIR)

    if not os.path.isdir(image_dir):
        return jsonify(error=f"Directory not found: {image_dir}"), 404

    images = []
    for f in sorted(os.listdir(image_dir)):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
            images.append(f)

    return jsonify({
        'images': images,
        'image_dir': image_dir
    })

@app.route('/images/<path:filename>')
def serve_image(filename):
    image_dir = request.args.get('dir', DEFAULT_IMAGE_DIR)
    return send_from_directory(image_dir, filename)

@app.route('/api/set-folder-icon', methods=['POST'])
def set_folder_icon():
    data = request.get_json()
    folder_path = data.get('folder_path')
    icon_path = data.get('icon_path')

    if not folder_path or not icon_path:
        return jsonify(success=False, message='Missing folder_path or icon_path'), 400

    if not os.path.isdir(folder_path):
        return jsonify(success=False, message=f"Folder not found: {folder_path}"), 404

    if not os.path.isfile(icon_path):
        return jsonify(success=False, message=f"Icon not found: {icon_path}"), 404

    try:
        subprocess.run(['gio', 'set', folder_path, 'metadata::custom-icon', f'file://{icon_path}'], check=True)
        return jsonify(success=True, message=f'Successfully set icon for {os.path.basename(folder_path)}')
    except subprocess.CalledProcessError as e:
        return jsonify(success=False, message=f'Failed to set icon: {e}'), 500
    except FileNotFoundError:
        return jsonify(success=False, message='The "gio" command is not installed. Please install it to set folder icons.'), 500

@app.route('/api/get-folder-icon', methods=['POST'])
def get_folder_icon():
    data = request.get_json()
    folder_path = data.get('folder_path')

    if not folder_path:
        return jsonify(success=False, message='Missing folder_path'), 400

    if not os.path.isdir(folder_path):
        return jsonify(success=False, message=f"Folder not found: {folder_path}"), 404

    try:
        # Get the custom icon metadata from the folder
        result = subprocess.run(['gio', 'get', folder_path, 'metadata::custom-icon'],
                              capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            icon_path = result.stdout.strip()
            # gio returns file:// URIs, convert to direct path if possible
            if icon_path.startswith('file://'):
                icon_path = icon_path[7:]  # Remove 'file://' prefix
            return jsonify(success=True, icon_path=icon_path)
        else:
            return jsonify(success=False, message='No custom icon found')

    except subprocess.CalledProcessError:
        return jsonify(success=False, message='No custom icon found')
    except FileNotFoundError:
        return jsonify(success=False, message='The "gio" command is not installed')

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    os._exit(0)

if __name__ == '__main__':
    import logging
    from waitress import serve

    # Find available port
    Port = FindAvailablePort()

    # Configure logging
    logging.basicConfig(level=logging.CRITICAL)

    print(f"Starting ImageBrowser on port {Port}")
    print(f"Access at: http://127.0.0.1:{Port}")

    # Open browser automatically
    webbrowser.open(f'http://127.0.0.1:{Port}')

    # Serve the application
    serve(app, host='127.0.0.1', port=Port, _quiet=True)