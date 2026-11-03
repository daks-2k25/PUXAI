"""Relatório de erro com um clique (botão "Relatar problema" do painel).

Junta o que ajuda a descobrir o que deu errado: versões (Puxaí, yt-dlp, FFmpeg,
Deno), sistema, o erro do download e as últimas linhas de erro do Puxai.log.
Sai sem dados pessoais: o nome de usuário e as pastas viram "~", os links
ficam só com o site, e-mails e o código dos vídeos são tirados. A pessoa vê o
texto (e pode apagar o que quiser) antes de enviar pelo GitHub ou por e-mail.
"""
import getpass
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.parse

from servicos import autoatualizacao, programa
from servicos.caminhos import EXECUTAVEL, PASTA_BASE
from servicos.downloader import erros_download, pedidos_download, status_download

# Para onde vão os relatórios. EMAIL_SUPORTE vazio: o botão de e-mail não aparece.
URL_NOVO_ISSUE = f"https://github.com/{autoatualizacao.REPOSITORIO}/issues/new"
EMAIL_SUPORTE = ""

ARQUIVO_REGISTRO = os.path.join(PASTA_BASE, "Puxai.log")
# Linhas do Puxai.log que interessam (erros e avisos); o resto (o que foi baixado) fica de fora
LINHA_DE_ERRO = re.compile(r"ERRO|Erro|ERROR|WARNING|Traceback|Exception|[Ff]alhou|Não foi possível|indisponível|"
                           r"\[SEGURANÇA\]|\[JANELA\]|\[BANDEJA\]|\[ATUALIZAÇÃO\]|\[ATUALIZADOR\]")
LINHAS_DO_REGISTRO = 30

# Limites do tamanho do endereço: o GitHub corta perto de 8 mil caracteres; alguns
# programas de e-mail, perto de 2 mil
LIMITE_GITHUB = 7500
LIMITE_EMAIL = 1900


def limpar(texto):
    """Tira do texto o que identifica a pessoa (pastas, nome de usuário, links, e-mails)."""
    if not texto:
        return texto
    casa = os.path.expanduser("~")
    for variante in {casa, casa.replace("\\", "/"), casa.replace("\\", "\\\\")}:
        texto = re.sub(re.escape(variante), "~", texto, flags=re.IGNORECASE)
    try:
        usuario = getpass.getuser()
    except Exception:
        usuario = ""
    if len(usuario) >= 3:
        texto = re.sub(rf"(?<![\w]){re.escape(usuario)}(?![\w])", "<usuário>", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "<e-mail>", texto)
    # Links: só o site (o resto pode dizer o que a pessoa estava vendo)
    texto = re.sub(r"(https?://[^/\s\"'<>]+)[^\s\"'<>]*", r"\1/…", texto)
    # "[youtube] dQw4w9WgXcQ: ..." -> "[youtube] <vídeo>: ..."
    texto = re.sub(r"(\[[\w:-]+\]) [\w-]{6,}:", r"\1 <vídeo>:", texto)
    return texto


def _site(url):
    return urllib.parse.urlsplit(url or "").netloc.removeprefix("www.") or "?"


def _versao_de(comando, padrao):
    caminho = shutil.which(comando)
    if not caminho:
        return "não encontrado"
    try:
        saida = subprocess.run([caminho, "-version" if comando != "deno" else "--version"], capture_output=True,
                               text=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
        achado = re.search(padrao, saida)
        return achado.group(1) if achado else "?"
    except (OSError, subprocess.TimeoutExpired):
        return "?"


def _sistema():
    if sys.platform.startswith("linux"):
        nome = "Linux"
        try:
            with open("/etc/os-release", encoding="utf-8") as f:
                nome = next((linha.split("=", 1)[1].strip().strip('"') for linha in f if linha.startswith("PRETTY_NAME=")), nome)
        except OSError:
            pass
        area = os.environ.get("XDG_CURRENT_DESKTOP") or "?"
        sessao = os.environ.get("XDG_SESSION_TYPE") or "?"
        return f"{nome} ({platform.machine()}, {area}, {sessao})"
    return f"{platform.system()} {platform.release()} ({platform.version()}, {platform.machine()})"


def _linhas_do_registro():
    """As últimas linhas de erro do Puxai.log (com o "Traceback" inteiro, quando houver)."""
    try:
        with open(ARQUIVO_REGISTRO, encoding="utf-8", errors="replace") as f:
            linhas = f.read().splitlines()[-2000:]
    except OSError:
        return []
    escolhidas, no_traceback = [], False
    for linha in linhas:
        if linha.startswith("Traceback"):
            no_traceback = True
        elif no_traceback and not linha.startswith((" ", "\t")):
            no_traceback = False
            escolhidas.append(linha)  # a última linha do Traceback é a do erro
            continue
        if no_traceback or LINHA_DE_ERRO.search(linha):
            escolhidas.append(linha[:400])
    return [limpar(linha) for linha in escolhidas[-LINHAS_DO_REGISTRO:]]


def montar(id_download=None):
    """O relatório (texto em Markdown) e um título curto. id_download: o download que deu erro."""
    import yt_dlp

    ffmpeg = _versao_de("ffmpeg", r"ffmpeg version (\S+)")
    deno = _versao_de("deno", r"deno (\S+)")
    titulo = "Problema no Puxaí"
    partes = ["## Sobre o computador", "",
              f"- Puxaí: {autoatualizacao.versao_instalada()} ({'programa pronto' if EXECUTAVEL else 'pelo código'})",
              f"- Sistema: {limpar(_sistema())}",
              f"- Aberto em: {'janela do aplicativo' if programa.na_janela() else 'navegador'}",
              f"- Python: {platform.python_version()}",
              f"- yt-dlp: {yt_dlp.version.__version__}",
              f"- FFmpeg: {ffmpeg}",
              f"- Deno: {deno}"]

    if sys.platform.startswith("linux"):
        from servicos import janela
        teste = janela._resultado_do_teste_do_qt
        partes.append(f"- Janela/ícone (Qt): {'ok' if teste == '' else limpar(teste) if teste else 'não testado'}")

    pedido = pedidos_download.get(id_download or "")
    if pedido:
        site = _site(pedido["url"])
        tipo = "MP3" if pedido["formato"] == "mp3" else f"MP4 {pedido['qualidade']}p"
        titulo = f"Erro ao baixar de {site} ({tipo})"
        partes += ["", "## O download", "",
                   f"- Site: {site}",
                   f"- Formato: {tipo}{' (trecho)' if pedido['trecho'] else ''}",
                   f"- Situação: {status_download.get(id_download, '?')}",
                   f"- Erro: {limpar(erros_download.get(id_download)) or '(sem mensagem)'}"]

    # Outros erros desta vez (sem dizer de quais vídeos)
    outros = [limpar(m) for i, m in erros_download.items() if i != id_download and status_download.get(i) == "Erro"]
    if outros:
        partes += ["", "## Outros erros desde que o Puxaí abriu", ""] + [f"- {m}" for m in outros[-5:]]

    registro = _linhas_do_registro()
    partes += ["", "## Últimas linhas de erro do registro (Puxai.log)", ""]
    partes += ["```", *registro, "```"] if registro else ["(nenhuma)"]
    return {"titulo": titulo, "texto": "\n".join(partes)}


def _corpo(descricao, texto):
    descricao = (descricao or "").strip() or "(a pessoa não descreveu)"
    return f"## O que aconteceu\n\n{descricao}\n\n{texto}"


def _caber(montar_endereco, descricao, texto, limite):
    """Corta o fim do relatório até o endereço caber no limite (o começo é o mais importante)."""
    corpo = _corpo(descricao, texto)
    endereco = montar_endereco(corpo)
    while len(endereco) > limite and len(corpo) > 200:
        corpo = corpo[: int(len(corpo) * 0.85)].rstrip() + "\n\n(relatório cortado: muito grande para enviar assim)"
        endereco = montar_endereco(corpo)
    return endereco


def endereco_github(titulo, descricao, texto):
    def montar_endereco(corpo):
        return URL_NOVO_ISSUE + "?" + urllib.parse.urlencode({"title": titulo, "body": corpo})
    return _caber(montar_endereco, descricao, texto, LIMITE_GITHUB)


def endereco_email(titulo, descricao, texto):
    if not EMAIL_SUPORTE:
        return None

    def montar_endereco(corpo):
        return f"mailto:{EMAIL_SUPORTE}?" + urllib.parse.urlencode({"subject": titulo, "body": corpo},
                                                                   quote_via=urllib.parse.quote)
    return _caber(montar_endereco, descricao, texto, LIMITE_EMAIL)
