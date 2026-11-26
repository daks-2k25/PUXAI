"""Histórico dos arquivos salvos pelo programa (aba "Meus downloads").

Fica em .historico.json ao lado do programa, fora do Git; o botão de
atualizar não mexe nele. Guarda só o que o programa salvou, não a pasta
Downloads inteira.
"""
import json
import os
import threading
import time

from servicos.caminhos import PASTA_BASE

ARQUIVO = os.path.join(PASTA_BASE, ".historico.json")
_trava = threading.Lock()

# Os mais antigos saem da lista (o arquivo continua na pasta Downloads)
LIMITE = 300

# Extensão -> tipo mostrado no painel (filtros Vídeos / Músicas / Fotos / Documentos)
TIPOS = {"mp4": "video", "mp3": "musica", "jpg": "foto", "png": "foto", "webp": "foto", "pdf": "documento"}


def _ler():
    try:
        with open(ARQUIVO, encoding="utf-8") as f:
            itens = json.load(f)
        return itens if isinstance(itens, list) else []
    except (OSError, ValueError):
        return []


def _gravar(itens):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False, indent=2)


def registrar(id_arquivo, caminho, titulo=None, origem=None):
    """Anota um arquivo que acabou de ser salvo. origem: link do vídeo (se houver)."""
    extensao = caminho.rsplit(".", 1)[-1].lower()
    item = {
        "id": id_arquivo,
        "caminho": caminho,
        "titulo": titulo or os.path.splitext(os.path.basename(caminho))[0],
        "tipo": TIPOS.get(extensao, "outro"),
        "formato": extensao.upper(),
        "origem": origem,
        "data": time.time(),
    }
    try:
        with _trava:
            itens = [i for i in _ler() if i.get("id") != id_arquivo]
            itens.insert(0, item)
            _gravar(itens[:LIMITE])
    except OSError as e:
        # Sem histórico o download continua valendo; só não aparece na aba
        print(f"[HISTÓRICO] Não foi possível salvar: {e}")


def listar():
    """Itens do mais novo para o mais antigo, dizendo se o arquivo ainda existe."""
    resultado = []
    for item in _ler():
        caminho = item.get("caminho", "")
        existe = os.path.isfile(caminho)
        resultado.append({
            **item,
            "arquivo": os.path.basename(caminho),
            "existe": existe,
            "tamanho": os.path.getsize(caminho) if existe else None,
        })
    return resultado


def caminho(id_arquivo):
    for item in _ler():
        if item.get("id") == id_arquivo:
            return item.get("caminho")
    return None


def remover(id_arquivo):
    """Tira da lista (não apaga o arquivo). Devolve False se não estava lá."""
    with _trava:
        itens = _ler()
        restantes = [i for i in itens if i.get("id") != id_arquivo]
        if len(restantes) == len(itens):
            return False
        _gravar(restantes)
        return True


def limpar():
    """Esvazia a lista (os arquivos continuam na pasta Downloads)."""
    with _trava:
        _gravar([])
