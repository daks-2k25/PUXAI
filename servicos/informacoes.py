import threading

import yt_dlp

from servicos.sites import SITES_COM_FOTOS, link_real, nome_do_site, opcoes_de_login, titulo_amigavel

# Guarda as últimas consultas: colar o mesmo link de novo responde na hora
LIMITE_CACHE = 100
cache_informacoes = {}
trava = threading.Lock()


def formatar_duracao(segundos):
    """165 -> "2:45" | 3725 -> "1:02:05\""""
    if not segundos:
        return None
    segundos = int(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas:
        return f"{horas}:{minutos:02d}:{segundos:02d}"
    return f"{minutos}:{segundos:02d}"


def obter_informacoes(url):
    """Busca título, canal, duração e miniatura do vídeo, sem baixar nada."""
    with trava:
        if url in cache_informacoes:
            return cache_informacoes[url]

    opcoes = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,  # Vídeo dentro de playlist: pega só o vídeo
        'skip_download': True,
        # Link de playlist/canal: só lista os vídeos, sem abrir um por um
        'extract_flat': 'in_playlist',
        'playlistend': 1,
        **opcoes_de_login(),
    }
    endereco = link_real(url)  # pin.it/... (link curto do Pinterest) -> o link do pin
    if any(site in endereco.lower() for site in ("instagram.com", "pinterest.")):
        # Post (ou pin) de foto não tem vídeo: em vez de erro, a prévia mostra a foto (o Puxaí baixa ela)
        opcoes['ignore_no_formats_error'] = True
        opcoes.pop('playlistend')
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(endereco, download=False)

    carrossel = info.get("extractor_key") == "Instagram" and info.get("_type") == "playlist"
    foto = info.get("extractor_key") in SITES_COM_FOTOS and info.get("_type") != "playlist" and not info.get("formats")
    if carrossel or foto:
        # Carrossel do Instagram (vários itens num post) ou post/pin de foto: é um post só, não uma
        # playlist (a pasta de um pin do Pinterest, essa sim, continua sendo uma lista)
        itens = [e for e in (info.get("entries") or [info]) if e]
        fotos = sum(1 for e in itens if not e.get("formats"))
        resultado = {
            "id": info.get("id"),
            "titulo": titulo_amigavel(info),
            "canal": info.get("channel") or info.get("uploader"),
            "site": nome_do_site(info),
            "duracao": "",
            "miniatura": info.get("thumbnail") or next((e.get("thumbnail") for e in itens if e.get("thumbnail")), None),
            "youtube": False,
            "fotos": fotos,  # o painel avisa que vai baixar a(s) foto(s)
            "videos": len(itens) - fotos,
        }
    elif info.get("_type") == "playlist":
        # Canal, álbum, playlist sem "list=" no link...: o painel abre a lista de vídeos
        resultado = {"playlist": True, "titulo": info.get("title")}
    else:
        resultado = {
            "id": info.get("id"),
            "titulo": titulo_amigavel(info),
            "canal": info.get("channel") or info.get("uploader"),
            "site": nome_do_site(info),  # "YouTube", "TikTok", "Twitch"...
            "duracao": formatar_duracao(info.get("duration")),
            "miniatura": info.get("thumbnail"),
            # Só vídeos do YouTube podem ser assistidos dentro do painel
            "youtube": info.get("extractor_key") == "Youtube",
        }

    _guardar(cache_informacoes, url, resultado)
    return resultado


def _guardar(cache, chave, valor):
    with trava:
        if len(cache) >= LIMITE_CACHE:
            cache.pop(next(iter(cache)))
        cache[chave] = valor


# ==========================================
# Playlists (e canais, álbuns...): lista os vídeos para escolher quais baixar
# ==========================================

# Mais que isso deixaria a lista lenta de carregar e de marcar
LIMITE_PLAYLIST = 200
cache_playlists = {}

# Vídeos que aparecem na playlist mas não podem ser baixados
TITULOS_INDISPONIVEIS = {"[Private video]", "[Deleted video]", "[Unavailable video]"}


def _miniatura(entrada):
    if entrada.get("thumbnail"):
        return entrada["thumbnail"]
    miniaturas = entrada.get("thumbnails") or []
    # A lista vem da menor para a maior; uma média basta para a lista do painel
    return miniaturas[len(miniaturas) // 2].get("url") if miniaturas else None


def obter_playlist(url):
    """Título, canal e os primeiros LIMITE_PLAYLIST vídeos de uma playlist, sem baixar nada."""
    with trava:
        if url in cache_playlists:
            return cache_playlists[url]

    opcoes = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': 'in_playlist',  # só a lista: rápido mesmo com centenas de vídeos
        'playlistend': LIMITE_PLAYLIST,
        **opcoes_de_login(),
    }
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=False)

        # Página inicial de um canal do YouTube: a "playlist" são as abas
        # (Vídeos, Shorts, Ao vivo). Usa a aba Vídeos.
        entradas = [e for e in info.get("entries") or [] if e]
        if entradas and all(e.get("_type") == "playlist" for e in entradas):
            if info.get("extractor_key") != "YoutubeTab":
                raise ValueError("Este link tem várias listas dentro. Abra uma playlist específica e cole o link dela.")
            info = ydl.extract_info(info.get("webpage_url", url).rstrip("/") + "/videos", download=False)

    if info.get("_type") != "playlist":
        raise ValueError("Este link não é de uma playlist.")

    itens = []
    for numero, entrada in enumerate(info.get("entries") or [], start=1):
        if not entrada:
            continue
        link = entrada.get("url") or entrada.get("webpage_url") or ""
        titulo = entrada.get("title") or ""
        disponivel = (
            link.startswith("http")
            and titulo not in TITULOS_INDISPONIVEIS
            and entrada.get("availability") not in ("private", "needs_auth", "subscriber_only", "premium_only")
        )
        itens.append({
            "numero": numero,
            "url": link,
            "titulo": titulo or f"Vídeo {numero}",
            "duracao": formatar_duracao(entrada.get("duration")),
            "miniatura": _miniatura(entrada),
            "disponivel": disponivel,
        })

    total = info.get("playlist_count") or len(itens)
    resultado = {
        "titulo": info.get("title") or "Playlist",
        "canal": info.get("channel") or info.get("uploader"),
        "site": nome_do_site(info),
        "total": max(total, len(itens)),
        "limite": LIMITE_PLAYLIST,
        "itens": itens,
    }
    _guardar(cache_playlists, url, resultado)
    return resultado
