"""A extensão do navegador ("Baixar com o Puxaí", pasta extensao/).

São as únicas rotas que a extensão pode usar (veja seguranca.py): ver se o
programa está aberto, pôr um link na fila e trazer o Puxaí para a frente.
"""
import uuid

from flask import Blueprint, jsonify, request

from rotas.seguranca import ORIGENS_DE_EXTENSAO, ROTAS_DA_EXTENSAO
from rotas.videos import QUALIDADE_PADRAO, QUALIDADES_PERMITIDAS
from servicos import area_de_transferencia, autoatualizacao, programa, sistema
from servicos.downloader import adicionar_fila
from servicos.janela import trazer_para_frente
from servicos.sites import e_playlist_sem_video

rotas = Blueprint("extensao", __name__)


@rotas.after_app_request
def permitir_a_extensao(resposta):
    # CORS só para a extensão e só nestas rotas (o Firefox pode pedir, conforme a permissão dada)
    origem = request.headers.get("Origin") or ""
    if origem.startswith(ORIGENS_DE_EXTENSAO) and request.path.startswith(ROTAS_DA_EXTENSAO):
        resposta.headers["Access-Control-Allow-Origin"] = origem
        resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resposta.headers["Access-Control-Allow-Methods"] = "GET, POST"
        resposta.headers["Vary"] = "Origin"
    return resposta


@rotas.route('/api/extensao/estado', methods=['GET'])
def estado_api():
    # A extensão pergunta se o Puxaí está aberto (e quais qualidades mostrar)
    return jsonify({
        "puxai": True,
        "versao": autoatualizacao.versao_instalada(),
        "qualidades": [f"{q}p" for q in QUALIDADES_PERMITIDAS],
        "padrao": f"{QUALIDADE_PADRAO}p",
    })


@rotas.route('/api/extensao/enviar', methods=['POST'])
def enviar_api():
    # {"url", "formato": "mp4"|"mp3", "qualidade": "720p", "titulo": "título da aba"}
    dados = request.get_json(silent=True) or {}
    url = str(dados.get("url") or "").strip()
    formato = dados.get("formato", "mp4")
    if formato not in ("mp4", "mp3"):
        return jsonify({"erro": "Formato inválido."}), 400
    try:
        qualidade = int(str(dados.get("qualidade", QUALIDADE_PADRAO)).lower().rstrip("p"))
    except ValueError:
        qualidade = None
    if qualidade not in QUALIDADES_PERMITIDAS:
        qualidade = QUALIDADE_PADRAO

    # Só links que o Puxaí sabe baixar (o mesmo teste do aviso de link copiado)
    link = area_de_transferencia.link_de_video(url)
    if not link:
        return jsonify({"erro": "O Puxaí não sabe baixar desta página."}), 400
    if e_playlist_sem_video(link["url"]):
        return jsonify({"erro": "É o link de uma playlist: cole ele no Puxaí para escolher os vídeos."}), 400

    id_download = str(uuid.uuid4())
    titulo = str(dados.get("titulo") or "")[:300] or None
    adicionar_fila(link["url"], formato, qualidade, id_download, titulo=titulo, origem="extensao")
    print(f"[EXTENSÃO] {link['site']}: {link['url']} ({formato})")
    return jsonify({"id": id_download, "site": link["site"], "formato": formato,
                    "qualidade": f"{qualidade}p" if formato == "mp4" else None}), 202


@rotas.route('/api/extensao/abrir', methods=['POST'])
def abrir_api():
    # Botão "Abrir o Puxaí" da extensão: traz a janela para a frente (ou abre o painel)
    if programa.janela is not None:
        trazer_para_frente()
    else:
        sistema.abrir_no_navegador(programa.ENDERECO_PAINEL)
    return jsonify({"ok": True})
