import os
import cv2
import threading
import numpy as np

def carregar_e_validar_imagem(caminho_arquivo):
    imagem = cv2.imread(caminho_arquivo)
    if imagem is None:
        os.remove(caminho_arquivo)
        return None
    return imagem

def dividir_imagem(imagem, numero_de_partes):
    altura, largura, _ = imagem.shape
    altura_parte = altura // numero_de_partes
    partes = []
    
    for i in range(numero_de_partes):
        inicio_y = i * altura_parte
        fim_y = altura if i == numero_de_partes - 1 else (i + 1) * altura_parte
        partes.append(imagem[inicio_y:fim_y, :])
    
    return partes

def processamento_parte_imagem(parte_imagem, resultados, indice):
    try:
        escala_cinza = cv2.cvtColor(parte_imagem, cv2.COLOR_BGR2GRAY)
        escala_cinza = cv2.resize(escala_cinza, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        imagem_borrada = cv2.bilateralFilter(escala_cinza, 11, 17, 17)
        imagem_limiarizada = cv2.adaptiveThreshold(imagem_borrada, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        kernel = np.ones((3,3), np.uint8)
        imagem_dilatada = cv2.dilate(imagem_limiarizada, kernel, iterations=1)

        resultados[indice] = (parte_imagem, escala_cinza, imagem_limiarizada, imagem_dilatada)
    except Exception as e:
        resultados[indice] = None

def processar_imagem(caminho_arquivo, num_partes=3):
    imagem = carregar_e_validar_imagem(caminho_arquivo)
    if imagem is None:
        return None

    partes_imagem = dividir_imagem(imagem, num_partes)
    threads = []
    resultados = [None] * num_partes

    for i, parte in enumerate(partes_imagem):
        thread = threading.Thread(target=processamento_parte_imagem, args=(parte, resultados, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if any(r is None for r in resultados):
        return None

    return resultados
