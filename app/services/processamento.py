import cv2

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