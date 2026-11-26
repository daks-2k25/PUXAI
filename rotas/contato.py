"""Aba "Fale com a gente": enviar sugestões, problemas e outros assuntos (para um Google Forms)."""
from flask import Blueprint, jsonify, request

from servicos import contato

rotas = Blueprint("contato", __name__)


@rotas.route('/api/contato', methods=['GET'])
def contato_api():
    # O painel só mostra a aba se houver um formulário configurado
    return jsonify({"disponivel": contato.disponivel(), "tipos": contato.TIPOS})


@rotas.route('/api/contato', methods=['POST'])
def enviar_contato_api():
    # {"tipo": "sugestao"|"problema"|"outro", "mensagem", "contato" (opcional), "relatorio" (opcional)}
    if not contato.disponivel():
        return jsonify({"erro": "O envio de mensagens não está configurado nesta versão."}), 404
    dados = request.get_json(silent=True) or {}
    tipo = dados.get("tipo")
    mensagem = str(dados.get("mensagem") or "").strip()
    if tipo not in contato.TIPOS:
        return jsonify({"erro": "Tipo inválido. Use 'sugestao', 'problema' ou 'outro'."}), 400
    if len(mensagem) < 3:
        return jsonify({"erro": "Escreva a sua mensagem antes de enviar."}), 400
    try:
        contato.enviar(tipo, mensagem, str(dados.get("contato") or "").strip(), str(dados.get("relatorio") or ""))
    except Exception as e:
        print(f"[CONTATO] Não foi possível enviar: {e}")
        return jsonify({"erro": "Não foi possível enviar agora. Confira a internet e tente de novo."}), 502
    return jsonify({"ok": True})
