import threading
import os
import cv2
import numpy as np
from flask import Flask, request, jsonfy
from werkzeug.utils import secure_filename

app = Flask(__name__)
from routes import *
PASTA_UPLOAD = 'uploads'
os.makedirs(PASTA_UPLOAD, exist_ok=True)
app.config['UPLOAD_FOLDER'] = PASTA_UPLOAD

caminho_cascade = cv2.data.haarcascades+ 'haarcascade_frontalface_default.xml'
detector_objetos = cv2.CascadeClassifier(caminho_cascade)

def processamento_parte_imagem(parte_imagem, resultados, indice):
    escala_cinza = cv2.cvtColor(parte_imagem, cv2.COLOR_BGR2GRAY)
    objetos = detector_objetos.detectMultiScale(escala_cinza, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
    resultados[indice] = len(objetos)

def dividir_imagem(imagem, numero_de_partes):
    altura, largura, _ = imagem.shape
    altura_parte = altura // numero_de_partes
    partes = []

    for i in range(numero_de_partes):
        inicio_y = i *altura_parte
        if i == numero_de_partes -1:
            fim_y = altura
        else:
            fim_y = (i +1) * altura_parte
            partes.append(imagem[inicio_y:fim_y, :])

            return partes

@app.route('/upload', methods=['POST'])
def upload_imagem():
    if 'file' not in request.files:
        return  jsonfy({'erro': 'nenhum arquivo encontrado'}), 400

    arquivo = request.files['file']
    if arquivo.filename == '':
        return jsonfy({'erro' : 'nome do arquivo invalido.'}), 400

    nome_arquivo = secure_filename(arquivo.filename)
    caminho_arquivo = os.path.join(app.config['PASTA_UPLOAD'], nome_arquivo)
    arquivo.save(caminho_arquivo)

    imagem = cv2.imread(caminho_arquivo)
    num_partes = 3
    partes_imagem = dividir_imagem(imagem, num_partes)

    threads = []
    resultados = [0] * num_partes

    for i, parte in enumerate(partes_imagem):
        thread = threading.Thread(target=processamento_parte_imagem, args=(parte, resultados, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return jsonfy({'resultados' : resultados})

if __name__ == "__main__":
    app.run(debug=True)
