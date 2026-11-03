"""Versão nova do programa: aviso, botão "Depois" e "Atualizar agora"."""
from flask import Blueprint, jsonify, request

from servicos import autoatualizacao, programa
from servicos.downloader import downloads_em_andamento

rotas = Blueprint("atualizacao", __name__)


@rotas.route('/api/versao', methods=['GET'])
def versao_api():
    # Versão instalada e, se houver, a versão nova disponível no GitHub
    dados = dict(autoatualizacao.verificar(forcar=request.args.get('forcar') == '1'))
    # "adiada": a pessoa clicou em "Depois" para esta versão; o painel não insiste
    dados["adiada"] = bool(dados["disponivel"] and dados["nova"] == autoatualizacao.versao_adiada())
    return jsonify(dados)


@rotas.route('/api/versao/adiar', methods=['POST'])
def adiar_versao_api():
    # Botão "Depois" da notificação: não avisar de novo sobre esta versão
    versao = (request.get_json(silent=True) or {}).get("versao")
    if not versao:
        return jsonify({"erro": "Informe a versão."}), 400
    autoatualizacao.adiar(versao)
    return jsonify({"ok": True})


@rotas.route('/api/atualizar', methods=['POST'])
def atualizar_api():
    if downloads_em_andamento():
        return jsonify({"erro": "Espere os downloads terminarem (ou cancele) antes de atualizar."}), 409
    try:
        versao = autoatualizacao.aplicar()
    except Exception as e:
        print(f"[ATUALIZAÇÃO] Falhou: {e}")
        return jsonify({"erro": f"Não foi possível atualizar: {e}"}), 500

    # Responde ao painel e reinicia já na versão nova
    autoatualizacao.reiniciar()
    programa.encerrar_em_instantes()
    return jsonify({"mensagem": "Atualizado! Reiniciando...", "versao": versao})


@rotas.route('/api/atualizar/andamento', methods=['GET'])
def andamento_da_atualizacao_api():
    # Programa gerado: quanto da versão nova já foi baixado ({"etapa": "baixando"|"extraindo"|null, "baixado", "total"})
    return jsonify(autoatualizacao.andamento())
