from paddleocr import PaddleOCR
import cv2
import numpy as np
import threading
import gc
import time
import os

_ocr_instance = None
_ocr_lock = threading.RLock()
_ocr_busy = False
_last_reset_time = 0
_reset_cooldown = 5

def get_ocr_instance():
    global _ocr_instance, _ocr_busy
    with _ocr_lock:
        if _ocr_instance is None and not _ocr_busy:
            try:
                _ocr_busy = True
                os.environ['OMP_NUM_THREADS'] = '1'
                os.environ['MKL_NUM_THREADS'] = '1'
                
                _ocr_instance = PaddleOCR(
                    use_angle_cls=True, 
                    lang="en", 
                    show_log=False,
                    use_gpu=False,
                    cpu_threads=1
                )
                print("Nova instância do OCR criada")
            except Exception as e:
                print(f"Erro ao inicializar OCR: {str(e)}")
                _ocr_instance = None
            finally:
                _ocr_busy = False
        return _ocr_instance

def reset_ocr_instance():
    global _ocr_instance, _last_reset_time, _ocr_busy
    current_time = time.time()
    
    with _ocr_lock:
        if current_time - _last_reset_time < _reset_cooldown:
            print(f"Reset em cooldown. Aguarde {_reset_cooldown - (current_time - _last_reset_time):.1f}s")
            return False
            
        if _ocr_instance is not None:
            try:
                print("Resetando instância do OCR...")
                del _ocr_instance
                gc.collect()
                time.sleep(1)
            except Exception as e:
                print(f"Erro ao resetar OCR: {str(e)}")
            finally:
                _ocr_instance = None
                _ocr_busy = False
                _last_reset_time = current_time
        return True

def reconhecer_texto(imagem, retry_count=0, max_retries=2):
    
    if retry_count > max_retries:
        return "Erro: Muitas tentativas de OCR falharam"
    
    if not _ocr_lock.acquire(timeout=30):
        return "Erro: Timeout ao aguardar OCR disponível"
    
    try:
        if imagem is None or imagem.size == 0:
            return "Imagem inválida para OCR"
        
        if len(imagem.shape) == 2:
            altura, largura = imagem.shape
        else:
            altura, largura, _ = imagem.shape
            
        if altura < 10 or largura < 10:
            return "Imagem muito pequena para OCR"
        
        if not np.any(imagem):
            return "Imagem vazia ou corrompida"
        
        if altura > 800 or largura > 800:
            fator = min(800/altura, 800/largura)
            nova_largura = int(largura * fator)
            nova_altura = int(altura * fator)
            imagem = cv2.resize(imagem, (nova_largura, nova_altura))
        
        if len(imagem.shape) == 2:
            imagem = cv2.cvtColor(imagem, cv2.COLOR_GRAY2RGB)
        elif len(imagem.shape) == 3 and imagem.shape[2] == 3:
            imagem = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
        
        if imagem.dtype != np.uint8:
            imagem = np.clip(imagem, 0, 255).astype(np.uint8)
        
        ocr = get_ocr_instance()
        if ocr is None:
            return "Erro ao inicializar OCR"
        
        try:
            resultado_ocr = ocr.ocr(imagem, cls=True)
        except Exception as ocr_error:
            raise ocr_error
        
        if not resultado_ocr or not resultado_ocr[0]:
            return "Nenhum texto encontrado"

        texto_extraido = []

        for bloco in resultado_ocr:
            if bloco:
                for linha in bloco:
                    if linha and len(linha) > 1 and linha[1]:
                        texto_extraido.append(linha[1][0])

        return "\n".join(texto_extraido) if texto_extraido else "Nenhum texto encontrado"
        
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Erro no OCR (tentativa {retry_count + 1}): {str(e)}")
        
        reset_keywords = [
            "could not execute a primitive",
            "could not create a primitive",
            "segmentation fault",
            "corrupted",
            "preconditionnotmeterror",
            "tensor holds no memory"
        ]
        
        should_reset = any(keyword in error_msg for keyword in reset_keywords)
        
        if should_reset and retry_count < max_retries:
            print("Erro crítico detectado, tentando resetar OCR...")
            if reset_ocr_instance():
                time.sleep(2)
                return reconhecer_texto(imagem, retry_count + 1, max_retries)
        
        return f"Erro no OCR: {str(e)}"
        
    finally:
        _ocr_lock.release()