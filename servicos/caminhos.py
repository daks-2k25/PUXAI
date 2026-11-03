import os
import sys

# Quando roda como .exe (PyInstaller), os arquivos do painel ficam numa pasta
# temporária (sys._MEIPASS) e a pasta de downloads deve ficar ao lado do .exe.
# Rodando com "python app.py", tudo fica na pasta do projeto.
EXECUTAVEL = getattr(sys, "frozen", False)

if EXECUTAVEL:
    PASTA_RECURSOS = sys._MEIPASS
    PASTA_BASE = os.path.dirname(sys.executable)
else:
    PASTA_RECURSOS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PASTA_BASE = PASTA_RECURSOS

PASTA_PAINEL = os.path.join(PASTA_RECURSOS, "painel")
# Arquivos temporários enquanto o download acontece
PASTA_DOWNLOADS = os.path.join(PASTA_BASE, "downloads")


def _pasta_downloads_do_linux():
    """A pasta Downloads do Linux, com o nome que o sistema usa (ex.: "Transferências").
    Fica em ~/.config/user-dirs.dirs, numa linha XDG_DOWNLOAD_DIR="$HOME/Downloads"."""
    configuracao = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    try:
        with open(os.path.join(configuracao, "user-dirs.dirs"), encoding="utf-8") as f:
            for linha in f:
                if linha.startswith("XDG_DOWNLOAD_DIR="):
                    pasta = linha.split("=", 1)[1].strip().strip('"').replace("$HOME", os.path.expanduser("~"))
                    # "$HOME/" sozinho quer dizer "sem pasta Downloads": usa a padrão
                    if os.path.isabs(pasta) and os.path.normpath(pasta) != os.path.expanduser("~"):
                        return pasta
    except OSError:
        pass
    return None


def _pasta_downloads_do_usuario():
    """A pasta Downloads do usuário, mesmo se ele a moveu (outro disco, OneDrive...)."""
    if sys.platform.startswith("linux"):
        pasta = _pasta_downloads_do_linux()
        if pasta:
            return pasta
    if sys.platform == "win32":
        try:
            import ctypes
            import uuid

            # FOLDERID_Downloads
            guid = uuid.UUID("{374DE290-123F-4565-9164-39C4925E467B}")

            class GUID(ctypes.Structure):
                _fields_ = [("data", ctypes.c_byte * 16)]

            caminho = ctypes.c_wchar_p()
            resultado = ctypes.windll.shell32.SHGetKnownFolderPath(
                ctypes.byref(GUID((ctypes.c_byte * 16)(*guid.bytes_le))), 0, None, ctypes.byref(caminho)
            )
            if resultado == 0 and caminho.value:
                pasta = caminho.value
                ctypes.windll.ole32.CoTaskMemFree(caminho)
                return pasta
        except Exception:
            pass
    return os.path.join(os.path.expanduser("~"), "Downloads")


# Onde os vídeos e músicas prontos são salvos
PASTA_DESTINO = _pasta_downloads_do_usuario()

os.makedirs(PASTA_DOWNLOADS, exist_ok=True)

# Sem a janela preta (Puxai.exe ou pythonw), não existe onde mostrar as
# mensagens. Elas vão para o arquivo Puxai.log, útil se algo der errado.
if sys.stdout is None or sys.stderr is None:
    caminho_registro = os.path.join(PASTA_BASE, "Puxai.log")
    # Continua o arquivo existente; recomeça do zero quando passa de 1 MB
    modo = "w" if os.path.exists(caminho_registro) and os.path.getsize(caminho_registro) > 1_000_000 else "a"
    registro = open(caminho_registro, modo, encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or registro
    sys.stderr = sys.stderr or registro

# Saída indo para um arquivo (ex.: o iniciar.sh manda para o Puxai.log): grava cada
# linha na hora. Sem isso, o Python junta as mensagens e o que faltava gravar se
# perde quando o programa encerra (os._exit), justamente quando algo deu errado.
for _saida in (sys.stdout, sys.stderr):
    try:
        _saida.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

# Se tiver o FFmpeg ao lado do programa, usa ele (não precisa instalar no PC).
# No Linux, o iniciar.sh baixa o FFmpeg para a pasta .ffmpeg se o sistema não tiver.
# No programa gerado para Linux, o Deno também fica ao lado (o yt-dlp procura no PATH).
for _pasta in (PASTA_BASE, os.path.join(PASTA_BASE, ".ffmpeg")):
    if os.path.exists(os.path.join(_pasta, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")):
        os.environ["PATH"] = _pasta + os.pathsep + os.environ.get("PATH", "")
        break
