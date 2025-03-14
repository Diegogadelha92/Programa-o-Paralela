import os
import threading
import cv2
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from app.services.processamento import processamento_parte_imagem, dividir_imagem
from flask import current_app as app

bp = Blueprint('image_routes', __name__)

@bp.route('/upload', methods=['POST'])
def upload_imagem():
    if 'file' not in request.files:
        return  jsonify({'erro': 'nenhum arquivo encontrado'}), 400

    arquivo = request.files['file']
    if arquivo.filename == '':
        return jsonify({'erro' : 'nome do arquivo invalido.'}), 400

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

    return jsonify({'resultados' : resultados})