let isUploading = false;
let uploadTimeout = null;
let countdownInterval = null;

function showCountdown(timeRemaining) {
    const noResultsDiv = document.getElementById('noResults');
    const uploadButton = document.querySelector('button[onclick="uploadImage()"]') || 
                        document.querySelector('button[onclick="debounceUpload()"]');
    
    function updateCountdown() {
        if (timeRemaining <= 0) {
            clearInterval(countdownInterval);
            countdownInterval = null;
            
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.textContent = 'Enviar Imagem';
                uploadButton.style.backgroundColor = '';
                uploadButton.style.cursor = '';
            }
            
            noResultsDiv.innerHTML = 'Você pode tentar novamente agora.';
            noResultsDiv.style.color = '#28a745';
            
            setTimeout(() => {
                noResultsDiv.style.display = 'none';
            }, 3000);
            
            return;
        }
        
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        const timeString = minutes > 0 ? 
            `${minutes}:${seconds.toString().padStart(2, '0')}` : 
            `${seconds}s`;
            
        noResultsDiv.innerHTML = `
            <div style="text-align: center;">
                <div style="font-size: 18px; margin-bottom: 10px;">
                    ⏱️ Limite de requisições atingido
                </div>
                <div style="font-size: 24px; font-weight: bold; color: #dc3545; margin-bottom: 10px;">
                    ${timeString}
                </div>
                <div style="font-size: 14px; color: #666;">
                    Aguarde para fazer uma nova tentativa
                </div>
                <div style="width: 100%; background-color: #e9ecef; border-radius: 10px; margin-top: 15px; overflow: hidden;">
                    <div style="height: 8px; background-color: #dc3545; width: ${((60 - timeRemaining) / 60) * 100}%; transition: width 1s ease;"></div>
                </div>
            </div>
        `;
        
        if (uploadButton) {
            uploadButton.textContent = `Aguarde ${timeString}`;
            uploadButton.style.backgroundColor = '#dc3545';
            uploadButton.style.cursor = 'not-allowed';
        }
        
        timeRemaining--;
    }
    
    updateCountdown();
    countdownInterval = setInterval(updateCountdown, 1000);
}

function uploadImage() {
    if (isUploading) {
        console.log('Upload já em andamento, ignorando...');
        return;
    }

    const input = document.getElementById('imageInput');
    const uploadButton = document.querySelector('button[onclick="uploadImage()"]') || 
                        document.querySelector('button[onclick="debounceUpload()"]');
    
    if (input.files.length === 0) {
        alert('Por favor, selecione uma imagem para enviar.');
        return;
    }

    isUploading = true;
    
    if (uploadButton) {
        uploadButton.disabled = true;
        uploadButton.textContent = 'Processando...';
        uploadButton.style.backgroundColor = '#007bff';
        uploadButton.style.cursor = 'wait';
    }

    document.getElementById('result').style.display = 'none';
    document.getElementById('noResults').style.display = 'none';
    
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }

    const formData = new FormData();
    formData.append('file', input.files[0]);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    fetch('/upload', {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(async response => {
        clearTimeout(timeoutId);
        
        let responseData = null;
        try {
            responseData = await response.json();
        } catch (jsonError) {
            console.error('Erro ao parsear JSON da resposta:', jsonError);
        }
        
        if (response.status === 429) {
            throw new Error(JSON.stringify({
                status: 429,
                data: responseData
            }));
        }
        
        if (!response.ok) {
            const errorMessage = responseData && responseData.erro 
                ? responseData.erro 
                : `HTTP error! status: ${response.status}`;
            
            throw new Error(JSON.stringify({
                status: response.status,
                message: errorMessage,
                data: responseData
            }));
        }
        
        return responseData;
    })
    .then(data => {
        if (data.erro) {
            document.getElementById('result').style.display = 'none';
            document.getElementById('noResults').style.display = 'block';
            document.getElementById('noResults').innerText = 'Erro: ' + data.erro;
            document.getElementById('noResults').style.color = '#dc3545';
        } else {
            document.getElementById('noResults').style.display = 'none';

            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            
            const existingImage = resultDiv.querySelector('img');
            if (existingImage) {
                existingImage.remove();
            }
            
            const resultImage = document.createElement('img');
            resultImage.src = data.detected_plates;
            resultImage.alt = 'Placa detectada';
            resultImage.style.maxWidth = '100%';
            resultImage.style.height = 'auto';
            resultImage.style.border = '2px solid #28a745';
            resultImage.style.borderRadius = '8px';
            resultImage.style.marginBottom = '15px';
            resultDiv.insertBefore(resultImage, document.getElementById('extractedTextTitle'));

            const extractedText = document.getElementById('extractedText');
            extractedText.innerText = data.extracted_text || 'Nenhum texto extraído.';
        }
    })
    .catch(error => {
        clearTimeout(timeoutId);
        console.error('Erro no upload:', error);
        
        document.getElementById('result').style.display = 'none';
        document.getElementById('noResults').style.display = 'block';
        
        let errorMessage = 'Erro ao enviar a imagem: ';
        
        try {
            const errorData = JSON.parse(error.message);
            
            if (errorData.status === 429 && errorData.data && errorData.data.rate_limit && errorData.data.time_remaining) {
                showCountdown(errorData.data.time_remaining);
                return;
            }
            
            if (errorData.message) {
                errorMessage += errorData.message;
            } else if (errorData.data && errorData.data.erro) {
                errorMessage += errorData.data.erro;
            } else {
                errorMessage += `HTTP ${errorData.status}`;
            }
            
        } catch (parseError) {
            if (error.name === 'AbortError') {
                errorMessage += 'Timeout - operação demorou muito para completar';
            } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                errorMessage += 'Erro de rede ou servidor indisponível';
            } else if (error.message.includes('429')) {
                errorMessage += 'Muitas requisições. Aguarde um momento antes de tentar novamente.';
            } else {
                let originalMessage = error.message;
                
                if (originalMessage.includes('HTTP error! status:')) {
                    const statusMatch = originalMessage.match(/status:\s*(\d+)/);
                    if (statusMatch) {
                        const status = statusMatch[1];
                        switch (status) {
                            case '400':
                                errorMessage += 'Requisição inválida - verifique o arquivo enviado';
                                break;
                            case '413':
                                errorMessage += 'Arquivo muito grande';
                                break;
                            case '415':
                                errorMessage += 'Tipo de arquivo não suportado';
                                break;
                            case '500':
                                errorMessage += 'Erro interno do servidor';
                                break;
                            default:
                                errorMessage += `Erro HTTP ${status}`;
                        }
                    } else {
                        errorMessage += originalMessage;
                    }
                } else {
                    errorMessage += originalMessage;
                }
            }
        }
        
        document.getElementById('noResults').innerText = errorMessage;
        document.getElementById('noResults').style.color = '#dc3545';
    })
    .finally(() => {
        isUploading = false;
        if (!countdownInterval && uploadButton) {
            uploadButton.disabled = false;
            uploadButton.textContent = 'Enviar Imagem';
            uploadButton.style.backgroundColor = '';
            uploadButton.style.cursor = '';
        }
    });
}

function debounceUpload() {
    if (uploadTimeout) {
        clearTimeout(uploadTimeout);
    }
    
    uploadTimeout = setTimeout(() => {
        uploadImage();
    }, 300);
}

document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('imageInput');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !isUploading) {
                e.preventDefault();
                debounceUpload();
            }
        });
    }
});
