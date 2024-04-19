from flask import Flask, render_template, request, send_from_directory, abort, jsonify, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
import os
import base64
import random
import io
import zipfile
import qrcode
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploaded_files'
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024 * 1024  # 3 gigabytes

socketio = SocketIO(app)

network_ip = 'http://192.168.1.143:5000'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

code_file_mapping = {}

# Key management for Fernet encryption
KEY_FILE = 'fernet_key.key'

def load_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as key_file:
            key = key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
    return key

key = load_or_create_key()
cipher_suite = Fernet(key)

def encrypt_data(data):
    return cipher_suite.encrypt(data)

def decrypt_data(data):
    return cipher_suite.decrypt(data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['GET', 'POST'])
def download_page():
    if request.method == 'POST':
        code = request.form.get('code')  # Retrieve 'code' from form data
        if code:
            return redirect(url_for('download_file', code=code))  # Redirect with 'code' parameter
        else:
            # Handle case where code is not provided
            return abort(400)
    else:
        return render_template('download.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    if not files:
        return 'No files to upload', 400

    zip_filename = "files.zip"
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as myzip:
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                in_memory_file = io.BytesIO()
                file.save(in_memory_file)
                in_memory_file.seek(0)
                encrypted_content = encrypt_data(in_memory_file.read())
                myzip.writestr(filename, encrypted_content)
    
    code = generate_random_pin()
    code_file_mapping[code] = zip_filename
    full_url = f"{network_ip}/download/{code}"
    qr_code_img = generate_qr_code(full_url)

    return jsonify({'filename': zip_filename, 'qr': qr_code_img, 'pin': code})

@app.route('/download/<code>')
def download_file(code):
    filename = code_file_mapping.get(code)
    if filename and os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return render_template('download_page.html', filename=filename, code=code)
    else:
        abort(404)

@app.route('/download/file/<code>')
def download_file_direct(code):
    filename = code_file_mapping.get(code)
    if not filename:
        abort(404)
    
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(zip_path):
        decrypted_files = io.BytesIO()
        with zipfile.ZipFile(zip_path, 'r') as encrypted_zip:
            with zipfile.ZipFile(decrypted_files, 'w') as decrypted_zip:
                for encrypted_file in encrypted_zip.infolist():
                    encrypted_content = encrypted_zip.read(encrypted_file.filename)
                    decrypted_content = decrypt_data(encrypted_content)
                    decrypted_zip.writestr(encrypted_file.filename, decrypted_content)
        decrypted_files.seek(0)
        return send_file(decrypted_files, as_attachment=True, mimetype='application/zip', download_name=filename)
    else:
        abort(404)

def generate_random_pin():
    return '{:04d}'.format(random.randint(0, 9999))

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    qr_code_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{qr_code_data}"

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
