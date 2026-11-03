"""Puxaí: início do programa (iniciar.bat, iniciar.sh, atalho, Puxai.exe ou "uv run app.py").

Liga o servidor do painel e abre a janela do aplicativo ou o navegador.
O resto fica organizado em pastas:

- rotas/     endereços da API usados pelo painel (um arquivo por área)
- servicos/  o que o programa faz (downloads, fotos, histórico, janela...)
- painel/    o site do painel (HTML, CSS e JavaScript)
"""
import os
import sys
import threading
import urllib.request

# Linux: o programa se abre assim por um instante, antes de abrir a janela
# própria, para conferir se ela funciona neste PC (veja servicos/janela.py)
if "--testar-janela" in sys.argv:
    from qtpy import QtWebEngineWidgets  # noqa: F401
    from qtpy.QtWidgets import QApplication
    QApplication([])
    sys.exit(0)

from servicos import atualizador
atualizador.usar_versao_atualizada()  # Precisa vir antes de qualquer import do yt-dlp

from rotas import criar_app
from servicos import (atalho, atualizacao_do_programa, bandeja_linux, downloader, estatisticas, preferencias, programa,
                      sistema)
from servicos.caminhos import EXECUTAVEL
from servicos.janela import abrir_janela

app = criar_app()


def iniciar_servidor():
    from waitress import serve
    # Waitress: servidor robusto (o do Flask é só para desenvolvimento).
    # threads=16: atende o painel enquanto os downloads acontecem
    # max_request_body_size: o padrão (1 GB) barraria vídeos grandes de celular (4K)
    serve(app, host="127.0.0.1", port=programa.PORTA, threads=16, max_request_body_size=32 * 1024**3)


def usar_navegador(servidor, abrir=True):
    """Modo navegador: o painel fica numa aba e o programa roda em segundo plano.
    Fecha sozinho 3 minutos depois que nenhuma aba estiver aberta (sem downloads)."""
    programa.janela = None
    programa.painel_deu_sinal()
    print(f"Painel no navegador: {programa.ENDERECO_PAINEL}")
    if abrir:
        sistema.abrir_no_navegador(programa.ENDERECO_PAINEL)
    threading.Thread(target=programa.fechar_quando_ninguem_usar, daemon=True).start()
    # No Linux, mantém o ícone da bandeja respondendo; no Windows (ou sem o ícone), só espera
    bandeja_linux.rodar_ate_encerrar(servidor)


if __name__ == "__main__":
    # Reiniciando pelo painel: o programa antigo ainda pode estar fechando. Sem
    # esperar, ele seria confundido com "já está aberto" e o navegador abriria
    # uma aba que dá "conexão recusada" logo depois que ele fecha.
    if os.environ.get("PUXAI_MODO"):
        programa.esperar_porta_livre()

    # Clicou de novo com o programa já aberto: só traz a janela para a frente
    if programa.ja_esta_rodando():
        try:
            pedido = urllib.request.Request(f"{programa.ENDERECO_PAINEL}/api/focar", method="POST")
            urllib.request.urlopen(pedido, timeout=3)
        except Exception:
            sistema.abrir_no_navegador(programa.ENDERECO_PAINEL)
        sys.exit(0)

    print("==========================================")
    print("                Puxaí")
    print("==========================================")

    programa.limpar_sobras()  # temporários de uma vez anterior que fechou no meio de algo
    downloader.retomar_fila()  # downloads que não terminaram da vez anterior
    if EXECUTAVEL:
        atualizacao_do_programa.limpar_sobras()  # atualização do programa que ficou pela metade
    atalho.criar()  # Linux: atalho "Puxaí" no menu de aplicativos (no Windows, quem cria é o iniciar.ps1)

    servidor = threading.Thread(target=iniciar_servidor, daemon=True)
    servidor.start()
    programa.esperar_servidor()
    # Ícone perto do relógio (abrir, navegador, pasta, encerrar)
    if sys.platform == "win32":
        # Feito com as funções do Windows: nem dá para importar em outro sistema
        from servicos import bandeja
        bandeja.iniciar()
    else:
        bandeja_linux.iniciar()  # com o Qt, na thread principal (só faz algo no Linux)
    atualizador.verificar_atualizacao()  # Só faz algo dentro do .exe, uma vez por dia
    estatisticas.iniciar()  # só com a chave configurada e a permissão da pessoa
    programa.ao_encerrar.append(lambda: estatisticas.enviar(espera=2))  # manda o que faltou, sem demorar

    # Janela do aplicativo ou navegador: escolhido em Configurações (⚙) no painel.
    # PUXAI_MODO força um modo uma vez (usado ao reabrir pelo painel).
    modo = os.environ.pop("PUXAI_MODO", "") or preferencias.modo_de_abertura()
    estatisticas.registrar("abriu", instalacao="programa pronto" if EXECUTAVEL else "pelo código", modo=modo)

    if modo == "janela":
        try:
            abrir_janela()
        except Exception as e:
            # Sem a janela (ex.: WebView2 ausente, ou o Qt não abre no Linux), usa o navegador
            print(f"[JANELA] Não foi possível abrir a janela própria ({e}); usando o navegador.")
            usar_navegador(servidor)
        else:
            if not programa.trocando_para_navegador:
                programa.encerrar()  # a janela foi fechada
            # "Abrir no navegador": a aba já foi aberta; o programa segue no navegador
            usar_navegador(servidor, abrir=False)
    else:
        usar_navegador(servidor)
