"""Aba "Fale com a gente": sugestões, problemas e outros assuntos.

As mensagens vão para um formulário do Google (Google Forms) e chegam numa
planilha, com aviso por e-mail. Quem usa não precisa de conta em lugar nenhum:
o Puxaí envia as respostas do formulário direto, como se a pessoa tivesse
preenchido o formulário no navegador.

Desligado até haver o FORMULARIO e os CAMPOS: sem eles, a aba nem aparece.
Para configurar: no formulário, "Gerar link pré-preenchido" com uma resposta
qualquer em cada pergunta; o link mostra o código de cada uma (entry.123...).
"""
import os
import urllib.parse
import urllib.request

from servicos import autoatualizacao

# Link do formulário (o de responder: https://docs.google.com/forms/d/e/<código>/viewform)
FORMULARIO = "https://docs.google.com/forms/d/e/1FAIpQLSd9vCokxEqS_D97aJsQ_m0lFDnhNjPNhO_yRd0CfvgCL_o0mw/viewform"
# O código de cada pergunta do formulário, na ordem: Tipo, Mensagem, Contato, Relatório técnico, Versão
CAMPOS = {"tipo": "entry.1867407806", "mensagem": "entry.938646911", "contato": "entry.1071330111",
          "relatorio": "entry.774995304", "versao": "entry.1866659627"}

TIPOS = {"sugestao": "Sugestão", "problema": "Problema", "outro": "Outro assunto"}
LIMITES = {"mensagem": 5000, "contato": 200, "relatorio": 20000}


class EnvioRecusado(Exception):
    """O Google não aceitou a resposta (ex.: o formulário passou a exigir login)."""


def disponivel():
    """Há um formulário para onde enviar? (Sem ele, o painel nem mostra a aba.)"""
    return bool(FORMULARIO) and all(CAMPOS.values())


def _endereco():
    # PUXAI_URL_FORMULARIO troca o endereço, para testar sem enviar de verdade
    if os.environ.get("PUXAI_URL_FORMULARIO"):
        return os.environ["PUXAI_URL_FORMULARIO"]
    base = FORMULARIO.split("?", 1)[0]
    return base.rsplit("/", 1)[0] + "/formResponse"  # .../viewform -> .../formResponse


def enviar(tipo, mensagem, contato="", relatorio=""):
    """Envia a mensagem para o formulário. Erro de rede ou recusa viram exceção."""
    respostas = {
        CAMPOS["tipo"]: TIPOS[tipo],
        CAMPOS["mensagem"]: mensagem[:LIMITES["mensagem"]],
        CAMPOS["contato"]: contato[:LIMITES["contato"]],
        CAMPOS["relatorio"]: relatorio[:LIMITES["relatorio"]],
        CAMPOS["versao"]: autoatualizacao.versao_instalada(),
    }
    pedido = urllib.request.Request(
        _endereco(), data=urllib.parse.urlencode(respostas).encode(), method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0 (Puxai)"},
    )
    with urllib.request.urlopen(pedido, timeout=20) as resposta:
        # Formulário que passou a exigir login manda para a página de entrar do Google
        if "accounts.google.com" in resposta.geturl():
            raise EnvioRecusado("o formulário está pedindo login (desligue 'Coletar e-mails' e 'Limitar a 1 resposta')")
