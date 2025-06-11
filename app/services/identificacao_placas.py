import cv2
import numpy as np

def reconhecer_placa(imagem_np, caminho_arquivo):
    try:
        net = cv2.dnn.readNet("app/models/yolo/custom-yolov4-detector.cfg", "app/models/yolo/custom-yolov4-detector_final.weights")
        nomes_camadas = net.getLayerNames()
        camadas_saida = [nomes_camadas[i - 1] for i in net.getUnconnectedOutLayers()]

        img = cv2.imdecode(imagem_np, cv2.IMREAD_COLOR)

        if img is None:
            return None, "Arquivo não é uma imagem válida."
        
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

        if not boxes:
            return None, "Nenhuma placa detectada."

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        if len(indexes) == 0:
            return None, "Nenhuma placa detectada após filtragem."

        i = indexes[0]
        x, y, w, h = boxes[i]
        
        x = max(0, x)
        y = max(0, y)
        w = min(w, largura - x)
        h = min(h, altura - y)
        
        placa_recortada = img[y:y+h, x:x+w]

        if placa_recortada.size == 0:
            return None, "A placa detectada está vazia."
        
        cv2.imwrite(caminho_arquivo, placa_recortada)
        
        return placa_recortada, None
        
    except Exception as e:
        return None, f"Erro ao processar detecção: {str(e)}"
