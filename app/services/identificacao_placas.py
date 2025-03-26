import cv2
import numpy as np

def reconhecer_placa(imagem_np, caminho_arquivo):
    net = cv2.dnn.readNet("app/models/yolo/custom-yolov4-detector.cfg", "app/models/yolo/custom-yolov4-detector_final.weights")
    nomes_camadas = net.getLayerNames()
    camadas_saida = [nomes_camadas[i - 1] for i in net.getUnconnectedOutLayers()]

    img = cv2.imdecode(imagem_np, cv2.IMREAD_COLOR)

    if img is None:
        return "Erro: Arquivo não é uma imagem válida.", 400
    altura, largura, _ = img.shape

    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    saidas = net.forward(camadas_saida)

    boxes = []
    confidences = []
    ids_classes = []

    for saida in saidas:
        for deteccao in saida:
            scores = deteccao[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(deteccao[0] * largura)
                center_y = int(deteccao[1] * altura)
                w = int(deteccao[2] * largura)
                h = int(deteccao[3] * altura)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                ids_classes.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    placas_detectadas = []
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            placas_detectadas.append((x, y, w, h))

    if not boxes or len(placas_detectadas) == 0:
        return "Erro: Nenhuma placa detectada.", 404

    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            placas_detectadas.append((x, y, w, h))
            placa_recortada = img[y:y+h, x:x+w]

            if placa_recortada.size == 0:
                return "Erro: A placa detectada parece estar vazia.", 400
            
            cv2.imwrite(caminho_arquivo, placa_recortada)

    return placa_recortada, None
