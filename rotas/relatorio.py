"""Relatório de erro: montar (para a pessoa conferir) e abrir o GitHub ou o e-mail já preenchido."""
from flask import Blueprint, jsonify, request

from servicos import relatorio, sistema

rotas = Blueprint("relatorio", __name__)


@rotas.route('/api/relatorio', methods=['POST'])
def montar_relatorio_api():
    # {"id": "<download que deu erro>"} (opcional) -> o texto, para mostrar antes de enviar
    id_download = (request.get_json(silent=True) or {}).get("id")
    dados = relatorio.montar(str(id_download) if id_download else None)
    dados["email"] = bool(relatorio.EMAIL_SUPORTE)  # o painel só mostra "Enviar por e-mail" se houver
    return jsonify(dados)


@rotas.route('/api/relatorio/enviar', methods=['POST'])
def enviar_relatorio_api():
    # {"destino": "github"|"email", "titulo", "descricao", "texto"}: o texto é o que a pessoa conferiu
    dados = request.get_json(silent=True) or {}
    titulo = str(dados.get("titulo") or "Problema no Puxaí")[:150]
    descricao = str(dados.get("descricao") or "")[:3000]
    texto = str(dados.get("texto") or "")[:20000]
    if dados.get("destino") == "github":
        endereco = relatorio.endereco_github(titulo, descricao, texto)
        sistema.abrir_no_navegador(endereco)
    elif dados.get("destino") == "email" and relatorio.EMAIL_SUPORTE:
        endereco = relatorio.endereco_email(titulo, descricao, texto)
        sistema.abrir(endereco)  # o programa de e-mail do computador
    else:
        return jsonify({"erro": "Destino inválido."}), 400
    return jsonify({"ok": True})
