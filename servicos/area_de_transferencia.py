"""Link de vídeo copiado (o painel oferece "Colar" quando você copia um link).

Lê o texto da área de transferência do sistema direto (o programa roda no
mesmo computador), em vez de pedir ao navegador, que perguntaria permissão
toda vez. No Linux, pelo xclip, xsel ou wl-paste (o que estiver instalado). Só devolve algo se o texto copiado for um link de um site que o
yt-dlp sabe baixar; qualquer outro texto copiado (senhas, mensagens...) não
sai daqui nem fica guardado.
"""
import ctypes
import os
import re
import shutil
import subprocess
import sys
import time

from servicos import sistema
from servicos.sites import nome_amigavel

CF_UNICODETEXT = 13
LINK = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
TAMANHO_MAXIMO = 4000  # texto maior que isso não é "um link copiado"

_extratores = None
_cache = {}


def ler_texto():
    """O texto copiado agora (ou None: nada copiado, não é texto ou não deu para ler)."""
    if sys.platform.startswith("linux"):
        return _ler_texto_no_linux()
    if sys.platform != "win32":
        return None
    from ctypes import wintypes
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalSize.restype = ctypes.c_size_t
    kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]

    # Outro programa pode estar usando a área de transferência neste instante
    for _ in range(5):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return None
    try:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return None
        dados = user32.GetClipboardData(CF_UNICODETEXT)
        if not dados:
            return None
        if kernel32.GlobalSize(dados) > TAMANHO_MAXIMO * 2:  # 2 bytes por letra
            return None
        ponteiro = kernel32.GlobalLock(dados)
        if not ponteiro:
            return None
        try:
            return ctypes.wstring_at(ponteiro)
        finally:
            kernel32.GlobalUnlock(dados)
    finally:
        user32.CloseClipboard()


# No Linux, a área de transferência é lida por um programa pequeno. Com o Wayland
# (GNOME e KDE novos), xclip e xsel leem a do Xwayland, que o sistema mantém
# igual à do Wayland; o wl-paste fica por último porque no GNOME ele abre uma
# janelinha por um instante para conseguir ler.
COMANDOS_LINUX = (
    ("DISPLAY", ["xclip", "-selection", "clipboard", "-out", "-target", "UTF8_STRING"]),
    ("DISPLAY", ["xsel", "--clipboard", "--output"]),
    ("WAYLAND_DISPLAY", ["wl-paste", "--no-newline", "--type", "text/plain;charset=utf-8"]),
)


def _ler_texto_no_linux():
    for tela, comando in COMANDOS_LINUX:
        if not os.environ.get(tela) or not shutil.which(comando[0]):
            continue
        try:
            resultado = sistema.rodar(comando, capture_output=True, timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if resultado.returncode == 0:
            if len(resultado.stdout) > TAMANHO_MAXIMO * 4:  # até 4 bytes por letra (UTF-8)
                return None
            return resultado.stdout.decode("utf-8", errors="replace")
    return None


def _site_do_link(url):
    """Nome do site se o yt-dlp sabe baixar desse link; None se não sabe."""
    global _extratores
    if url in _cache:
        return _cache[url]
    if re.match(r"https?://(www\.)?pin\.it/", url, re.IGNORECASE):
        return "Pinterest"  # link curto do app do Pinterest (o yt-dlp só entende o link do pin)
    if _extratores is None:
        from yt_dlp.extractor import gen_extractor_classes
        # "Generic" aceita qualquer link: não diz nada sobre ser um site de vídeo
        _extratores = [e for e in gen_extractor_classes() if e.ie_key() != "Generic"]
    extrator = next((e for e in _extratores if e.suitable(url)), None)
    site = nome_amigavel(extrator.ie_key(), extrator.IE_NAME) if extrator else None
    if len(_cache) > 200:
        _cache.clear()
    _cache[url] = site
    return site


def link_de_video(texto):
    """{"url", "site"} do primeiro link de vídeo no texto, ou None."""
    if not texto or len(texto) > TAMANHO_MAXIMO:
        return None
    achado = LINK.search(texto)
    if not achado:
        return None
    url = achado.group(0).rstrip("),.;")
    site = _site_do_link(url)
    return {"url": url, "site": site} if site else None


def link_copiado():
    """O link de vídeo que está copiado agora, ou None."""
    return link_de_video(ler_texto())
