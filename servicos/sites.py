"""O que é comum aos sites de vídeo: nomes, títulos, login e mensagens de erro.

O Puxaí baixa de qualquer site que o yt-dlp conhece (mais de mil): YouTube,
TikTok, Instagram, X, Facebook, Twitch, SoundCloud, Dailymotion, Vimeo...
"""
import os
import urllib.parse
import urllib.request
from urllib.parse import parse_qs, urlparse

from servicos.caminhos import PASTA_BASE

# Login opcional: alguns vídeos só abrem com uma conta logada (posts do Instagram,
# Reddit, Vimeo, vídeos com restrição de idade...). Coloque um cookies.txt
# (exportado do navegador com uma extensão como "Get cookies.txt LOCALLY") ao
# lado do programa e ele passa a ser usado em todos os sites.
ARQUIVO_COOKIES = os.path.join(PASTA_BASE, "cookies.txt")

# Nome do extrator do yt-dlp (começo do nome) -> nome para mostrar no painel
NOMES_DOS_SITES = {
    "Youtube": "YouTube", "TikTok": "TikTok", "Instagram": "Instagram", "Twitter": "X (Twitter)",
    "Facebook": "Facebook", "Twitch": "Twitch", "Soundcloud": "SoundCloud", "DailyMotion": "Dailymotion",
    "Vimeo": "Vimeo", "Reddit": "Reddit", "Kwai": "Kwai", "Pinterest": "Pinterest", "BiliBili": "Bilibili",
    "Bandcamp": "Bandcamp", "Mixcloud": "Mixcloud", "Streamable": "Streamable", "NineGag": "9GAG",
    "ArchiveOrg": "Internet Archive", "Imgur": "Imgur", "Threads": "Threads", "Bluesky": "Bluesky",
    "Tumblr": "Tumblr", "Rumble": "Rumble", "Kick": "Kick", "Odysee": "Odysee", "Snapchat": "Snapchat",
    "Globo": "Globoplay", "Spotify": "Spotify", "Linkedin": "LinkedIn", "Loom": "Loom", "Ted": "TED",
}


def nome_amigavel(chave_do_extrator, nome_interno=""):
    """"TwitchClips" -> "Twitch". Site sem nome cadastrado: o nome que o yt-dlp usa."""
    chave = chave_do_extrator or ""
    for prefixo, nome in NOMES_DOS_SITES.items():
        if chave.lower().startswith(prefixo.lower()):
            return nome
    nome = (nome_interno or chave).split(":")[0]
    # "CNN" fica "CNN"; "youtube" vira "Youtube"
    return nome if any(letra.isupper() for letra in nome) else nome.capitalize()


def e_playlist_sem_video(url):
    """True quando o link é de uma playlist inteira (ex.: youtube.com/playlist?list=...).
    Um vídeo aberto dentro de uma playlist (watch?v=...&list=...) é aceito:
    o downloader baixa só aquele vídeo."""
    try:
        partes = urlparse(str(url).strip())
    except ValueError:
        return False

    parametros = parse_qs(partes.query)
    if "list" not in parametros:
        return False

    host = (partes.hostname or "").lower()
    tem_video = (
        "v" in parametros
        or (host.endswith("youtu.be") and len(partes.path) > 1)
        or partes.path.startswith(("/shorts/", "/live/", "/embed/"))
    )
    return not tem_video


def opcoes_de_login():
    """Opções do yt-dlp para usar o login do cookies.txt, se ele existir."""
    if os.path.isfile(ARQUIVO_COOKIES):
        return {"cookiefile": ARQUIVO_COOKIES}
    return {}


def nome_do_site(info):
    return nome_amigavel(info.get("extractor_key"), info.get("extractor"))


def titulo_amigavel(info):
    """O Instagram devolve títulos como "Video by fulano" e o Pinterest, "Pinterest video #123";
    nesses casos usa a primeira linha da legenda (ou descrição), que descreve melhor."""
    titulo = (info.get("title") or "").strip()
    autor = info.get("channel") or info.get("uploader") or ""
    if not titulo or titulo.lower().startswith(("video by ", "post by ", "pinterest video #")):
        legenda = (info.get("description") or "").strip().splitlines()
        primeira_linha = legenda[0].strip() if legenda else ""
        if primeira_linha:
            titulo = primeira_linha
        elif autor:
            titulo = f"Vídeo de {autor}"
    if len(titulo) > 100:
        titulo = titulo[:100].rstrip() + "…"
    return titulo or info.get("id") or "video"


COOKIES = "Coloque um arquivo cookies.txt ao lado do programa (veja o README) e tente de novo."
COOKIES_NO_MEIO = "coloque um arquivo cookies.txt ao lado do programa (veja o README)."

# (trechos da mensagem do yt-dlp, mensagem para quem usa). A ordem importa: a
# primeira que combinar vale (ex.: "Private video. Sign in..." é "privado", não "login").
# Sites em que um post sem vídeo é uma foto (ou várias): o Puxaí baixa a(s) foto(s)
SITES_COM_FOTOS = ("Instagram", "Pinterest")


class LinkInvalido(ValueError):
    """Link que dá para saber, sem o yt-dlp, que não funciona (a mensagem já é para quem usa)."""


def link_real(url):
    """Links curtos do Pinterest (pin.it/..., os do botão Compartilhar do app) viram o link
    do pin, que o yt-dlp entende. Os outros links voltam como estão."""
    if urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.") != "pin.it":
        return url
    pedido = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(pedido, timeout=15) as resposta:
        final = resposta.geturl()
    if "/pin/" not in final:
        # Link curto que não existe (ou expirou): o Pinterest manda para a página inicial
        raise LinkInvalido("Esse link curto do Pinterest não leva a nenhum pin (pode ter expirado). "
                         "Abra o pin e copie o link de novo.")
    return final


# Frases do yt-dlp para "este post não tem vídeo" (no Instagram e no Pinterest, o Puxaí baixa a foto)
SEM_VIDEO = ("there is no video", "there's no video", "no video could be found", "no video formats", "no media found")


def post_sem_video(erro):
    return any(trecho in str(erro).lower() for trecho in SEM_VIDEO)


MENSAGENS = [
    # Falha no próprio computador, não no link (veja servicos/certificados.py)
    (("curl: (77)", "trust anchors"),
     "O Puxaí não conseguiu abrir os certificados de segurança neste computador. Feche e abra o programa; "
     "se continuar, mova a pasta do Puxaí para um caminho sem acentos."),
    # O Instagram responde assim tanto para post apagado/privado quanto para post que pede login
    (("empty media response",),
     "Não foi possível abrir esse post do Instagram. Ele pode ser privado, ter sido apagado "
     "ou exigir login (nesse caso, veja no README como usar o arquivo cookies.txt)."),
    (("not a bot",),
     "O YouTube pediu para confirmar que não é um robô. Espere alguns minutos e tente de novo; "
     f"se continuar, {COOKIES_NO_MEIO}"),
    (("tls fingerprint", "impersonat"),
     "Esse site bloqueou o acesso de programas (só deixa navegadores). Tente de novo mais tarde; "
     f"se o vídeo pedir login, {COOKIES_NO_MEIO}"),
    (("private", "privado"), "Esse vídeo é privado."),
    (("sign in to confirm your age", "age-restricted", "age restricted"),
     f"Esse vídeo tem restrição de idade e só abre com login. {COOKIES}"),
    (("login", "logged-in", "log in", "sign in", "authentication", "cookies", "rate-limit"),
     f"Esse vídeo exige login para ser baixado. {COOKIES}"),
    (SEM_VIDEO,
     "Esse post não tem vídeo nem foto que dê para baixar (só texto)."),
    (("unsupported url",),
     "O Puxaí não reconhece esse link. Confira se é o link do próprio vídeo (e não de um perfil "
     "ou da página inicial do site)."),
    (("getaddrinfo", "timed out", "network is unreachable", "connection reset", "connection refused",
      "nodename nor servname", "no address associated"),
     "Sem conexão com o site. Confira a internet e tente de novo."),
    (("not available", "unavailable", "removed", "deleted", "404"),
     "Esse vídeo não está disponível (pode ter sido apagado ou ser restrito)."),
    (("please report this issue", "unable to extract", "cannot parse"),
     "O Puxaí não conseguiu ler esse vídeo: o site deve ter mudado. Tente de novo mais tarde "
     "(o leitor de sites, o yt-dlp, é atualizado sozinho)."),
    (("http error 5", "unable to download", "http error 403", "http error 429"),
     "O site não respondeu ou recusou o pedido agora. Tente de novo em alguns minutos."),
]


def mensagem_de_erro(erro):
    """Traduz os erros mais comuns do yt-dlp para uma mensagem que o usuário entenda."""
    if isinstance(erro, LinkInvalido):
        return str(erro)
    texto = str(erro).lower()
    for trechos, mensagem in MENSAGENS:
        if any(trecho in texto for trecho in trechos):
            return mensagem
    return "Não encontramos esse vídeo. Confira o link."
