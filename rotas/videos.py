"""Baixar vídeos e músicas (YouTube, TikTok, Instagram e os outros sites que o yt-dlp conhece)."""
import os
import re
import uuid

from flask import Blueprint, jsonify, request, send_file

from servicos import area_de_transferencia, compressor_video, preferencias
from servicos.downloader import (
    adicionar_fila, arquivos_salvos, cancelar_download, erros_download, extras_download, fila_atual,
    nome_de_arquivo_seguro, status_download, titulos_download,
)
from rotas.utilidades import pasta_do_arquivo
from servicos.informacoes import obter_informacoes, obter_playlist
from servicos.sites import e_playlist_sem_video, mensagem_de_erro

rotas = Blueprint("videos", __name__)

# Resoluções permitidas para MP4 (máximo 1080p para não pesar no servidor)
QUALIDADES_PERMITIDAS = [360, 480, 720, 1080]
QUALIDADE_PADRAO = 720

# O ID vira nome de arquivo: só letras, números, "-" e "_" (evita acessar outras pastas)
PADRAO_ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')


def ler_tempo(valor):
    """Converte "1:20", "1:02:05" ou 80 em segundos. Vazio -> None."""
    if valor is None or str(valor).strip() == "":
        return None
    partes = str(valor).strip().split(":")
    if len(partes) > 3:
        raise ValueError("tempo inválido")
    segundos = 0.0
    for parte in partes:
        numero = float(parte)
        if numero < 0:
            raise ValueError("tempo negativo")
        segundos = segundos * 60 + numero
    return segundos


@rotas.route('/api/download', methods=['POST'])
def download_api():
    dados = request.get_json()

    if not dados or 'url' not in dados:
        return jsonify({"erro": "A URL do video e obrigatoria."}), 400

    url = dados['url']
    formato = dados.get('formato', 'mp4')
    id_download = str(dados.get('id', uuid.uuid4()))

    if formato not in ('mp4', 'mp3'):
        return jsonify({"erro": "Formato inválido. Use 'mp4' ou 'mp3'."}), 400

    if e_playlist_sem_video(url):
        return jsonify({"erro": "Este link é de uma playlist. Playlists não são permitidas: envie o link de um vídeo só."}), 400

    if not PADRAO_ID.match(id_download):
        return jsonify({"erro": "ID inválido. Use só letras, números, '-' e '_' (até 64 caracteres)."}), 400

    try:
        qualidade = int(str(dados.get('qualidade', QUALIDADE_PADRAO)).lower().rstrip('p'))
    except ValueError:
        qualidade = None

    if qualidade not in QUALIDADES_PERMITIDAS:
        return jsonify({
            "erro": f"Qualidade inválida. Opções: {', '.join(f'{q}p' for q in QUALIDADES_PERMITIDAS)}."
        }), 400

    # Trecho opcional: "inicio" e "fim" como "1:20" (ou segundos)
    try:
        inicio = ler_tempo(dados.get('inicio'))
        fim = ler_tempo(dados.get('fim'))
    except ValueError:
        return jsonify({"erro": "Tempo do trecho inválido. Use o formato 1:20 (minutos:segundos)."}), 400

    trecho = None
    if inicio is not None or fim is not None:
        inicio = inicio or 0
        fim = fim if fim is not None else float("inf")  # sem fim: até o final do vídeo
        if fim <= inicio:
            return jsonify({"erro": "O fim do trecho precisa ser depois do início."}), 400
        trecho = (inicio, fim)

    # Playlist (opcional): subpasta com o nome dela e o número do vídeo na frente do nome
    pasta = dados.get('pasta')
    if pasta:
        # Sem caracteres proibidos nem "." no começo/fim: a pasta fica sempre dentro de Downloads
        pasta = nome_de_arquivo_seguro(pasta)[:100].strip(" .") or None
    numero = None
    try:
        if dados.get('numero') is not None:
            total = max(int(dados.get('total') or 0), int(dados['numero']))
            numero = str(int(dados['numero'])).zfill(max(2, len(str(total))))  # 3 de 40 -> "03"
    except (TypeError, ValueError):
        return jsonify({"erro": "Número do vídeo na playlist inválido."}), 400

    # Título da prévia (opcional): o painel mostra se a fila voltar depois de fechar o programa
    titulo = str(dados.get('titulo') or '')[:300] or None
    adicionar_fila(url, formato, qualidade, id_download, trecho, pasta, numero, titulo)

    return jsonify({
        "mensagem": "Vídeo enfileirado com sucesso!",
        "id": id_download,
        "formato": formato,
        "qualidade": f"{qualidade}p" if formato == "mp4" else None,
        "trecho": {"inicio": trecho[0], "fim": None if trecho[1] == float("inf") else trecho[1]} if trecho else None,
        "status": "Na fila..."
    }), 202


@rotas.route('/api/info', methods=['GET'])
def info_api():
    # Prévia do vídeo (título, canal, duração, miniatura) antes de baixar
    url = request.args.get('url', '').strip()

    if not url:
        return jsonify({"erro": "Informe a URL do vídeo."}), 400

    if e_playlist_sem_video(url):
        return jsonify({"erro": "Este link é de uma playlist."}), 400

    try:
        return jsonify(obter_informacoes(url))
    except Exception as e:
        print(f"[INFO] Não foi possível obter a prévia de {url}: {e}")
        return jsonify({"erro": mensagem_de_erro(e)}), 404


@rotas.route('/api/link-copiado', methods=['GET'])
def link_copiado_api():
    # O painel pergunta ao abrir e ao voltar para ele: se houver um link de vídeo
    # copiado, oferece "Colar". Qualquer outro texto copiado não sai daqui.
    if not preferencias.detectar_link():
        return jsonify({"url": None, "site": None})
    return jsonify(area_de_transferencia.link_copiado() or {"url": None, "site": None})


@rotas.route('/api/playlist', methods=['GET'])
def playlist_api():
    # Lista os vídeos de uma playlist (ou canal) para o painel marcar quais baixar
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({"erro": "Informe a URL da playlist."}), 400

    try:
        return jsonify(obter_playlist(url))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print(f"[PLAYLIST] Não foi possível listar {url}: {e}")
        return jsonify({"erro": mensagem_de_erro(e)}), 404


@rotas.route('/api/qualidades', methods=['GET'])
def qualidades_api():
    # Para o frontend montar a lista de opções
    return jsonify({
        "qualidades": [f"{q}p" for q in QUALIDADES_PERMITIDAS],
        "padrao": f"{QUALIDADE_PADRAO}p"
    })


def progresso(id_download):
    status = status_download.get(id_download, "Desconhecido")
    caminho = arquivos_salvos.get(id_download)
    return {
        "id": id_download,
        "status": status,
        "titulo": titulos_download.get(id_download),
        "arquivo": os.path.basename(caminho) if caminho else None,  # nome do arquivo salvo
        "pasta": pasta_do_arquivo(caminho),  # nome da pasta onde ficou ("Downloads", "Músicas"...)
        "erro": erros_download.get(id_download) if status == "Erro" else None,  # motivo da falha
        # Compressão de vídeo: tamanho antes/depois, resolução final, "ja_otimizada"
        "extra": extras_download.get(id_download),
    }


@rotas.route('/api/fila', methods=['GET'])
def fila_api():
    # Downloads que ainda não terminaram (inclusive os que voltaram de quando o programa fechou)
    return jsonify(fila_atual())


@rotas.route('/api/progresso/<id_download>', methods=['GET'])
def progresso_api(id_download):
    return jsonify(progresso(id_download))


@rotas.route('/api/progresso', methods=['POST'])
def progresso_lote_api():
    # O painel pergunta de todos os downloads de uma vez (playlists têm até 200)
    ids = (request.get_json(silent=True) or {}).get("ids")
    if not isinstance(ids, list):
        return jsonify({"erro": "Envie {\"ids\": [...]}."}), 400
    return jsonify({str(i): progresso(str(i)) for i in ids[:500]})


@rotas.route('/api/cancelar/<id_download>', methods=['POST'])
def cancelar_api(id_download):
    # Vale para downloads e para compressões de vídeo (que usam a mesma lista de status)
    if not compressor_video.cancelar(id_download) and not cancelar_download(id_download):
        return jsonify({"erro": "Esse download não existe ou já terminou."}), 404
    return jsonify({"mensagem": "Cancelando...", "id": id_download})


@rotas.route('/api/arquivo/<id_download>', methods=['GET'])
def baixar_arquivo_api(id_download):
    # O arquivo já fica salvo na pasta Downloads; esta rota é para quem usa a API
    # de outro programa e quer receber o arquivo pela resposta HTTP
    caminho = arquivos_salvos.get(id_download)
    if not caminho or not os.path.exists(caminho):
        return jsonify({"erro": "Arquivo ainda não está pronto ou não foi encontrado."}), 404
    return send_file(caminho, as_attachment=True, download_name=os.path.basename(caminho))
