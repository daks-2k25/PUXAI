"""Estatísticas anônimas de uso (só com a permissão da pessoa).

Servem para saber quantas pessoas usam o Puxaí e quais sites mais falham, para
saber o que consertar primeiro. São enviadas para o Aptabase, um serviço de
estatísticas feito para aplicativos e focado em privacidade: ele não guarda o
IP nem identifica ninguém (cada abertura do programa vira um código aleatório).

O que é enviado (e nada mais):
- ao abrir: versão do Puxaí, sistema e versão dele, idioma, se é o programa
  pronto ou pelo código, e se abriu na janela ou no navegador
- ao terminar um download: o site (ex.: "YouTube"), MP4 ou MP3 e a qualidade,
  se deu certo, deu erro ou foi cancelado, a mensagem de erro do Puxaí (uma
  frase fixa, ex.: "Esse vídeo não está disponível"), se veio da extensão e se
  foi um trecho ou um download que voltou de quando o programa fechou
Nunca: links, títulos, nomes de arquivo, pastas ou qualquer coisa que identifique a pessoa.

Desligado até haver uma CHAVE_APP: sem ela, o painel nem pergunta.
A permissão fica em .preferencias.json ("estatisticas": true/false; sem a
chave = ainda não perguntou). Se o envio falhar (sem internet...), nada acontece.
"""
import json
import locale
import os
import platform
import random
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone

from servicos import preferencias

# Chave do app no Aptabase (ex.: "A-EU-1234567890"). Vazia: estatísticas desligadas.
CHAVE_APP = ""
VERSAO_DO_ENVIO = "puxai-python@1"
EVENTOS_POR_ENVIO = 25    # o máximo que o Aptabase aceita de uma vez
ENVIAR_A_CADA = 60        # segundos
MAXIMO_NA_FILA = 200      # sem internet por muito tempo: os mais antigos são descartados

# Um código por abertura do programa (o formato que o Aptabase pede: segundos + 8 números)
_sessao = f"{int(time.time())}{random.randint(0, 99999999):08d}"
_fila = []
_trava = threading.Lock()


def disponivel():
    """Há para onde enviar? (Sem a chave, o painel nem pergunta.)"""
    return bool(CHAVE_APP)


def permissao():
    """True (aceitou), False (recusou) ou None (ainda não respondeu)."""
    valor = preferencias.obter("estatisticas")
    return valor if isinstance(valor, bool) else None


def permitido():
    return disponivel() and permissao() is True


def _endereco():
    # PUXAI_URL_ESTATISTICAS troca o endereço, para testar sem enviar de verdade
    return os.environ.get("PUXAI_URL_ESTATISTICAS") or (
        ("https://eu.aptabase.com" if "-EU-" in CHAVE_APP else "https://us.aptabase.com") + "/api/v0/events")


def _sistema():
    if sys.platform.startswith("linux"):
        nome, versao = "Linux", platform.release()
        try:
            with open("/etc/os-release", encoding="utf-8") as f:
                dados = dict(linha.strip().split("=", 1) for linha in f if "=" in linha)
            nome = dados.get("NAME", "Linux").strip('"')
            versao = dados.get("VERSION_ID", versao).strip('"')
        except OSError:
            pass
    elif sys.platform == "win32":
        nome, versao = "Windows", platform.release()
    else:
        nome, versao = platform.system(), platform.release()
    idioma = (locale.getlocale()[0] or "").replace("_", "-")
    from servicos import autoatualizacao
    return {"locale": idioma, "osName": nome, "osVersion": versao, "deviceModel": "",
            "isDebug": os.environ.get("PUXAI_DEBUG") == "1",
            "appVersion": autoatualizacao.versao_instalada(), "sdkVersion": VERSAO_DO_ENVIO}


def registrar(evento, **dados):
    """Guarda um evento para enviar (só se a pessoa permitiu). Nunca trava nem dá erro."""
    if not permitido():
        return
    try:
        momento = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        with _trava:
            _fila.append({"timestamp": momento, "sessionId": _sessao, "eventName": evento,
                          "systemProps": _sistema(), "props": dados})
            del _fila[:-MAXIMO_NA_FILA]
            cheia = len(_fila) >= EVENTOS_POR_ENVIO
        if cheia:
            threading.Thread(target=enviar, daemon=True).start()
    except Exception as e:
        print(f"[ESTATÍSTICAS] {e}")


def enviar(espera=10):
    """Manda o que está na fila (de 25 em 25). Se falhar, os eventos voltam para a fila."""
    if not disponivel():
        return
    while True:
        with _trava:
            lote = _fila[:EVENTOS_POR_ENVIO]
            del _fila[:EVENTOS_POR_ENVIO]
        if not lote:
            return
        pedido = urllib.request.Request(_endereco(), data=json.dumps(lote).encode(), method="POST",
                                        headers={"Content-Type": "application/json", "App-Key": CHAVE_APP})
        try:
            urllib.request.urlopen(pedido, timeout=espera).close()
        except Exception as e:
            with _trava:
                _fila[:0] = lote
                del _fila[:-MAXIMO_NA_FILA]
            print(f"[ESTATÍSTICAS] Não foi possível enviar agora ({e}); tenta de novo depois.")
            return


def iniciar():
    """Envia de tempos em tempos, em segundo plano (só faz algo com a chave configurada)."""
    if not disponivel():
        return

    def repetir():
        while True:
            time.sleep(ENVIAR_A_CADA)
            enviar()

    threading.Thread(target=repetir, daemon=True, name="estatisticas").start()
