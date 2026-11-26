"""Aba "Documentos": comprimir PDF, fotos -> PDF e PDF -> imagens.

Tudo no próprio computador (nada é enviado para sites de fora), com:
- pypdf (Python puro): abre o PDF e troca as imagens de dentro dele ao comprimir
- PDFium (pypdfium2, o motor de PDF do Chrome): monta PDFs e desenha as páginas
- FFmpeg (já vem junto): recomprime as imagens e salva JPG/PNG
"""
import os
import subprocess

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject

SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# ==========================================
# COMPRIMIR PDF
# ==========================================
# O que pesa num PDF quase sempre são as fotos e as páginas escaneadas. Cada
# imagem é recomprimida em JPG e, se for maior que o necessário para o nível,
# reduzida (DPI = pontos por polegada na página impressa). Texto, fontes e
# links ficam intactos. Nunca devolve um arquivo maior que o original.
NIVEIS_PDF = {
    # DPI máximo das imagens e qualidade do JPG no FFmpeg (-q:v: 2 = melhor, 31 = pior)
    "alta": {"dpi": 200, "qualidade": 3},
    "equilibrado": {"dpi": 150, "qualidade": 5},
    "forte": {"dpi": 100, "qualidade": 8},
}
NIVEL_PADRAO_PDF = "equilibrado"
ECONOMIA_MINIMA = 0.02  # abaixo disso, não vale a pena salvar outro arquivo
# Imagens que dá para recomprimir com segurança: cores comuns (RGB ou cinza), 8 bits.
# As outras (CMYK de gráfica, preto e branco de 1 bit de scanner/fax, máscaras) ficam como estão.
CANAIS = {"/DeviceRGB": 3, "/DeviceGray": 1}


class PdfProtegido(Exception):
    """O PDF pede senha para abrir."""


def _ffmpeg(*argumentos, entrada=None):
    resultado = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *argumentos], input=entrada,
                               capture_output=True, creationflags=SEM_JANELA)
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.decode("utf-8", "replace").strip()[-500:])
    return resultado.stdout


def _abrir(caminho):
    leitor = PdfReader(caminho)
    if leitor.is_encrypted:
        # PDF só com "senha do dono" (impede editar) abre com a senha vazia; com senha de abrir, não
        try:
            if not leitor.decrypt(""):
                raise PdfProtegido()
        except Exception:
            raise PdfProtegido()
    return leitor


def _canais(imagem):
    """3 (RGB) ou 1 (cinza) se dá para recomprimir esta imagem; None se não."""
    espaco = imagem.get("/ColorSpace")
    if espaco is None:
        return None
    espaco = espaco.get_object()
    if isinstance(espaco, list):  # [/ICCBased <perfil>]: vale o número de canais do perfil
        if espaco and espaco[0] == "/ICCBased":
            return {3: 3, 1: 1}.get(int(espaco[1].get_object().get("/N", 0)))
        return None
    return CANAIS.get(espaco)


def _filtros(imagem):
    filtro = imagem.get("/Filter")
    if filtro is None:
        return []
    filtro = filtro.get_object()
    return [str(f) for f in filtro] if isinstance(filtro, list) else [str(filtro)]


def _recomprimir(imagem, canais, lado_maximo, qualidade):
    """A imagem em JPG, menor se passar do lado máximo. Devolve (bytes, largura, altura)."""
    largura, altura = int(imagem["/Width"]), int(imagem["/Height"])
    filtros = _filtros(imagem)
    if filtros == ["/DCTDecode"]:
        entrada = ["-f", "jpeg_pipe", "-i", "-"]
        dados = imagem._data  # o JPG como está no arquivo
    else:
        entrada = ["-f", "rawvideo", "-pix_fmt", "rgb24" if canais == 3 else "gray",
                   "-s", f"{largura}x{altura}", "-i", "-"]
        dados = imagem.get_data()  # os pixels já descompactados
        if len(dados) != largura * altura * canais:
            return None
    escala = min(1.0, lado_maximo / max(largura, altura))
    nova_largura, nova_altura = max(1, round(largura * escala)), max(1, round(altura * escala))
    jpg = _ffmpeg(*entrada, "-vf", f"scale={nova_largura}:{nova_altura}:flags=lanczos",
                  "-pix_fmt", "yuvj420p" if canais == 3 else "gray", "-q:v", str(qualidade),
                  "-frames:v", "1", "-f", "mjpeg", "-", entrada=dados)
    return jpg, nova_largura, nova_altura


def _imagens_da_pagina(recursos, vistas):
    """As imagens da página (inclusive as de dentro de "formulários" do PDF), cada uma uma vez só."""
    if recursos is None:
        return
    objetos = recursos.get_object().get("/XObject")
    if objetos is None:
        return
    for referencia in objetos.get_object().values():
        chave = getattr(referencia, "idnum", None) or id(referencia)
        if chave in vistas:
            continue
        vistas.add(chave)
        objeto = referencia.get_object()
        if objeto.get("/Subtype") == "/Image":
            yield objeto
        elif objeto.get("/Subtype") == "/Form":
            yield from _imagens_da_pagina(objeto.get("/Resources"), vistas)


def comprimir_pdf(entrada, saida, nivel=NIVEL_PADRAO_PDF):
    """Comprime o PDF. Devolve {"antes", "depois", "paginas", "imagens", "ja_otimizado"}.
    Se não der para economizar, não deixa nada em "saida" e "ja_otimizado" é True."""
    config = NIVEIS_PDF.get(nivel, NIVEIS_PDF[NIVEL_PADRAO_PDF])
    antes = os.path.getsize(entrada)
    escritor = PdfWriter(clone_from=_abrir(entrada))

    vistas, trocadas = set(), 0
    for pagina in escritor.pages:
        # Maior lado que uma imagem precisa ter: a página inteira no DPI do nível
        caixa = pagina.mediabox
        lado_maximo = round(max(float(caixa.width), float(caixa.height)) / 72 * config["dpi"])
        for imagem in _imagens_da_pagina(pagina.get("/Resources"), vistas):
            canais = _canais(imagem)
            filtros = _filtros(imagem)
            if (canais is None or imagem.get("/ImageMask") or imagem.get("/Decode") is not None
                    or int(imagem.get("/BitsPerComponent", 0)) != 8
                    or not set(filtros) <= {"/DCTDecode", "/FlateDecode"}):
                continue
            try:
                resultado = _recomprimir(imagem, canais, lado_maximo, config["qualidade"])
            except Exception as e:
                print(f"[DOCUMENTOS] Imagem mantida como estava: {e}")
                continue
            if not resultado or len(resultado[0]) >= len(imagem._data) * 0.95:
                continue  # não ficou (bem) menor: mantém a original
            jpg, largura, altura = resultado
            imagem._data = jpg
            imagem.decoded_self = None
            imagem[NameObject("/Filter")] = NameObject("/DCTDecode")
            imagem[NameObject("/Width")] = NumberObject(largura)
            imagem[NameObject("/Height")] = NumberObject(altura)
            imagem.pop(NameObject("/DecodeParms"), None)
            trocadas += 1

    # O resto: textos compactados e objetos repetidos guardados uma vez só
    for pagina in escritor.pages:
        pagina.compress_content_streams()
    escritor.compress_identical_objects()  # padrão: tira os repetidos e os que sobraram sem uso
    with open(saida, "wb") as f:
        escritor.write(f)

    depois = os.path.getsize(saida)
    ja_otimizado = depois > antes * (1 - ECONOMIA_MINIMA)
    if ja_otimizado:
        os.remove(saida)
    return {"antes": antes, "depois": antes if ja_otimizado else depois, "paginas": len(escritor.pages),
            "imagens": trocadas, "ja_otimizado": ja_otimizado}


# ==========================================
# FOTOS -> PDF
# ==========================================
# Uma foto por página, na ordem enviada. "a4": página A4 (em pé ou deitada,
# conforme a foto), com margem, boa para imprimir e mandar documentos; "foto":
# a página do tamanho da foto. Cada foto passa pelo FFmpeg antes: vira JPG,
# fica em pé (fotos de celular), perde a localização (GPS) e ganha fundo branco
# onde era transparente (PNG).
TAMANHOS_DE_PAGINA = ("a4", "foto")
A4 = (595, 842)        # em pontos (1/72 de polegada)
MARGEM_A4 = 28         # ~1 cm
DPI_DAS_FOTOS = 200    # resolução máxima das fotos no PDF (boa para imprimir, sem pesar)
EXTENSOES_DE_FOTO = ("jpg", "jpeg", "png", "webp", "heic", "heif")


def _medidas(caminho):
    saida = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", caminho],
                           capture_output=True, text=True, creationflags=SEM_JANELA).stdout
    largura, altura = saida.strip().split(",")[:2]
    return int(largura), int(altura)


def fotos_para_pdf(fotos, saida, tamanho="a4"):
    """Junta as fotos (caminhos, na ordem) num PDF. Devolve o número de páginas."""
    import pypdfium2 as pdfium

    lado_maximo = round(max(A4) / 72 * DPI_DAS_FOTOS)  # ~2340 px
    pdf = pdfium.PdfDocument.new()
    temporarios = []
    try:
        for numero, foto in enumerate(fotos):
            jpg = f"{saida}.{numero}.jpg"
            temporarios.append(jpg)
            # Fundo branco por baixo (para PNG transparente), reduz se for maior que o necessário, JPG
            _ffmpeg("-i", foto, "-frames:v", "1", "-filter_complex",
                    "[0]format=rgba,split[a][b];[a]drawbox=c=white:t=fill[fundo];[fundo][b]overlay=format=auto,"
                    f"scale='min(iw,{lado_maximo})':'min(ih,{lado_maximo})':force_original_aspect_ratio=decrease"
                    ":flags=lanczos,format=yuvj420p",
                    "-map_metadata", "-1", "-q:v", "3", jpg)
            largura, altura = _medidas(jpg)

            if tamanho == "foto":
                pagina_l, pagina_a = largura * 72 / DPI_DAS_FOTOS, altura * 72 / DPI_DAS_FOTOS
                foto_l, foto_a, x, y = pagina_l, pagina_a, 0, 0
            else:
                pagina_l, pagina_a = (A4[1], A4[0]) if largura > altura else A4  # deitada se a foto for
                escala = min((pagina_l - 2 * MARGEM_A4) / largura, (pagina_a - 2 * MARGEM_A4) / altura)
                foto_l, foto_a = largura * escala, altura * escala
                x, y = (pagina_l - foto_l) / 2, (pagina_a - foto_a) / 2  # centralizada

            pagina = pdf.new_page(pagina_l, pagina_a)
            imagem = pdfium.PdfImage.new(pdf)
            imagem.load_jpeg(jpg, pages=[pagina])
            imagem.set_matrix(pdfium.PdfMatrix().scale(foto_l, foto_a).translate(x, y))
            pagina.insert_obj(imagem)
            pagina.gen_content()
        pdf.save(saida)
        return len(fotos)
    finally:
        pdf.close()
        for temporario in temporarios:
            if os.path.exists(temporario):
                os.remove(temporario)


# ==========================================
# PDF -> IMAGENS
# ==========================================
# Cada página escolhida vira uma imagem, desenhada pelo PDFium (como o Chrome
# mostraria) e salva pelo FFmpeg.
FORMATOS_DE_IMAGEM = ("jpg", "png")
QUALIDADES_DE_IMAGEM = {"tela": 110, "impressao": 300}  # DPI
LADO_MAXIMO_DA_IMAGEM = 8000  # páginas enormes (pôsteres) não viram imagens gigantes
MAXIMO_DE_PAGINAS = 500


def ler_paginas(texto, total):
    """"1-3, 5" -> [1, 2, 3, 5]. Vazio = todas. Página fora do PDF vira ValueError (com a mensagem)."""
    texto = (texto or "").replace(" ", "")
    if not texto:
        return list(range(1, total + 1))
    escolhidas = []
    for parte in texto.split(","):
        if not parte:
            continue
        inicio, _, fim = parte.partition("-")
        if not inicio.isdigit() or (fim and not fim.isdigit()):
            raise ValueError(f"Não entendi as páginas \"{parte}\". Use, por exemplo: 1-3, 5")
        inicio, fim = int(inicio), int(fim or inicio)
        if inicio < 1 or fim > total or inicio > fim:
            raise ValueError(f"O PDF tem {total} página(s): \"{parte}\" não existe.")
        escolhidas.extend(n for n in range(inicio, fim + 1) if n not in escolhidas)
    return escolhidas


def abrir_com_pdfium(entrada):
    import pypdfium2 as pdfium
    try:
        return pdfium.PdfDocument(entrada)
    except pdfium.PdfiumError as e:
        if "password" in str(e).lower():
            raise PdfProtegido()
        raise


def pdf_para_imagens(entrada, pasta_saida, formato="jpg", dpi=QUALIDADES_DE_IMAGEM["tela"], paginas=None):
    """Salva as páginas escolhidas ("1-3, 5"; vazio = todas) como "Página 01.jpg"... na pasta.
    Devolve a lista de arquivos criados."""
    pdf = abrir_com_pdfium(entrada)
    try:
        total = len(pdf)
        escolhidas = ler_paginas(paginas, total)
        if len(escolhidas) > MAXIMO_DE_PAGINAS:
            raise ValueError(f"São {len(escolhidas)} páginas: escolha até {MAXIMO_DE_PAGINAS} de uma vez.")
        os.makedirs(pasta_saida, exist_ok=True)
        digitos = max(2, len(str(total)))
        criados = []
        for numero in escolhidas:
            pagina = pdf[numero - 1]
            largura, altura = pagina.get_size()
            escala = min(dpi / 72, LADO_MAXIMO_DA_IMAGEM / max(largura, altura))
            bitmap = pagina.render(scale=escala)  # fundo branco, cores em BGR
            # Cada linha do bitmap pode ter bytes de sobra no fim: o FFmpeg quer as linhas coladas
            bruto, passo, util = bytes(bitmap.buffer), bitmap.stride, bitmap.width * 3
            pixels = bruto if passo == util else b"".join(
                bruto[linha * passo: linha * passo + util] for linha in range(bitmap.height))
            destino = os.path.join(pasta_saida, f"Página {str(numero).zfill(digitos)}.{formato}")
            _ffmpeg("-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{bitmap.width}x{bitmap.height}", "-i", "-",
                    *(["-q:v", "2", "-pix_fmt", "yuvj420p"] if formato == "jpg" else []), destino, entrada=pixels)
            criados.append(destino)
        return criados
    finally:
        pdf.close()
