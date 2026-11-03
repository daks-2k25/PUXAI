"""O programa em si: janela ou navegador, preferências e encerrar."""
import threading

from flask import Blueprint, jsonify, request

from servicos import destinos, estatisticas, preferencias, programa, sistema
from servicos.janela import barra_de_titulo_escura, trazer_para_frente

rotas = Blueprint("programa", __name__)


@rotas.route('/api/modo', methods=['GET'])
def modo_api():
    # O painel esconde o botão "Encerrar" quando está na janela própria
    return jsonify({
        "janela": programa.na_janela(),
        "preferencia": preferencias.modo_de_abertura(),
    })


@rotas.route('/api/ping', methods=['POST'])
def ping_api():
    # No modo navegador, o painel avisa a cada 30 segundos que continua aberto
    programa.painel_deu_sinal()
    return jsonify({"ok": True})


@rotas.route('/api/encerrar', methods=['POST'])
def encerrar_api():
    # Responde primeiro e fecha logo depois, para o painel receber a resposta
    programa.encerrar_em_instantes()
    return jsonify({"mensagem": "Programa encerrado."})


@rotas.route('/api/focar', methods=['POST'])
def focar_api():
    # Clicou no atalho com o programa já aberto: traz a janela para a frente
    if programa.janela is not None:
        trazer_para_frente()
    else:
        sistema.abrir_no_navegador(programa.ENDERECO_PAINEL)
    return jsonify({"ok": True})


def dados_das_preferencias():
    return {
        "modo_abertura": preferencias.modo_de_abertura(),
        "tema": preferencias.tema(),               # o escolhido: automatico, claro ou escuro
        "tema_em_uso": preferencias.tema_em_uso(),  # claro ou escuro (automático = o do sistema)
        "detectar_link": preferencias.detectar_link(),  # avisar quando copiar um link de vídeo
        # Estatísticas anônimas: só aparecem se houver para onde enviar; null = ainda não respondeu
        "estatisticas_disponivel": estatisticas.disponivel(),
        "estatisticas": estatisticas.permissao(),
    }


@rotas.route('/api/preferencias', methods=['GET'])
def preferencias_api():
    return jsonify(dados_das_preferencias())


@rotas.route('/api/preferencias', methods=['POST'])
def salvar_preferencias_api():
    # Configurações do painel: abrir na janela ou no navegador, e o tema (claro, escuro, automático)
    dados = request.get_json(silent=True) or {}
    if not {"modo_abertura", "tema", "detectar_link", "estatisticas"} & dados.keys():
        return jsonify({"erro": "Envie modo_abertura, tema, detectar_link e/ou estatisticas."}), 400
    if "estatisticas" in dados:
        if not isinstance(dados["estatisticas"], bool):
            return jsonify({"erro": "estatisticas deve ser true ou false."}), 400
        preferencias.salvar("estatisticas", dados["estatisticas"])
    if "detectar_link" in dados:
        if not isinstance(dados["detectar_link"], bool):
            return jsonify({"erro": "detectar_link deve ser true ou false."}), 400
        preferencias.salvar("detectar_link", dados["detectar_link"])
    if "modo_abertura" in dados:
        if dados["modo_abertura"] not in preferencias.MODOS_DE_ABERTURA:
            return jsonify({"erro": "Use 'janela' ou 'navegador'."}), 400
        preferencias.salvar("modo_abertura", dados["modo_abertura"])
    if "tema" in dados:
        if dados["tema"] not in preferencias.TEMAS:
            return jsonify({"erro": "Tema inválido. Use 'automatico', 'claro' ou 'escuro'."}), 400
        preferencias.salvar("tema", dados["tema"])
        if programa.na_janela():
            # A barra de título da janela acompanha o tema na hora
            barra_de_titulo_escura(preferencias.tema_em_uso() == "escuro")
    return jsonify(dados_das_preferencias())


@rotas.route('/api/pastas', methods=['GET'])
def pastas_api():
    # Onde os arquivos prontos são salvos (Configurações > Salvar arquivos em)
    return jsonify(destinos.configuracao())


@rotas.route('/api/pastas', methods=['POST'])
def salvar_pastas_api():
    # {"modo": "uma"|"separadas", "tudo"|"video"|"musica"|"foto": caminho ("" = Downloads)}
    try:
        return jsonify(destinos.salvar(request.get_json(silent=True) or {}))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400


@rotas.route('/api/pastas/escolher', methods=['POST'])
def escolher_pasta_api():
    # Abre a janela do Windows para escolher uma pasta (só devolve o caminho; quem salva é o POST /api/pastas)
    atual = (request.get_json(silent=True) or {}).get("atual")
    try:
        return jsonify({"pasta": destinos.escolher_pasta(atual)})
    except Exception as e:
        print(f"[PASTAS] Não foi possível abrir a janela de escolher pasta: {e}")
        return jsonify({"erro": "Não foi possível abrir a janela de escolher pasta."}), 500


@rotas.route('/api/abrir-no-navegador', methods=['POST'])
def abrir_no_navegador_api():
    # Abre o painel no navegador agora e fecha a janela; o programa continua rodando
    if programa.janela is not None:
        programa.trocando_para_navegador = True
        threading.Timer(0.3, programa.janela.destroy).start()
    sistema.abrir_no_navegador(programa.ENDERECO_PAINEL)
    return jsonify({"ok": True})


@rotas.route('/api/reabrir-como-aplicativo', methods=['POST'])
def reabrir_como_aplicativo_api():
    # No navegador: reinicia o programa já na janela do aplicativo
    if programa.na_janela():
        return jsonify({"erro": "O programa já está aberto como aplicativo."}), 409
    programa.reiniciar("janela")
    programa.encerrar_em_instantes()
    return jsonify({"ok": True})
