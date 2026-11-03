"""Endereços da API (/api/...) usados pelo painel, um arquivo por área:

- videos.py       baixar vídeos e músicas (YouTube, TikTok, Instagram e mais de mil sites)
- fotos.py        converter e comprimir fotos
- comprimir_video.py  comprimir vídeos do computador
- arquivos.py     mostrar na pasta, abrir e "Meus downloads"
- programa.py     janela ou navegador, preferências, encerrar
- atualizacao.py  versão nova e botão "Atualizar agora"
- extensao.py     a extensão do navegador ("Baixar com o Puxaí")
- relatorio.py    relatório de erro ("Relatar problema")
"""
import os

from flask import Flask, Response

from servicos import preferencias
from servicos.caminhos import PASTA_PAINEL
from rotas import arquivos, atualizacao, comprimir_video, extensao, fotos, programa, relatorio, videos
from rotas.seguranca import proteger


def criar_app():
    # O painel web (pasta painel/) é servido pela própria API em http://localhost:5000
    app = Flask(__name__, static_folder=PASTA_PAINEL, static_url_path="")
    proteger(app)  # só o painel pode usar a API (veja rotas/seguranca.py)

    @app.route('/')
    def painel():
        # A página já sai com o tema certo (claro/escuro): sem "piscar" o tema errado ao abrir
        with open(os.path.join(PASTA_PAINEL, "index.html"), encoding="utf-8") as arquivo:
            html = arquivo.read()
        html = html.replace('<html lang="pt-BR">', (
            f'<html lang="pt-BR" data-tema="{preferencias.tema_em_uso()}" '
            f'data-tema-escolhido="{preferencias.tema()}">'
        ), 1)
        return Response(html, mimetype="text/html")

    for modulo in (videos, fotos, comprimir_video, arquivos, programa, atualizacao, extensao, relatorio):
        app.register_blueprint(modulo.rotas)
    return app
