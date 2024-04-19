function confirmCode() {
    var code = document.getElementById('code-input').value;
    if (code.length === 4) {
        window.location.href = `/download/${code}`;
    } else {
        alert('Please enter a valid 4-digit code.');
    }
}
