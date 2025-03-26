from paddleocr import PaddleOCR

# Inicializa o OCR com suporte a ângulos e idioma inglês
ocr = PaddleOCR(use_angle_cls=True, lang="en")

def reconhecer_texto(imagem):
    resultado_ocr = ocr.ocr(imagem, cls=True)
    
    if not resultado_ocr:
        return "Nenhum texto encontrado"

    texto_extraido = []

    for bloco in resultado_ocr:
        for linha in bloco:
            texto_extraido.append(linha[1][0])

    return "\n".join(texto_extraido) 