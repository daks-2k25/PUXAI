"""Documentos (aba "Documentos"): comprimir PDF, fotos -> PDF e PDF -> imagens.

Recebem os arquivos como multipart/form-data e salvam o resultado na pasta de
fotos escolhida em Configurações (Downloads, se nenhuma). Respondem um JSON.
"""
import os
import shutil
import uuid

from flask import Blueprint, jsonify, request

from rotas.utilidades import apagar, extensao_do_arquivo, guardar_enviado, nome_sem_extensao, pasta_do_arquivo, \
    salvar_no_destino
from servicos import destinos, documentos, historico
from servicos.caminhos import PASTA_DOWNLOADS
from servicos.downloader import arquivos_salvos, nome_de_arquivo_seguro

rotas = Blueprint("documentos", __name__)

PROTEGIDO = {"erro": "Este PDF tem senha para abrir. Tire a senha (no programa que criou o PDF) e tente de novo."}
MAXIMO_DE_FOTOS = 200


def pdf_enviado():
    """O PDF do form-data, ou (None, resposta de erro)."""
    arquivo = request.files.get('arquivo')
    if arquivo is None or arquivo.filename == '':
        return None, (jsonify({"erro": "Nenhum arquivo enviado. Use o campo 'arquivo' no form-data."}), 400)
    if extensao_do_arquivo(arquivo.filename) != "pdf":
        return None, (jsonify({"erro": "Envie um arquivo PDF."}), 400)
    return arquivo, None


@rotas.route('/api/documentos/comprimir', methods=['POST'])
def comprimir_pdf_api():
    arquivo, erro = pdf_enviado()
    if erro:
        return erro
    nivel = request.form.get('nivel', documentos.NIVEL_PADRAO_PDF)
    if nivel not in documentos.NIVEIS_PDF:
        return jsonify({"erro": "Nível inválido. Use 'alta', 'equilibrado' ou 'forte'."}), 400

    id_arquivo = str(uuid.uuid4())
    original = guardar_enviado(arquivo, id_arquivo, "pdf")
    saida = os.path.join(PASTA_DOWNLOADS, f"{id_arquivo}_tentativa.pdf")
    try:
        resultado = documentos.comprimir_pdf(original, saida, nivel)
    except documentos.PdfProtegido:
        apagar(saida)
        return jsonify(PROTEGIDO), 400
    except Exception as e:
        print(f"[DOCUMENTOS] Erro ao comprimir {arquivo.filename}: {e}")
        apagar(saida)
        return jsonify({"erro": "Não foi possível comprimir. Verifique se o arquivo é um PDF válido."}), 500
    finally:
        apagar(original)

    dados = {"id": id_arquivo, **resultado, "arquivo": None}
    if not resultado["ja_otimizado"]:
        destino = salvar_no_destino(saida, f"{nome_sem_extensao(arquivo.filename)} (comprimido)", "pdf", id_arquivo)
        dados.update(arquivo=os.path.basename(destino), pasta=pasta_do_arquivo(destino))
    return jsonify(dados)


@rotas.route('/api/documentos/fotos-para-pdf', methods=['POST'])
def fotos_para_pdf_api():
    # Campo "arquivos" repetido, na ordem das páginas; "tamanho": "a4" ou "foto"; "nome" (opcional)
    fotos = [f for f in request.files.getlist('arquivos') if f.filename]
    if not fotos:
        return jsonify({"erro": "Nenhuma foto enviada. Use o campo 'arquivos' no form-data."}), 400
    if len(fotos) > MAXIMO_DE_FOTOS:
        return jsonify({"erro": f"São {len(fotos)} fotos: envie até {MAXIMO_DE_FOTOS} de uma vez."}), 400
    for foto in fotos:
        if extensao_do_arquivo(foto.filename) not in documentos.EXTENSOES_DE_FOTO:
            return jsonify({"erro": f"\"{foto.filename}\" não é uma foto JPG, PNG, WebP ou HEIC."}), 400
    tamanho = request.form.get('tamanho', 'a4')
    if tamanho not in documentos.TAMANHOS_DE_PAGINA:
        return jsonify({"erro": "Tamanho inválido. Use 'a4' ou 'foto'."}), 400

    id_arquivo = str(uuid.uuid4())
    originais = [guardar_enviado(foto, f"{id_arquivo}_{numero}", extensao_do_arquivo(foto.filename))
                 for numero, foto in enumerate(fotos)]
    saida = os.path.join(PASTA_DOWNLOADS, f"{id_arquivo}_tentativa.pdf")
    try:
        paginas = documentos.fotos_para_pdf(originais, saida, tamanho)
    except Exception as e:
        print(f"[DOCUMENTOS] Erro ao montar o PDF: {e}")
        apagar(saida)
        return jsonify({"erro": "Não foi possível montar o PDF. Verifique se os arquivos são fotos válidas."}), 500
    finally:
        apagar(*originais)

    nome = (request.form.get('nome') or "").strip()[:100] or nome_sem_extensao(fotos[0].filename)
    tamanho_final = os.path.getsize(saida)
    destino = salvar_no_destino(saida, nome, "pdf", id_arquivo)
    return jsonify({"id": id_arquivo, "paginas": paginas, "tamanho": tamanho_final,
                    "arquivo": os.path.basename(destino), "pasta": pasta_do_arquivo(destino)})


@rotas.route('/api/documentos/pdf-para-imagens', methods=['POST'])
def pdf_para_imagens_api():
    # "formato": "jpg"|"png"; "qualidade": "tela"|"impressao"; "paginas": "1-3, 5" (vazio = todas)
    arquivo, erro = pdf_enviado()
    if erro:
        return erro
    formato = request.form.get('formato', 'jpg')
    qualidade = request.form.get('qualidade', 'tela')
    if formato not in documentos.FORMATOS_DE_IMAGEM or qualidade not in documentos.QUALIDADES_DE_IMAGEM:
        return jsonify({"erro": "Formato ou qualidade inválida."}), 400

    id_arquivo = str(uuid.uuid4())
    original = guardar_enviado(arquivo, id_arquivo, "pdf")
    nome = nome_sem_extensao(arquivo.filename)
    # Uma pasta para as páginas, dentro da pasta de fotos: "Contrato (páginas)", "Contrato (páginas) (2)"...
    base = os.path.join(destinos.pasta_para("foto"), nome_de_arquivo_seguro(f"{nome} (páginas)"))
    pasta, numero = base, 2
    while os.path.exists(pasta):
        pasta, numero = f"{base} ({numero})", numero + 1
    try:
        criadas = documentos.pdf_para_imagens(original, pasta, formato, documentos.QUALIDADES_DE_IMAGEM[qualidade],
                                              request.form.get('paginas'))
    except documentos.PdfProtegido:
        shutil.rmtree(pasta, ignore_errors=True)
        return jsonify(PROTEGIDO), 400
    except ValueError as e:  # páginas que não existem ("20" num PDF de 14)
        shutil.rmtree(pasta, ignore_errors=True)
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print(f"[DOCUMENTOS] Erro ao transformar {arquivo.filename} em imagens: {e}")
        shutil.rmtree(pasta, ignore_errors=True)
        return jsonify({"erro": "Não foi possível abrir o PDF. Verifique se o arquivo é um PDF válido."}), 500
    finally:
        apagar(original)

    # "Mostrar na pasta" e "Meus downloads" apontam para a primeira imagem (a pasta abre com ela selecionada)
    arquivos_salvos[id_arquivo] = criadas[0]
    historico.registrar(id_arquivo, criadas[0], f"{nome} ({len(criadas)} {'página' if len(criadas) == 1 else 'páginas'})")
    return jsonify({"id": id_arquivo, "quantidade": len(criadas), "arquivo": os.path.basename(criadas[0]),
                    "pasta": os.path.basename(pasta)})
