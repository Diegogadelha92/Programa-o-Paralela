import os

from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from flask import current_app as app
from app.services.pre_processamento import processar_imagem
from app.services.identificacao_placas import reconhecer_placa
import json
import numpy as np

bp = Blueprint('main_routes', __name__, url_prefix="")

@bp.route("/", methods=['GET'])
def homepage():
    return render_template("homepage.html")

@bp.route('/upload', methods=['POST'])
def upload_imagem():
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo encontrado'}), 400

    arquivo = request.files['file']
    if arquivo.filename == '':
        return jsonify({'erro': 'Nome do arquivo inválido'}), 400

    try:
        imagem_bytes = arquivo.read()
        imagem_np = np.frombuffer(imagem_bytes, dtype=np.uint8)
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar imagem: {str(e)}'}), 400

    nome_arquivo = secure_filename(arquivo.filename)
    caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)

    placa_detectada, error = reconhecer_placa(imagem_np, caminho_arquivo)
    if error:
        return jsonify({'erro': error}), 400

    processamento_placa = processar_imagem(placa_detectada)
    if processamento_placa is None:
        return jsonify({'erro': 'Arquivo não é uma imagem válida'}), 400

    try:
        json_resultado = json.dumps([tuple(item.tolist() for item in resultado) for resultado in processamento_placa])
    except Exception as e:
        return jsonify({'erro': f'Erro ao converter resultado para JSON: {str(e)}'}), 500

    return jsonify({'resultados': json_resultado, 'placas': [placa.tolist() for placa in placa_detectada]})
