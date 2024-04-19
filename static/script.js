let socket;

window.onload = function() {
    socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    socket.on('file_shared', function(data) {
        console.log('File shared event received:', data);
        document.getElementById('upload-area').style.display = 'none';
        document.getElementById('file-info').style.display = 'block';
        document.getElementById('file-name').textContent = data.filename;
        document.getElementById('file-size').textContent = formatBytes(data.size);
        document.getElementById('qr-code').src = data.qr;
        document.getElementById('sharing-code').textContent = data.pin;
    });
};

function handleFileUpload(files) {
    const formData = new FormData();
    Array.from(files).forEach(file => {
        formData.append('file', file); // Note the change here to 'files[]' to signify multiple files
    });

    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        console.log('Upload successful:', data);
        // Assuming now you have a single response for the ZIP of all uploaded files
        displayFileData(data); // Directly call displayFileData with the single response
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function displayFileData(fileData) {
    document.getElementById('upload-area').style.display = 'none';
    const fileInfoDiv = document.getElementById('file-info');
    fileInfoDiv.style.display = 'block';
    
    // Assuming 'fileData' contains 'filename', 'qr', and 'pin' for the ZIP file
    document.getElementById('file-name').textContent = fileData.filename;
    // The 'file-size' display logic might need adjustments since we're now dealing with a ZIP file
    document.getElementById('qr-code').src = fileData.qr;
    document.getElementById('sharing-code').textContent = `PIN: ${fileData.pin}`;
}

// Helper function to format bytes into human-readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
