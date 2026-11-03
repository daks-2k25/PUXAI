"""Ciclo de vida do programa: porta, uma instância só, reiniciar e encerrar.

Também guarda o estado da janela, que é compartilhado entre a inicialização
(app.py), a janela (janela.py) e as rotas do painel (rotas/programa.py).
"""
import glob
import os
import socket
import subprocess
import sys
import threading
import time

from servicos.caminhos import EXECUTAVEL, PASTA_DOWNLOADS, PASTA_RECURSOS
from servicos.downloader import downloads_em_andamento, ids_guardados

PORTA = int(os.environ.get("PORTA", 5000))
ENDERECO_PAINEL = f"http://127.0.0.1:{PORTA}"

# Arquivo de entrada, para reabrir o programa com "python app.py"
ARQUIVO_PRINCIPAL = os.path.join(PASTA_RECURSOS, "app.py")

# Janela própria do programa (pywebview). Fica None quando o painel abre no
# navegador, o que acontece só se a janela não puder ser criada neste PC.
janela = None
# Virou True quando a pessoa clica em "Abrir no navegador": a janela fecha, mas o programa continua
trocando_para_navegador = False

# Modo navegador: o programa fecha sozinho quando ninguém está com o painel
# aberto há esse tempo e não há downloads em andamento
FECHAR_SEM_PAINEL_SEGUNDOS = 3 * 60
ultimo_sinal_do_painel = time.time()


def na_janela():
    """True se o painel está na janela própria (e não no navegador)."""
    return janela is not None and not trocando_para_navegador


def ja_esta_rodando():
    """Verifica se o programa já está aberto (porta ocupada)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # No Windows, conectar numa porta fechada leva ~2s para falhar.
        # Se o programa estiver aberto, a resposta vem em milissegundos.
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", PORTA)) == 0


def esperar_servidor(limite_segundos=10):
    for _ in range(limite_segundos * 20):
        if ja_esta_rodando():
            return True
        time.sleep(0.05)
    return False


def esperar_porta_livre(limite_segundos=15):
    """Ao reiniciar: espera o programa antigo terminar de fechar e soltar a porta."""
    limite = time.time() + limite_segundos
    while ja_esta_rodando() and time.time() < limite:
        time.sleep(0.2)


def comando_do_programa():
    """(pasta, [comando]) para abrir este programa de novo: o Puxai.exe ou "python app.py"."""
    if EXECUTAVEL:
        return os.path.dirname(sys.executable), [sys.executable]
    return os.path.dirname(ARQUIVO_PRINCIPAL), [sys.executable, ARQUIVO_PRINCIPAL]


def reiniciar(modo):
    """Abre o programa de novo daqui a ~2 segundos (tempo de este processo fechar),
    já no modo pedido ("janela" ou "navegador")."""
    pasta, comando = comando_do_programa()
    ambiente = dict(os.environ, PUXAI_MODO=modo)
    if sys.platform != "win32":
        subprocess.Popen(["sh", "-c", 'sleep 2; exec "$@"', "puxai", *comando],
                         cwd=pasta, env=ambiente, start_new_session=True)
        return
    comando = " ".join(f'"{parte}"' for parte in comando)
    # "ping" para esperar: o "timeout" do Windows falha quando não há janela de console
    subprocess.Popen(
        f'cmd /c ping -n 3 127.0.0.1 >nul & start "" {comando}',
        cwd=pasta, env=ambiente,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


# Funções chamadas logo antes de o programa fechar (ex.: tirar o ícone da bandeja,
# que senão ficaria "fantasma" perto do relógio até alguém passar o mouse)
ao_encerrar = []


def encerrar():
    print("Encerrando o programa...")
    for funcao in ao_encerrar:
        try:
            funcao()
        except Exception as e:
            print(f"[ENCERRAR] {e}")
    os._exit(0)


# Sobras certamente incompletas na pasta temporária (downloads\) de vezes anteriores
# em que o programa fechou no meio de algo. Os arquivos prontos não entram aqui.
SOBRAS = ("*.part", "*.ytdl", "*_original.*", "*_comprimido.mp4", "*_passadas*", "*_referencia.nut", "*_tentativa.*")


def limpar_sobras():
    """Chamado ao abrir o programa, quando nada está em andamento.
    Os pedaços dos downloads da fila guardada ficam: eles continuam de onde pararam."""
    apagadas = 0
    guardados = ids_guardados()
    for padrao in SOBRAS:
        for arquivo in glob.glob(os.path.join(PASTA_DOWNLOADS, padrao)):
            if os.path.basename(arquivo).split(".", 1)[0] in guardados:
                continue
            try:
                os.remove(arquivo)
                apagadas += 1
            except OSError:
                pass
    if apagadas:
        print(f"[LIMPEZA] {apagadas} arquivo(s) temporário(s) de antes apagado(s).")


def encerrar_em_instantes():
    """Fecha daqui a meio segundo: dá tempo de a rota responder ao painel antes."""
    threading.Timer(0.5, encerrar).start()


def painel_deu_sinal():
    global ultimo_sinal_do_painel
    ultimo_sinal_do_painel = time.time()


def fechar_quando_ninguem_usar():
    """Modo navegador: encerra quando nenhuma aba do painel dá sinal há 3 minutos."""
    while True:
        time.sleep(30)
        if not downloads_em_andamento() and time.time() - ultimo_sinal_do_painel > FECHAR_SEM_PAINEL_SEGUNDOS:
            encerrar()
