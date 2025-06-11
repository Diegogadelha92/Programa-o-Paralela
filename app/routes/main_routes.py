import os
import mimetypes
import time
from collections import defaultdict
from functools import wraps

from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from flask import current_app as app
from app.services.pre_processamento import processar_imagem
from app.services.identificacao_placas import reconhecer_placa
from app.services.reconhecimento_ocr import reconhecer_texto
import numpy as np
import cv2
import base64

bp = Blueprint('main_routes', __name__, url_prefix="")

request_counts = defaultdict(list)
RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW = 60

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        current_time = time.time()

        request_counts[client_ip] = [
            req_time for req_time in request_counts[client_ip] 
            if current_time - req_time < RATE_LIMIT_WINDOW
        ]

        if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
            oldest_request = min(request_counts[client_ip])
            time_remaining = int(RATE_LIMIT_WINDOW - (current_time - oldest_request))
            
            return jsonify({
                'erro': f'Muitas requisições. Limite: {RATE_LIMIT_REQUESTS} por {RATE_LIMIT_WINDOW} segundos.',
                'rate_limit': True,
                'time_remaining': max(time_remaining, 1),
                'retry_after': time_remaining
            }), 429

        request_counts[client_ip].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_MIMETYPES = {
    'image/png', 'image/jpeg', 'image/jpg', 'image/webp'
}

def allowed_file(filename, file_content=None):
    if not filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if extension not in ALLOWED_EXTENSIONS:
        return False

    if file_content:
        try:
            mimetype = mimetypes.guess_type(filename)[0]
            if mimetype and mimetype not in ALLOWED_MIMETYPES:
                return False
        except:
            pass
    
    return True

@bp.route("/", methods=['GET'])
def homepage():
    return render_template("homepage.html")

@bp.route('/upload', methods=['POST'])
@rate_limit
def upload_imagem():
    try:
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo encontrado'}), 400

        arquivo = request.files['file']
        if arquivo.filename == '':
            return jsonify({'erro': 'Nome do arquivo inválido'}), 400

        if not allowed_file(arquivo.filename):
            return jsonify({'erro': 'Tipo de arquivo não suportado. Use PNG, JPG, JPEG ou WEBP.'}), 400

        try:
            imagem_bytes = arquivo.read()

            if len(imagem_bytes) == 0:
                return jsonify({'erro': 'Arquivo está vazio'}), 400

            if len(imagem_bytes) > 10 * 1024 * 1024:
                return jsonify({'erro': 'Arquivo muito grande. Limite de 10MB.'}), 400
            
            imagem_np = np.frombuffer(imagem_bytes, dtype=np.uint8)

            test_img = cv2.imdecode(imagem_np, cv2.IMREAD_COLOR)
            if test_img is None:
                return jsonify({'erro': 'Arquivo não é uma imagem válida ou está corrompido'}), 400
            
        except Exception as e:
            return jsonify({'erro': f'Erro ao processar imagem: {str(e)}'}), 400

        nome_arquivo = secure_filename(arquivo.filename)
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)

        placa_detectada, error = reconhecer_placa(imagem_np, caminho_arquivo)
        if error:
            return jsonify({'erro': error}), 400

        if placa_detectada is None:
            return jsonify({'erro': 'Nenhuma placa foi detectada'}), 400

        processamento_placa = processar_imagem(placa_detectada)
        if processamento_placa is None:
            return jsonify({'erro': 'Erro no pré-processamento da placa'}), 400

        try:
            _, buffer = cv2.imencode('.png', processamento_placa)
            if len(buffer) == 0:
                return jsonify({'erro': 'Erro ao codificar imagem processada'}), 500
            imagem_base64 = base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            return jsonify({'erro': f'Erro ao codificar imagem: {str(e)}'}), 500

        texto_extraido = reconhecer_texto(processamento_placa)

        return jsonify({
            'detected_plates': f"data:image/png;base64,{imagem_base64}",
            'extracted_text': texto_extraido
        }), 200

    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500
