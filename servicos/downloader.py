import glob
import json
import os
import queue
import re
import shutil
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qs, unquote, urlparse

import yt_dlp
from yt_dlp.networking import Request
from yt_dlp.postprocessor import PostProcessor
from yt_dlp.utils import DownloadCancelled, download_range_func

from servicos import destinos, estatisticas, historico
from servicos.caminhos import PASTA_BASE, PASTA_DOWNLOADS
from servicos.sites import SITES_COM_FOTOS, LinkInvalido, link_real,mensagem_de_erro, opcoes_de_login, post_sem_video, titulo_amigavel

# Quantos downloads rodam ao mesmo tempo (os outros esperam na fila)
DOWNLOADS_SIMULTANEOS = 3

# Quantas vezes tenta baixar antes de marcar "Erro"
TENTATIVAS = 2

# Download de imagem por link: tamanho máximo e tipos aceitos (tipo que o site informa -> extensão)
LIMITE_IMAGEM = 50 * 1024 * 1024
TIPOS_DE_IMAGEM = {
    "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif",
    "image/heic": "heic", "image/heif": "heic", "image/svg+xml": "svg",
}
EXTENSOES_DE_IMAGEM = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif", ".svg")

# Status que indicam que o download acabou (deu certo ou não)
STATUS_FINAIS = ("Pronto", "Erro", "Cancelado")

# Dicionários e Fila globais
status_download = {}
titulos_download = {}  # ID -> título do vídeo
arquivos_salvos = {}   # ID -> caminho do arquivo pronto na pasta Downloads
cancelados = set()     # IDs que o usuário pediu para cancelar
erros_download = {}    # ID -> mensagem explicando por que o download falhou
extras_download = {}   # ID -> dados a mais para o painel (ex.: tamanho antes/depois de comprimir um vídeo)
pedidos_download = {}  # ID -> link, formato e qualidade (para o relatório de erro, mesmo depois de terminar)
# ID -> (hora, tarefa) do que chegou pela extensão há pouco. Uma imagem termina antes de o
# painel perguntar pela fila; sem isto, ela (ou o erro dela) nunca apareceria na lista
recentes_da_extensao = {}
SEGUNDOS_RECENTE = 30
fila_downloads = queue.Queue()

# Fila guardada em arquivo: o que ainda não terminou (na fila ou baixando). Se o
# programa fechar no meio, esses downloads voltam para a fila na próxima vez que
# ele abrir, continuando de onde pararam (os pedaços já baixados ficam guardados).
ARQUIVO_FILA = os.path.join(PASTA_BASE, ".fila.json")
tarefas_pendentes = {}  # ID -> tarefa (na ordem em que entraram na fila)
retomados = set()       # IDs que voltaram de uma vez anterior
_trava_fila = threading.Lock()


def _salvar_fila():
    """Grava as tarefas pendentes (num arquivo temporário e depois troca: nunca fica pela metade)."""
    with _trava_fila:
        tarefas = [dict(t, trecho=_trecho_para_salvar(t["trecho"])) for t in tarefas_pendentes.values()]
        temporario = ARQUIVO_FILA + ".tmp"
        try:
            with open(temporario, "w", encoding="utf-8") as f:
                json.dump(tarefas, f, ensure_ascii=False, indent=1)
            os.replace(temporario, ARQUIVO_FILA)
        except OSError as e:
            print(f"[FILA] Não foi possível guardar a fila: {e}")


def _trecho_para_salvar(trecho):
    # JSON não tem "infinito": fim None = até o final do vídeo
    return None if not trecho else [trecho[0], None if trecho[1] == float("inf") else trecho[1]]


def _ler_fila_salva():
    try:
        with open(ARQUIVO_FILA, encoding="utf-8") as f:
            tarefas = json.load(f)
        return [t for t in tarefas if isinstance(t, dict) and t.get("id_download") and t.get("url")]
    except (OSError, ValueError):
        return []


def ids_guardados():
    """IDs da fila guardada (os pedaços já baixados deles não são apagados ao abrir)."""
    return {t["id_download"] for t in _ler_fila_salva()}


def _terminou(id_download):
    """Tira da fila guardada um download que acabou (pronto, erro ou cancelado)."""
    if tarefas_pendentes.pop(id_download, None) is not None:
        _salvar_fila()


def nome_de_arquivo_seguro(texto):
    """Tira do título os caracteres que o Windows não aceita em nome de arquivo."""
    return re.sub(r'[\\/:*?"<>|]', '', str(texto)).strip()[:150] or "download"


def formatar_tempo(segundos):
    """80 -> "1.20" | 3725 -> "1.02.05" (sem ":" porque o Windows não aceita em nomes)."""
    segundos = int(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas}.{minutos:02d}.{segundos:02d}" if horas else f"{minutos}.{segundos:02d}"


def caminho_sem_sobrescrever(pasta, nome, extensao):
    """Se "nome.mp4" já existe, devolve "nome (2).mp4", "nome (3).mp4"..."""
    caminho = os.path.join(pasta, f"{nome}.{extensao}")
    numero = 2
    while os.path.exists(caminho):
        caminho = os.path.join(pasta, f"{nome} ({numero}).{extensao}")
        numero += 1
    return caminho


def apagar_temporarios(id_download):
    """Apaga os arquivos parciais deste download (.part, partes de vídeo/áudio...)."""
    for caminho in glob.glob(os.path.join(PASTA_DOWNLOADS, f"{glob.escape(id_download)}.*")):
        try:
            os.remove(caminho)
        except OSError:
            pass


# "(Official Video)", "[Lyrics]", "(4K Remaster)", "(Clipe Oficial)"...: sobra do título
# do vídeo que não faz parte do nome da música. "(feat. X)", "(Ao Vivo)" e "(Remix)" ficam.
SOBRAS_DO_TITULO = re.compile(
    r"\s*[(\[][^)\]]*\b(official|oficial|video|vídeo|videoclipe|clipe|clip|audio|áudio|"
    r"lyrics?|letra|visualizer|remaster(ed)?|hd|hq|4k|mv)\b[^)\]]*[)\]]",
    re.IGNORECASE,
)


def titulo_da_musica(titulo, artista):
    """"Rick Astley - Never Gonna Give You Up (Official Video)" -> "Never Gonna Give You Up"."""
    limpo = SOBRAS_DO_TITULO.sub("", titulo).strip()
    if artista:
        for separador in (" - ", " – ", " — ", " | "):
            if limpo.lower().startswith(artista.lower() + separador):
                limpo = limpo[len(artista) + len(separador):].strip()
                break
    return limpo or titulo


class DadosDoMp3(PostProcessor):
    """Ajusta o que vai gravado no MP3 (o que aparece no player e no celular).

    O yt-dlp usa os campos "meta_*" no lugar dos que ele escolheria sozinho:
    - título: o nome da música; sem ele, o título do vídeo sem o artista na
      frente nem "(Official Video)" etc. (no TikTok/Instagram, o título amigável,
      porque o "título" original é a legenda inteira do post)
    - artista: os artistas da música oficial ou o canal, sem o " - Topic"
    - gênero: só um gênero de verdade (o padrão seriam as tags do vídeo)
    - descrição: fica de fora (a do YouTube é enorme e cheia de links);
      no comentário vai o link do vídeo
    """

    def run(self, info):
        artistas = info.get('artists') or ([info['artist']] if info.get('artist') else [])
        canal = (info.get('channel') or info.get('uploader') or '').removesuffix(' - Topic')
        ano = info.get('release_year') or (info.get('upload_date') or '')[:4]

        artista = ', '.join(artistas) or canal
        info['meta_title'] = info.get('track') or titulo_da_musica(titulo_amigavel(info), artistas[0] if artistas else canal)
        info['meta_artist'] = artista
        info['meta_date'] = str(ano or '')
        info['meta_genre'] = info.get('genre') or ''
        info['meta_description'] = ''
        info['meta_synopsis'] = ''
        info['meta_comment'] = info.get('webpage_url') or ''
        return [], info


def worker_fila():
    """Fica rodando em segundo plano processando os downloads da fila."""
    while True:
        # Pega o próximo item da fila (se não houver, fica esperando travado aqui consumindo 0% de CPU)
        tarefa = fila_downloads.get()
        try:
            processar(tarefa)
            if status_download.get(tarefa["id_download"]) in STATUS_FINAIS:
                _terminou(tarefa["id_download"])
                _registrar_estatistica(tarefa)
        finally:
            # Sinaliza para a fila que essa tarefa acabou
            fila_downloads.task_done()


def _registrar_estatistica(tarefa):
    """Estatística anônima do download (só com permissão): o site e o resultado, nunca o link."""
    if not estatisticas.permitido():
        return
    from servicos.area_de_transferencia import link_de_video
    id_download = tarefa["id_download"]
    status = status_download.get(id_download)
    link = link_de_video(tarefa["url"])
    estatisticas.registrar(
        "download",
        site=link["site"] if link else "outro",
        formato=tarefa["formato"],
        qualidade=f"{tarefa['qualidade']}p" if tarefa["formato"] == "mp4" else "",
        resultado={"Pronto": "pronto", "Erro": "erro"}.get(status, "cancelado"),
        erro=erros_download.get(id_download, "") if status == "Erro" else "",  # frase fixa do Puxaí
        origem=tarefa.get("origem") or "painel",
        trecho=bool(tarefa.get("trecho")),
        retomado=id_download in retomados,
    )


def _extensao_da_imagem(dados):
    """Pelo começo do arquivo: o Pinterest guarda o original como foi enviado (JPG, PNG, GIF ou WebP)."""
    if dados.startswith(b"\x89PNG"):
        return "png"
    if dados.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if dados[8:12] == b"WEBP":
        return "webp"
    return "jpg"


def salvar_fotos_do_post(tarefa):
    """Post do Instagram ou pin do Pinterest sem vídeo (uma foto ou um carrossel de fotos):
    salva as fotos em tamanho original, no formato original, na pasta de fotos. Devolve True se salvou."""
    id_download, url = tarefa["id_download"], link_real(tarefa["url"])
    opcoes = {"quiet": True, "no_warnings": True, "ignore_no_formats_error": True, **opcoes_de_login()}
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=False)
        if info.get("extractor_key") not in SITES_COM_FOTOS:
            return False
        # Carrossel: um item por foto (os itens que são vídeos ficam de fora)
        itens = [e for e in (info.get("entries") or [info]) if e and not e.get("formats") and e.get("thumbnail")]
        if not itens:
            return False

        titulo = titulo_amigavel(info)
        if titulo.lower().startswith("vídeo de "):  # "Vídeo de fulano" (post sem legenda)
            titulo = "Foto de " + titulo[len("vídeo de "):]
        pasta = destinos.pasta_para("foto")
        nome = nome_de_arquivo_seguro(titulo)
        salvos = []
        for numero, item in enumerate(itens, 1):
            if id_download in cancelados:
                raise DownloadCancelled("Cancelado pelo usuário")
            status_download[id_download] = f"Baixando foto {numero} de {len(itens)}..." if len(itens) > 1 else "Baixando a foto..."
            # "thumbnail" é a foto inteira, no tamanho original (as outras são recortes e versões menores)
            dados = ydl.urlopen(Request(item["thumbnail"], headers=item.get("http_headers") or {})).read()
            extensao = _extensao_da_imagem(dados)
            destino = caminho_sem_sobrescrever(
                pasta, nome if len(itens) == 1 else f"{nome} ({numero} de {len(itens)})", extensao)
            with open(destino, "wb") as f:
                f.write(dados)
            historico.registrar(f"{id_download}-{numero}" if numero > 1 else id_download, destino, titulo, url)
            salvos.append(destino)

    titulos_download[id_download] = titulo
    arquivos_salvos[id_download] = salvos[0]
    extras_download[id_download] = {"fotos": len(salvos)}
    status_download[id_download] = "Pronto"
    print(f"[FILA] Post sem vídeo: {len(salvos)} foto(s) salva(s) em {pasta}")
    return True


def _ler_imagem(id_download, url):
    """Baixa a imagem do link para a memória. Devolve (dados, extensao); ValueError traz o motivo da falha."""
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("O link precisa começar com http:// ou https://.")
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            extensao = TIPOS_DE_IMAGEM.get(resposta.headers.get_content_type())
            if not extensao:
                raise ValueError("Este link não é de uma foto. Use um post do Instagram, um pin do Pinterest ou o "
                                 "endereço de uma imagem. Para baixar um vídeo, use a aba Vídeos.")
            total = resposta.length or 0
            dados = bytearray()
            while pedaco := resposta.read(64 * 1024):
                if id_download in cancelados:
                    raise DownloadCancelled("Cancelado pelo usuário")
                dados += pedaco
                if max(total, len(dados)) > LIMITE_IMAGEM:
                    raise ValueError(f"A imagem passa de {LIMITE_IMAGEM // 1024 // 1024} MB.")
                if total:
                    status_download[id_download] = f"{len(dados) / total * 100:.1f}%"
    except urllib.error.HTTPError as e:
        raise ValueError(f"O site recusou o download (erro {e.code}).") from e
    except OSError as e:
        raise ValueError("Não foi possível acessar o link.") from e
    return bytes(dados), extensao


def _endereco_da_imagem(url):
    """Link do Google Imagens (google.com/imgres?imgurl=...): o endereço da imagem que vem dentro dele."""
    partes = urlparse(url)
    if partes.path == "/imgres" and "google." in (partes.hostname or ""):
        url = parse_qs(partes.query).get("imgurl", [url])[0]
        partes = urlparse(url)
    # Dribbble: "?resize=400x300..." pede uma cópia menor; sem isso vem a imagem como foi enviada
    if partes.hostname == "cdn.dribbble.com" and "resize" in parse_qs(partes.query):
        return partes._replace(query="").geturl()
    return url


def _site_do_post(url):
    """"instagram" ou "pinterest" se o link é de uma página desses sites; None se não for.
    (As imagens de i.pinimg.com são links diretos, não páginas.)"""
    host = (urlparse(url).hostname or "").lower()
    if host == "instagram.com" or host.endswith(".instagram.com"):
        return "instagram"
    if host in ("pin.it", "www.pin.it") or re.fullmatch(r"([a-z]{2,3}\.)?pinterest\.[a-z]{2,3}(\.[a-z]{2})?", host):
        return "pinterest"
    return None


def _baixar_foto_de_post(tarefa, url, site):
    """Aba Fotos com o link de um post (Instagram) ou pin (Pinterest)."""
    id_download = tarefa["id_download"]
    try:
        status_download[id_download] = "Abrindo o post..."
        endereco = link_real(url)
        # Uma pasta do Pinterest tem centenas de pins: aqui é um pin de cada vez
        if site == "pinterest" and "/pin/" not in endereco:
            raise LinkInvalido("Cole o link de um pin do Pinterest (não o de uma pasta ou perfil).")
        if not salvar_fotos_do_post({**tarefa, "url": endereco}):
            raise LinkInvalido("Não encontrei foto neste post. Se for um vídeo, use a aba Vídeos.")
    except DownloadCancelled:
        status_download[id_download] = "Cancelado"
    except Exception as e:
        print(f"[FILA] Erro nas fotos do post {id_download}: {e}")
        erros_download[id_download] = str(e) if isinstance(e, LinkInvalido) else (
            "Não foi possível abrir esse post. Ele pode ser privado, ter sido apagado ou exigir login "
            "(veja no README como usar o arquivo cookies.txt).")
        status_download[id_download] = "Erro"


def baixar_imagem(tarefa):
    """Aba Fotos: post do Instagram, pin do Pinterest ou link direto de uma imagem. A imagem do
    link direto vai para a pasta de fotos com o nome que ela tem no link."""
    id_download, url = tarefa["id_download"], _endereco_da_imagem(tarefa["url"])
    if site := _site_do_post(url):
        return _baixar_foto_de_post(tarefa, url, site)
    try:
        status_download[id_download] = "Baixando..."
        dados, extensao = _ler_imagem(id_download, url)
        nome = os.path.splitext(os.path.basename(unquote(urlparse(url).path)))[0]
        titulo = nome_de_arquivo_seguro(nome)[:100] or "imagem"
        destino = caminho_sem_sobrescrever(destinos.pasta_para("foto"), titulo, extensao)
        with open(destino, "wb") as f:
            f.write(dados)
    except DownloadCancelled:
        status_download[id_download] = "Cancelado"
        return
    except (ValueError, OSError) as e:
        print(f"[FILA] Erro na imagem {id_download}: {e}")
        erros_download[id_download] = str(e)
        status_download[id_download] = "Erro"
        return

    titulos_download[id_download] = titulo
    arquivos_salvos[id_download] = destino
    historico.registrar(id_download, destino, titulo, url)
    status_download[id_download] = "Pronto"
    print(f"[FILA] Imagem salva em: {destino}")


def processar(tarefa):
    url = tarefa["url"]
    formato = tarefa["formato"]
    qualidade = tarefa["qualidade"]
    trecho = tarefa["trecho"]
    id_download = tarefa["id_download"]
    extensao = "mp3" if formato == "mp3" else "mp4"

    # Cancelado enquanto ainda esperava na fila
    if id_download in cancelados:
        status_download[id_download] = "Cancelado"
        return

    # Link de imagem colado na aba Vídeos também é salvo como foto: o yt-dlp "baixaria"
    # a imagem e a transformaria num .mp4
    if formato == "imagem" or urlparse(url).path.lower().endswith(EXTENSOES_DE_IMAGEM):
        baixar_imagem(tarefa)
        if status_download.get(id_download) == "Pronto":
            extras_download.setdefault(id_download, {"fotos": 1})  # o painel mostra "foto", não "MP4"
        return

    os.makedirs(PASTA_DOWNLOADS, exist_ok=True)
    caminho_temporario = os.path.join(PASTA_DOWNLOADS, f"{id_download}.{extensao}")

    def parar_se_cancelado():
        if id_download in cancelados:
            raise DownloadCancelled("Cancelado pelo usuário")

    def hook_progresso(d):
        parar_se_cancelado()
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                porcentagem = d.get('downloaded_bytes', 0) / total * 100
                status_download[id_download] = f"{min(porcentagem, 100):.1f}%"
        elif d['status'] == 'finished':
            status_download[id_download] = "Processando arquivo..."

    def hook_processamento(d):
        # Chamado antes de juntar vídeo/áudio ou converter para MP3
        parar_se_cancelado()

    # Salva com o ID no nome (e não o título) para sempre saber onde o arquivo está
    ydl_opts = {
        'outtmpl': os.path.join(PASTA_DOWNLOADS, f"{id_download}.%(ext)s"),
        'noplaylist': True,  # Link com &list=... baixa só o vídeo, não a playlist inteira
        'concurrent_fragment_downloads': 4,  # Baixa 4 partes ao mesmo tempo quando o vídeo vem fatiado
        'progress_hooks': [hook_progresso],
        'postprocessor_hooks': [hook_processamento],
        **opcoes_de_login(),  # cookies.txt, se existir (posts do Instagram que pedem login)
    }

    if formato == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            # Baixa a miniatura do vídeo para virar a capa do MP3
            'writethumbnail': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                # Título, artista, álbum e ano (ajustados por DadosDoMp3)
                {'key': 'FFmpegMetadata', 'add_metadata': True},
                # Capa: a miniatura vira JPG quadrado (corte no centro)
                {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'},
                {'key': 'EmbedThumbnail'},
            ],
            'postprocessor_args': {
                # Conversão para MP3 ~2,5x mais rápida, sem diferença audível a 192 kbps
                'extractaudio': ['-compression_level', '7'],
                # Capa quadrada, como a de um álbum. Na música oficial do YouTube a
                # miniatura é a capa do álbum com faixas dos lados: o corte deixa só a capa
                'thumbnailsconvertor+ffmpeg_o': [
                    '-c:v', 'mjpeg', '-q:v', '3',
                    '-vf', "crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'",
                ],
            },
        })
    else:
        ydl_opts.update({
            # Melhor vídeo + áudio, nunca a versão com marca d'água (TikTok)
            'format': 'bv*[format_note!*=?watermark]+ba/b[format_note!*=?watermark]',
            # "res" é a MENOR dimensão do vídeo: 720p vale tanto para 1280x720
            # (horizontal) quanto para 720x1280 (vertical: TikTok, Reels, Shorts).
            # Nunca passa da qualidade escolhida (máximo 1080p).
            # Depois prefere H.264 + AAC: arquivo menor que AV1 HDR, baixa mais
            # rápido e abre em qualquer player
            'format_sort': [f'res:{qualidade}', 'vcodec:h264', 'acodec:m4a'],
            'merge_output_format': 'mp4',
            # Garante .mp4 mesmo se vier um arquivo único em outro formato (ex.: .webm)
            'postprocessors': [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            }],
        })

    if trecho:
        # Baixa só o pedaço escolhido; corta no segundo exato (e não no quadro-chave mais próximo)
        ydl_opts['download_ranges'] = download_range_func(None, [trecho])
        ydl_opts['force_keyframes_at_cuts'] = True

    print(f"\n[FILA] Iniciando processamento do ID: {id_download}")

    try:
        # O YouTube às vezes falha do nada; tenta de novo antes de desistir
        for tentativa in range(1, TENTATIVAS + 1):
            try:
                status_download[id_download] = "Baixando..."

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    if formato == "mp3":
                        ydl.add_post_processor(DadosDoMp3(), when='pre_process')
                    info = ydl.extract_info(link_real(url), download=True)
                parar_se_cancelado()

                if os.path.exists(caminho_temporario):
                    titulo = titulo_amigavel(info)
                    nome = nome_de_arquivo_seguro(titulo)
                    if trecho:
                        inicio, fim = trecho
                        fim_texto = formatar_tempo(fim) if fim != float("inf") else "fim"
                        nome += f" (trecho {formatar_tempo(inicio)} a {fim_texto})"

                    # Playlist: pasta com o nome dela e o número na frente ("03 - Título"),
                    # para os arquivos ficarem na ordem da playlist
                    # Pasta escolhida em Configurações (Downloads, se nenhuma)
                    base = destinos.pasta_para("musica" if extensao == "mp3" else "video")
                    pasta = base
                    if tarefa.get("pasta"):
                        pasta = os.path.join(base, tarefa["pasta"])
                        os.makedirs(pasta, exist_ok=True)
                    if tarefa.get("numero"):
                        nome = f"{tarefa['numero']} - {nome}"

                    # Move para a pasta de destino, com o título no nome
                    destino = caminho_sem_sobrescrever(pasta, nome, extensao)
                    shutil.move(caminho_temporario, destino)

                    titulos_download[id_download] = titulo
                    arquivos_salvos[id_download] = destino
                    historico.registrar(id_download, destino, titulo, url)
                    status_download[id_download] = "Pronto"
                    print(f"[FILA] Sucesso! Salvo em: {destino}")
                    break

                print(f"[FILA] Arquivo final não encontrado no ID {id_download} (tentativa {tentativa}/{TENTATIVAS})")

            except DownloadCancelled:
                raise
            except Exception as e:
                if id_download in cancelados:
                    raise DownloadCancelled("Cancelado pelo usuário")
                # Post do Instagram que é foto (ou carrossel de fotos): baixa as fotos
                if post_sem_video(e):
                    try:
                        if salvar_fotos_do_post(tarefa):
                            break
                    except DownloadCancelled:
                        raise
                    except Exception as erro_das_fotos:
                        print(f"[FILA] Não foi possível baixar as fotos do post {id_download}: {erro_das_fotos}")
                print(f"[FILA] Erro no ID {id_download} (tentativa {tentativa}/{TENTATIVAS}): {e}")
                erros_download[id_download] = mensagem_de_erro(e)

            if tentativa < TENTATIVAS:
                time.sleep(2)
        else:
            status_download[id_download] = "Erro"

    except DownloadCancelled:
        status_download[id_download] = "Cancelado"
        print(f"[FILA] Download {id_download} cancelado.")

    finally:
        apagar_temporarios(id_download)


# Inicializa as Threads "Worker" em background assim que o módulo é importado
for _ in range(DOWNLOADS_SIMULTANEOS):
    threading.Thread(target=worker_fila, daemon=True).start()


def adicionar_fila(url, formato, qualidade, id_download, trecho=None, pasta=None, numero=None, titulo=None,
                   origem="painel"):
    """Adiciona um novo pedido na fila e define o status inicial.
    trecho: (inicio, fim) em segundos, para baixar só um pedaço do vídeo.
    pasta e numero (playlists): subpasta dentro de Downloads e o número que vai
    na frente do nome, já formatado (ex.: "03").
    titulo: o da prévia, para o painel mostrar se a fila voltar depois de fechar.
    origem: "painel" ou "extensao" (o painel acrescenta na lista sozinho os da extensão)."""
    cancelados.discard(id_download)
    status_download[id_download] = "Na fila..."
    tarefa = {
        "url": url,
        "formato": formato,
        "qualidade": qualidade,
        "trecho": trecho,
        "id_download": id_download,
        "pasta": pasta,
        "numero": numero,
        "titulo": titulo,
        "origem": origem,
    }
    tarefas_pendentes[id_download] = tarefa
    if origem == "extensao":
        recentes_da_extensao[id_download] = (time.monotonic(), tarefa)
    pedidos_download[id_download] = {"url": url, "formato": formato, "qualidade": qualidade, "trecho": bool(trecho)}
    _salvar_fila()
    fila_downloads.put(tarefa)


def retomar_fila():
    """Ao abrir: põe de volta na fila o que não terminou da vez anterior. Devolve quantos."""
    tarefas = _ler_fila_salva()
    for tarefa in tarefas:
        trecho = tarefa.get("trecho")
        if trecho:
            trecho = (trecho[0], float("inf") if trecho[1] is None else trecho[1])
        retomados.add(tarefa["id_download"])
        adicionar_fila(tarefa["url"], tarefa.get("formato", "mp4"), tarefa.get("qualidade"), tarefa["id_download"],
                       trecho, tarefa.get("pasta"), tarefa.get("numero"), tarefa.get("titulo"),
                       tarefa.get("origem", "painel"))
    if tarefas:
        print(f"[FILA] {len(tarefas)} download(s) da vez anterior de volta na fila.")
    return len(tarefas)


def fila_atual():
    """Os downloads que ainda não terminaram, na ordem da fila (para o painel montar a lista),
    mais os da extensão que acabaram de terminar."""
    tarefas = {i: t for i, t in list(tarefas_pendentes.items()) if status_download.get(i) not in STATUS_FINAIS}
    for id_download, (hora, tarefa) in list(recentes_da_extensao.items()):
        if time.monotonic() - hora > SEGUNDOS_RECENTE:
            recentes_da_extensao.pop(id_download, None)
        else:
            tarefas.setdefault(id_download, tarefa)
    return [
        {**{k: t[k] for k in ("id_download", "url", "formato", "qualidade", "titulo", "origem")},
         "trecho": _trecho_para_salvar(t["trecho"]), "status": status_download.get(t["id_download"]),
         "retomado": t["id_download"] in retomados}
        for t in tarefas.values()
    ]


def quantos_em_andamento():
    """Quantos downloads (e compressões de vídeo) ainda estão na fila ou acontecendo."""
    return sum(st not in STATUS_FINAIS for st in list(status_download.values()))


def downloads_em_andamento():
    """True se algum download ainda está na fila ou acontecendo."""
    return quantos_em_andamento() > 0


def cancelar_download(id_download):
    """Pede para cancelar. Devolve False se o download não existe ou já terminou."""
    status = status_download.get(id_download)
    if status is None or status in STATUS_FINAIS:
        return False

    cancelados.add(id_download)
    if status == "Na fila...":
        status_download[id_download] = "Cancelado"
    # Sai da fila guardada na hora: se o programa fechar antes, ele não volta
    _terminou(id_download)
    return True

