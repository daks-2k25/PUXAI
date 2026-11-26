"""Windows com acento no caminho do programa (pasta "PUXAÌ", usuário "João"...).

O curl_cffi (que o yt-dlp usa para se passar por navegador no TikTok, Instagram,
Vimeo...) não consegue abrir o arquivo de certificados num caminho com acento:
todo download desses sites falha com "curl: (77) error adding trust anchors".
Aqui ele recebe um caminho sem acento para o mesmo arquivo.

Precisa rodar antes do primeiro import do curl_cffi (veja servicos/__init__.py).
"""
import atexit
import os
import shutil
import sys
import tempfile


def _nome_curto(caminho):
    """O nome curto do Windows (C:\\...\\PUXA~1\\...), que aponta para o mesmo arquivo.
    Alguns discos não criam nomes curtos: aí volta o caminho como está."""
    import ctypes
    saida = ctypes.create_unicode_buffer(32768)
    return saida.value if ctypes.windll.kernel32.GetShortPathNameW(caminho, saida, len(saida)) else caminho


def _copia_sem_acento(caminho):
    """Sem nome curto: copia o arquivo para uma pasta temporária sem acento. A pasta é
    nova e só deste usuário (mkdtemp), para ninguém trocar os certificados; sai ao fechar."""
    for base in (tempfile.gettempdir(), os.environ.get("PROGRAMDATA", "")):
        if not base or not base.isascii():
            continue
        try:
            pasta = tempfile.mkdtemp(prefix="puxai-certificados-", dir=base)
            atexit.register(shutil.rmtree, pasta, ignore_errors=True)
            return shutil.copy(caminho, os.path.join(pasta, "cacert.pem"))
        except OSError:
            pass
    return None


def preparar():
    if sys.platform != "win32":
        return
    # Quem já escolheu os certificados (ex.: rede de empresa) continua com os seus
    if any(os.environ.get(v) for v in ("CURL_CA_BUNDLE", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE")):
        return
    try:
        import certifi
    except ImportError:
        return
    caminho = certifi.where()
    if caminho.isascii():
        return
    sem_acento = _nome_curto(caminho)
    if not sem_acento.isascii():
        sem_acento = _copia_sem_acento(caminho)
    if sem_acento:
        os.environ["CURL_CA_BUNDLE"] = sem_acento
    else:
        print("[CERTIFICADOS] A pasta do programa tem acento e não consegui contornar: "
              "mova o Puxaí para uma pasta sem acentos.")
