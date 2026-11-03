"""Só o painel do programa pode usar a API.

Sem isso, qualquer site aberto no navegador conseguiria mandar pedidos para
http://127.0.0.1:5000 enquanto o programa está aberto (baixar, encerrar,
atualizar...). Cada pedido passa por três conferências antes de chegar às rotas:

1. Endereço (Host): só 127.0.0.1 ou localhost. Barra o "DNS rebinding", em
   que um site se passa pelo próprio computador para falar com o programa.
2. Quem mandou (Sec-Fetch-Site): o navegador sempre informa se o pedido veio
   da própria página ("same-origin"), de um link digitado ("none") ou de outro
   site. Outro site, ou outro programa em outra porta, é recusado.
3. Origem (Origin): se vier, tem que ser exatamente o endereço do painel.

Exceção: a extensão do navegador (pasta extensao/) pode usar só as rotas
/api/extensao/... (pôr um link na fila e ver se o programa está aberto). Um
site não consegue se passar por extensão: o navegador não deixa uma página
mandar Origin "chrome-extension://..." ou "moz-extension://...".

Programas fora do navegador (curl, scripts) não mandam Sec-Fetch-Site nem
Origin, então continuam podendo usar a API.
"""
from flask import jsonify, request

from servicos import programa

ENDERECOS_LOCAIS = ("127.0.0.1", "localhost")
ORIGENS_DO_PAINEL = {f"http://{endereco}:{programa.PORTA}" for endereco in ENDERECOS_LOCAIS}
ORIGENS_DE_EXTENSAO = ("chrome-extension://", "moz-extension://")
ROTAS_DA_EXTENSAO = "/api/extensao/"


def pedido_permitido():
    endereco = request.host.rsplit(":", 1)[0] if ":" in request.host else request.host
    if endereco not in ENDERECOS_LOCAIS:
        return False
    origem = request.headers.get("Origin")
    if origem and origem.startswith(ORIGENS_DE_EXTENSAO):
        return request.path.startswith(ROTAS_DA_EXTENSAO)
    if request.headers.get("Sec-Fetch-Site") in ("cross-site", "same-site"):
        return False
    return origem is None or origem in ORIGENS_DO_PAINEL


def proteger(app):
    @app.before_request
    def so_o_painel():
        if not pedido_permitido():
            print(f"[SEGURANÇA] Pedido recusado: {request.method} {request.path} "
                  f"(host={request.host}, origem={request.headers.get('Origin')})")
            return jsonify({"erro": "Pedido recusado: só o painel do programa pode usar a API."}), 403
