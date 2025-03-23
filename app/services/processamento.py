import os
import cv2
import threading

caminho_cascade = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
detector_objetos = cv2.CascadeClassifier(caminho_cascade)

def carregar_e_validar_imagem(caminho_arquivo):
    imagem = cv2.imread(caminho_arquivo)
    if imagem is None:
        os.remove(caminho_arquivo)  # Remove arquivo inválido
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
    escala_cinza = cv2.cvtColor(parte_imagem, cv2.COLOR_BGR2GRAY)
    objetos = detector_objetos.detectMultiScale(escala_cinza, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
    resultados[indice] = len(objetos)

def processar_imagem(caminho_arquivo, num_partes=3):
    imagem = carregar_e_validar_imagem(caminho_arquivo)
    if imagem is None:
        return None

    partes_imagem = dividir_imagem(imagem, num_partes)
    threads = []
    resultados = [0] * num_partes

    for i, parte in enumerate(partes_imagem):
        thread = threading.Thread(target=processamento_parte_imagem, args=(parte, resultados, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return resultados
