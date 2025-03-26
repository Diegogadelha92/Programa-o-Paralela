function uploadImage() {
    const input = document.getElementById('imageInput');
    const formData = new FormData();

    if (input.files.length === 0) {
        alert('Por favor, selecione uma imagem para enviar.');
        return;
    }

    formData.append('file', input.files[0]);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.erro) {
            document.getElementById('result').innerText = 'Erro: ' + data.erro;
        } else {
            document.getElementById('result').innerText = 
                'Placa Detectada: \n' + JSON.stringify(data.placa_detectada) + '\n' +
                'Texto Extraído: \n' + data.texto_extraido;
        }
    })
    .catch(error => {
        document.getElementById('result').innerText = 'Erro ao enviar a imagem: ' + error;
    });
}
