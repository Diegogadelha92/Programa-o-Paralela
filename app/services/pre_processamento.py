import cv2
import threading
import numpy as np

def dividir_imagem(imagem, numero_de_partes):
    try:
        if len(imagem.shape) == 3:
            altura, largura, _ = imagem.shape
        else:
            altura, largura = imagem.shape
            
        if altura < numero_de_partes:
            numero_de_partes = max(1, altura // 2)
            
        altura_parte = altura // numero_de_partes
        partes = []
        
        for i in range(numero_de_partes):
            inicio_y = i * altura_parte
            fim_y = altura if i == numero_de_partes - 1 else (i + 1) * altura_parte
            
            if len(imagem.shape) == 3:
                parte = imagem[inicio_y:fim_y, :]
            else:
                parte = imagem[inicio_y:fim_y, :]
                
            if parte.size > 0:
                partes.append(parte)
        
        return partes if partes else [imagem]
    except Exception as e:
        print(f"Erro ao dividir imagem: {str(e)}")
        return [imagem]

def processamento_parte_imagem(parte_imagem, resultados, indice):
    try:
        if parte_imagem is None or parte_imagem.size == 0:
            resultados[indice] = None
            return
            
        if len(parte_imagem.shape) == 3:
            escala_cinza = cv2.cvtColor(parte_imagem, cv2.COLOR_BGR2GRAY)
        else:
            escala_cinza = parte_imagem.copy()
        
        if escala_cinza is None or escala_cinza.size == 0:
            resultados[indice] = None
            return
            
        altura, largura = escala_cinza.shape
        if altura > 0 and largura > 0:
            escala_cinza = cv2.resize(escala_cinza, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        else:
            resultados[indice] = None
            return
        
        try:
            imagem_borrada = cv2.bilateralFilter(escala_cinza, 11, 17, 17)
            if imagem_borrada is None:
                imagem_borrada = escala_cinza
        except:
            imagem_borrada = escala_cinza
            
        try:
            imagem_limiarizada = cv2.adaptiveThreshold(
                imagem_borrada, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            if imagem_limiarizada is None:
                imagem_limiarizada = imagem_borrada
        except:
            imagem_limiarizada = imagem_borrada
        
        try:
            kernel = np.ones((3,3), np.uint8)
            imagem_dilatada = cv2.dilate(imagem_limiarizada, kernel, iterations=1)
            if imagem_dilatada is None:
                imagem_dilatada = imagem_limiarizada
        except:
            imagem_dilatada = imagem_limiarizada

        resultados[indice] = imagem_dilatada
        
    except Exception as e:
        print(f"Erro no processamento da parte {indice}: {str(e)}")
        resultados[indice] = None

def processamento_simples(imagem):
    try:
        if imagem is None or imagem.size == 0:
            return None
            
        if len(imagem.shape) == 3:
            escala_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        else:
            escala_cinza = imagem.copy()
            
        if escala_cinza is None or escala_cinza.size == 0:
            return None
            
        escala_cinza = cv2.resize(escala_cinza, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        imagem_borrada = cv2.bilateralFilter(escala_cinza, 11, 17, 17)
        imagem_limiarizada = cv2.adaptiveThreshold(
            imagem_borrada, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2)
        kernel = np.ones((3,3), np.uint8)
        imagem_dilatada = cv2.dilate(imagem_limiarizada, kernel, iterations=1)

        return imagem_dilatada
    except Exception:
        return None

def processar_imagem(imagem_placa, num_partes=3):
    if imagem_placa is None:
        return None

    partes_imagem = dividir_imagem(imagem_placa, num_partes)
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

    imagem_final = np.vstack(resultados)
    return imagem_final
