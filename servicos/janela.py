"""Janela própria do programa (pywebview), com a logo na barra de tarefas.

No Windows, a janela usa o WebView2 (o Edge que vem no sistema); no Linux, o Qt
(que vem junto, pelo pywebview[qt]). Sem ela, o painel abre no navegador.
"""
import os
import subprocess
import sys

from servicos import preferencias, programa
from servicos.caminhos import PASTA_PAINEL
from servicos.downloader import downloads_em_andamento

TITULO = "Puxaí"
# Cor de fundo enquanto a página carrega (a mesma do --fundo de cada tema)
FUNDO = {"claro": "#fff4ea", "escuro": "#150f0c"}


def _achar_janela(titulo=TITULO):
    """A janela (HWND) com esse título que pertence a este processo, ou None."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    meu_pid = os.getpid()
    encontrada = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def verificar(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == meu_pid:
            texto = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, texto, 256)
            if texto.value == titulo:
                encontrada.append(hwnd)
                return False
        return True

    user32.EnumWindows(verificar, 0)
    return encontrada[0] if encontrada else None


def barra_de_titulo_escura(escura):
    """Barra de título escura (ou clara) como a dos aplicativos do Windows no modo escuro.
    Funciona no Windows 10 (20H1 em diante) e 11; nos outros, não faz nada."""
    hwnd = _achar_janela()
    if not hwnd:
        return
    import ctypes
    from ctypes import wintypes

    valor = ctypes.c_int(1 if escura else 0)
    dwmapi = ctypes.windll.dwmapi
    dwmapi.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    for atributo in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (19 nas versões antigas do Windows 10)
        if dwmapi.DwmSetWindowAttribute(hwnd, atributo, ctypes.byref(valor), ctypes.sizeof(valor)) == 0:
            break
    # Redesenha a barra (sem isso, ela só muda quando a janela perde e ganha o foco)
    user32 = ctypes.windll.user32
    SWP_SEM_MUDAR = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020  # NOSIZE|NOMOVE|NOZORDER|NOACTIVATE|FRAMECHANGED
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, SWP_SEM_MUDAR)


def colocar_icone_na_janela(titulo, caminho_icone):
    """Troca o ícone da janela (barra de título e barra de tarefas).

    Usa mensagens do Windows enviadas com PostMessage, que não esperam resposta.
    Não mexe na janela pelo .NET a partir de outra thread: isso pode travar a
    janela ("Não respondendo"), porque só a thread dona da janela pode alterá-la.
    """
    hwnd = _achar_janela(titulo)
    if not hwnd:
        return
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    encontrada = [hwnd]

    IMAGE_ICON, LR_LOADFROMFILE, WM_SETICON = 1, 0x10, 0x80
    # Tipos declarados: no Windows 64 bits, os identificadores não cabem num int comum
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    for tipo, metrica in ((1, 11), (0, 49)):  # ícone grande (SM_CXICON) e pequeno (SM_CXSMICON)
        tamanho = user32.GetSystemMetrics(metrica)
        icone = user32.LoadImageW(None, caminho_icone, IMAGE_ICON, tamanho, tamanho, LR_LOADFROMFILE)
        if icone:
            user32.PostMessageW(encontrada[0], WM_SETICON, tipo, icone)


_resultado_do_teste_do_qt = None


def testar_qt_no_linux():
    """Confere, num processo à parte, se o Qt (janela e ícone da bandeja) abre neste PC.

    Quando falta algo no sistema (ex.: a biblioteca libxcb-cursor0) ou não há
    tela (servidor, SSH), o Qt encerra o programa inteiro na hora, sem dar para
    tratar o erro. Testando antes, o programa só usa o navegador nesses casos.
    O resultado fica guardado: o teste roda uma vez só.
    """
    global _resultado_do_teste_do_qt
    if _resultado_do_teste_do_qt is None:
        try:
            _rodar_teste_do_qt()
            _resultado_do_teste_do_qt = ""
        except RuntimeError as e:
            _resultado_do_teste_do_qt = str(e)
    if _resultado_do_teste_do_qt:
        raise RuntimeError(_resultado_do_teste_do_qt)


def _rodar_teste_do_qt():
    pasta, comando = programa.comando_do_programa()
    try:
        resultado = subprocess.run([*comando, "--testar-janela"], cwd=pasta,
                                   capture_output=True, text=True, errors="replace", timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"o teste da janela não terminou: {e}")
    if resultado.returncode != 0:
        detalhe = (resultado.stderr.strip().splitlines() or [f"código {resultado.returncode}"])[-1]
        raise RuntimeError(f"o Qt não abriu: {detalhe}")


def abrir_janela():
    """Abre o painel numa janela própria. Bloqueia até a janela ser fechada."""
    if sys.platform.startswith("linux"):
        testar_qt_no_linux()

    import webview

    if sys.platform == "win32":
        import ctypes
        # Faz a barra de tarefas tratar o programa como um aplicativo próprio (e não como "Python")
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Puxai.Painel")
    else:
        from qtpy.QtGui import QGuiApplication
        # Liga a janela ao atalho do menu (puxai.desktop): a barra de tarefas mostra a logo e o nome
        QGuiApplication.setDesktopFileName("puxai")

    tema = preferencias.tema_em_uso()
    janela = programa.janela = webview.create_window(
        TITULO, programa.ENDERECO_PAINEL,
        width=760, height=900, min_size=(440, 620), background_color=FUNDO[tema],
    )

    def ao_mostrar():
        # Coloca a logo do programa na janela e na barra de tarefas
        try:
            colocar_icone_na_janela(TITULO, os.path.join(PASTA_PAINEL, "icone.ico"))
        except Exception as e:
            print(f"[JANELA] Não foi possível colocar o ícone: {e}")
        if tema == "escuro":
            try:
                barra_de_titulo_escura(True)
            except Exception as e:
                print(f"[JANELA] Não foi possível escurecer a barra de título: {e}")

    def ao_fechar():
        # Trocando para o navegador: o programa continua, então não precisa perguntar
        if programa.trocando_para_navegador:
            return True
        # Avisa antes de fechar se ainda há download acontecendo
        if downloads_em_andamento():
            return janela.create_confirmation_dialog(
                "Fechar o Puxaí?",
                "Ainda há downloads em andamento. Se fechar agora, eles serão interrompidos.",
            )
        return True

    janela.events.shown += ao_mostrar
    janela.events.closing += ao_fechar
    if sys.platform == "win32":
        webview.start(gui="edgechromium")
    else:
        webview.start(gui="qt", icon=os.path.join(PASTA_PAINEL, "icone.png"))


def trazer_para_frente():
    """Clicou no atalho com o programa já aberto: traz a janela para a frente."""
    janela = programa.janela
    janela.restore()
    janela.show()
    janela.on_top = True   # liga e desliga o "sempre no topo" para a
    janela.on_top = False  # janela passar na frente das outras
