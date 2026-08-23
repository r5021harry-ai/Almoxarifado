"""
Geração de QR Codes dos produtos.
O QR Code guarda apenas o CÓDIGO do produto (ex: "PROD:FIL001").
O estoque é sempre consultado no banco no momento da leitura.
"""
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QRCODES_DIR = os.path.join(BASE_DIR, "qrcodes")

QR_PREFIX = "PROD:"


def gerar_qrcode_produto(codigo: str) -> str:
    """Gera (ou regenera) o QR Code de um produto e devolve o caminho do arquivo PNG."""
    os.makedirs(QRCODES_DIR, exist_ok=True)
    payload = f"{QR_PREFIX}{codigo}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    path = os.path.join(QRCODES_DIR, f"{codigo}.png")
    img.save(path)
    return path


def extrair_codigo(qr_texto: str):
    """Extrai o código do produto a partir do conteúdo lido do QR Code."""
    if qr_texto is None:
        return None
    qr_texto = qr_texto.strip()
    if qr_texto.startswith(QR_PREFIX):
        return qr_texto[len(QR_PREFIX):]
    # aceita também QR codes "crus" contendo somente o código
    return qr_texto


def gerar_etiqueta(codigo: str, nome: str, numero_peca: str = "", localizacao: str = "") -> str:
    """Gera uma etiqueta (QR + textos) pronta para impressão, sem quantidade."""
    qr_path = gerar_qrcode_produto(codigo)
    qr_img = Image.open(qr_path)

    largura, altura_qr = 400, 400
    qr_img = qr_img.resize((largura, altura_qr))

    linhas_texto = [nome[:40]]
    linhas_texto.append(f"Cod: {codigo}")
    if numero_peca:
        linhas_texto.append(f"Peça: {numero_peca}")
    if localizacao:
        linhas_texto.append(f"Local: {localizacao}")

    altura_texto = 30 * len(linhas_texto) + 20
    etiqueta = Image.new("RGB", (largura, altura_qr + altura_texto), "white")
    etiqueta.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(etiqueta)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    y = altura_qr + 10
    for linha in linhas_texto:
        draw.text((10, y), linha, fill="black", font=font)
        y += 28

    etiqueta_path = os.path.join(QRCODES_DIR, f"etiqueta_{codigo}.png")
    etiqueta.save(etiqueta_path)
    return etiqueta_path
