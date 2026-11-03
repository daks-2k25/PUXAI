"""Ícone do Puxaí na bandeja do Linux (perto do relógio), igual ao do Windows (bandeja.py).

- Clique: abre o Puxaí (traz a janela para a frente ou abre o painel no navegador)
- Botão direito: menu com Abrir, Abrir no navegador, Abrir a pasta dos
  arquivos e Encerrar (que pergunta antes se ainda há algo em andamento)
- Ao parar o mouse: "Puxaí", ou "Puxaí · 3 em andamento"

Feito com o Qt, que já vem junto para a janela própria (pywebview[qt]). O Qt
usa o padrão de ícones de bandeja do Linux (StatusNotifierItem), que funciona
no KDE, XFCE, Cinnamon, MATE, Budgie e no Ubuntu. No GNOME sem a extensão
"AppIndicator" (ex.: Fedora, Debian) não existe bandeja: o programa segue sem o ícone.

O Qt precisa rodar na thread principal. Na janela própria, quem mantém o Qt
rodando é o pywebview; no modo navegador, é rodar_ate_encerrar().
"""
import sys
import threading

from servicos import destinos, programa, sistema
from servicos.caminhos import PASTA_PAINEL
from servicos.downloader import quantos_em_andamento

# Guardados aqui: sem uma referência, o Python apagaria o ícone e o menu
_app = None
_icone = None
_menu = None
_timer = None


def iniciar():
    """Põe o ícone na bandeja (chamado na thread principal). Se não der, o programa segue sem ele."""
    global _app
    if not sys.platform.startswith("linux"):
        return
    try:
        from servicos.janela import testar_qt_no_linux
        testar_qt_no_linux()  # sem isso, um Qt quebrado derrubaria o programa inteiro

        # A janela do painel (Qt WebEngine) exige estas duas coisas antes de o QApplication existir
        from qtpy import QtWebEngineWidgets  # noqa: F401
        from qtpy.QtCore import QCoreApplication, Qt
        from qtpy.QtGui import QGuiApplication
        from qtpy.QtWidgets import QApplication, QSystemTrayIcon
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        # O mesmo nome do atalho do menu (puxai.desktop)
        QGuiApplication.setDesktopFileName("puxai")

        _app = QApplication.instance() or QApplication(sys.argv)
        # Fechar uma caixa de diálogo (ou a janela) não encerra o Qt: quem decide é o programa
        _app.setQuitOnLastWindowClosed(False)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("[BANDEJA] Este sistema não tem área de ícones perto do relógio "
                  "(no GNOME, ela vem com a extensão AppIndicator); seguindo sem o ícone.")
            return
        _criar_icone()
    except Exception as e:
        print(f"[BANDEJA] Ícone da bandeja indisponível: {e}")


def _criar_icone():
    global _icone, _menu, _timer
    import os

    from qtpy.QtCore import QTimer
    from qtpy.QtGui import QIcon
    from qtpy.QtWidgets import QMenu, QSystemTrayIcon

    _icone = QSystemTrayIcon(QIcon(os.path.join(PASTA_PAINEL, "icone.png")))
    _menu = QMenu()
    _menu.addAction("Abrir o Puxaí").triggered.connect(lambda: _em_segundo_plano(_abrir))
    _menu.addAction("Abrir no navegador").triggered.connect(
        lambda: _em_segundo_plano(lambda: sistema.abrir_no_navegador(programa.ENDERECO_PAINEL)))
    _menu.addAction("Abrir a pasta dos arquivos").triggered.connect(lambda: _em_segundo_plano(_abrir_pasta))
    _menu.addSeparator()
    _menu.addAction("Encerrar o Puxaí").triggered.connect(_encerrar)
    _icone.setContextMenu(_menu)

    def ao_clicar(motivo):
        if motivo == QSystemTrayIcon.ActivationReason.Trigger:
            _em_segundo_plano(_abrir)

    _icone.activated.connect(ao_clicar)
    _atualizar_dica()
    _timer = QTimer()
    _timer.timeout.connect(_atualizar_dica)
    _timer.start(2000)
    _icone.show()
    print("[BANDEJA] Ícone do Puxaí perto do relógio.")


def _em_segundo_plano(acao):
    # Fora da thread do Qt: algumas ações da janela (pywebview) esperam resposta dela
    def rodar():
        try:
            acao()
        except Exception as e:
            print(f"[BANDEJA] Não foi possível executar a ação: {e}")

    threading.Thread(target=rodar, daemon=True).start()


def _abrir():
    if programa.na_janela():
        from servicos.janela import trazer_para_frente
        trazer_para_frente()
    else:
        sistema.abrir_no_navegador(programa.ENDERECO_PAINEL)


def _abrir_pasta():
    pastas = destinos.configuracao()
    sistema.abrir(destinos.pasta_para("video") if pastas["modo"] == "separadas" else pastas["tudo"])


def _encerrar():
    # Na thread do Qt: a pergunta é uma caixa de diálogo do Qt
    from qtpy.QtWidgets import QMessageBox

    quantos = quantos_em_andamento()
    if quantos:
        resposta = QMessageBox.question(
            None, "Encerrar o Puxaí?",
            f"Ainda há {quantos} {'item' if quantos == 1 else 'itens'} em andamento "
            "(downloads ou compressões). Se encerrar agora, eles serão interrompidos.\n\nEncerrar mesmo assim?",
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return
    programa.encerrar()


def _atualizar_dica():
    quantos = quantos_em_andamento()
    _icone.setToolTip("Puxaí" if not quantos else f"Puxaí · {quantos} em andamento")


def rodar_ate_encerrar(servidor):
    """Modo navegador: mantém o Qt rodando (o ícone responde a cliques) até o programa encerrar.
    Sem o Qt (ou fora do Linux), só espera o servidor."""
    if _app is not None:
        _app.exec()
    # Sem o Qt, ou se o laço dele parar por algum motivo: o programa continua até encerrar()
    servidor.join()
