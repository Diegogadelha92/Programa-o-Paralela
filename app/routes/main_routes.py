import os
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from app.services.processamento import processar_imagem
from flask import current_app as app

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

    nome_arquivo = secure_filename(arquivo.filename)
    caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
    arquivo.save(caminho_arquivo)

    resultados = processar_imagem(caminho_arquivo)

    if resultados is None:
        return jsonify({'erro': 'Arquivo não é uma imagem válida'}), 400

    return jsonify({'resultados': resultados})
