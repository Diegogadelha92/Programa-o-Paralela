function uploadImage() {
    const input = document.getElementById('imageInput');
    const file = input.files[0];

    if (!file) {
        alert("Por favor, selecione uma imagem");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    fetch('http://127.0.0.1:5000/upload', {
        method: 'POST',
        body: formData,
    }).then(reponse => response.json()).then(data => {
        document.getElemetById('result').textContext = JSON.stringify(data, null, 2);
    }).catch(error => {
        alert.error('Eroo ao enviar mensagem', error)
        document.getElementById('result').textContent = 'Erro ao enviar imagem';
    });
}