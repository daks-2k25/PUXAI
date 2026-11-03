"""Atualiza o próprio programa pelo botão "Atualizar agora" do painel.

A versão instalada fica em versao.json. O painel compara com o versao.json do
GitHub (no programa gerado, com a última Release) e, se houver versão nova,
oferece a atualização:

- Pasta baixada como ZIP: baixa o ZIP novo do GitHub e substitui os arquivos
  do projeto (downloads, ambiente, logs e atalho não são tocados).
- Pasta clonada com git: roda "git pull", mas só se estiver na branch principal
  e sem mudanças locais (para não atrapalhar quem está desenvolvendo).
- Programa gerado (Puxai.exe ou o do Linux): baixa o arquivo da Release e
  troca os arquivos do programa (veja atualizacao_do_programa.py).

Depois de atualizar pelo ZIP ou pelo git, o programa reinicia pelo iniciar.bat
(iniciar.sh, no Linux), que também instala bibliotecas novas, se a versão nova
precisar.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

from servicos import atualizacao_do_programa, preferencias
from servicos.caminhos import EXECUTAVEL, PASTA_RECURSOS

REPOSITORIO = "daks-2k25/API-BAIXAR-YOUTUBE"
RAMO = "main"
URL_VERSAO = f"https://raw.githubusercontent.com/{REPOSITORIO}/{RAMO}/versao.json"
URL_ZIP = f"https://codeload.github.com/{REPOSITORIO}/zip/refs/heads/{RAMO}"
# Programa gerado: a versão nova é a da última Release (que já tem o arquivo pronto).
# PUXAI_URL_RELEASE troca o endereço, para testar a atualização sem publicar.
URL_RELEASE = os.environ.get("PUXAI_URL_RELEASE") or f"https://api.github.com/repos/{REPOSITORIO}/releases/latest"
URL_VERSAO_DA_TAG = "https://raw.githubusercontent.com/" + REPOSITORIO + "/{tag}/versao.json"

PASTA_PROJETO = PASTA_RECURSOS
ARQUIVO_VERSAO = os.path.join(PASTA_PROJETO, "versao.json")
# Lista dos arquivos que vieram na última atualização (para apagar os que saírem do projeto)
ARQUIVO_MANIFESTO = os.path.join(PASTA_PROJETO, ".arquivos_do_programa.txt")

# Pastas e arquivos da pessoa que a atualização nunca toca
PROTEGIDOS = (
    # "BaixarYouTube": pasta do programa gerado antes de o app se chamar Puxaí
    # ".ffmpeg": o FFmpeg que o iniciar.sh baixa no Linux
    ".git", ".ambiente", ".venv", ".ffmpeg", ".atualizacao", "downloads", "Puxai", "BaixarYouTube", "atualizacoes",
    "ferramentas/compilacao", ".atalho_criado", ".arquivos_do_programa.txt",
    ".preferencias.json", ".historico.json", ".fila.json", "cookies.txt",
)


# Guarda a última consulta ao GitHub por alguns minutos
_cache = {"momento": 0, "dados": None, "release": None}
CACHE_SEGUNDOS = 10 * 60


def _versao_como_tupla(versao):
    return tuple(int(p) for p in str(versao).split(".") if p.isdigit())


def versao_instalada():
    try:
        with open(ARQUIVO_VERSAO, encoding="utf-8") as f:
            return json.load(f).get("versao", "0")
    except (OSError, ValueError):
        return "0"


def versao_adiada():
    """Versão nova que a pessoa mandou avisar depois (não mostra a notificação de novo)."""
    return preferencias.obter("atualizacao_adiada")


def adiar(versao):
    preferencias.salvar("atualizacao_adiada", str(versao))


def _git(*argumentos):
    resultado = subprocess.run(
        ["git", *argumentos], cwd=PASTA_PROJETO, capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return resultado.returncode, (resultado.stdout + resultado.stderr).strip()


def como_atualizar(release=None):
    """Devolve ("zip" | "git" | "programa", None) ou (None, motivo pelo qual não dá para atualizar aqui)."""
    if EXECUTAVEL:
        manual = (f"Baixe a versão nova em github.com/{REPOSITORIO}/releases/latest "
                  "e descompacte por cima da pasta do programa (suas configurações continuam).")
        if not atualizacao_do_programa.sistema_suportado():
            return None, manual
        if release is not None and atualizacao_do_programa.arquivo_da_release(release) is None:
            return None, "A versão nova ainda está sendo preparada para o seu sistema. Tente de novo daqui a pouco."
        if not atualizacao_do_programa.pasta_permite_escrever():
            return None, "A pasta do programa não aceita arquivos novos (ex.: está em Arquivos de Programas). " + manual
        return "programa", None

    if os.path.isdir(os.path.join(PASTA_PROJETO, ".git")):
        if shutil.which("git") is None:
            return None, "Esta pasta usa git, mas o git não foi encontrado. Atualize com \"git pull\"."
        codigo, ramo = _git("rev-parse", "--abbrev-ref", "HEAD")
        if codigo != 0 or ramo != RAMO:
            return None, f"Esta pasta está na branch \"{ramo}\". A atualização automática só funciona na branch \"{RAMO}\"."
        codigo, mudancas = _git("status", "--porcelain", "--untracked-files=no")
        if mudancas:
            return None, "Esta pasta tem alterações no código que ainda não foram salvas no git. Atualize com \"git pull\"."
        return "git", None

    return "zip", None


def verificar(forcar=False):
    """Compara a versão instalada com a do GitHub."""
    agora = time.time()
    if not forcar and _cache["dados"] and agora - _cache["momento"] < CACHE_SEGUNDOS:
        return _cache["dados"]

    atual = versao_instalada()
    dados = {"atual": atual, "nova": None, "novidades": [], "disponivel": False,
             "pode_atualizar": False, "motivo": None}
    release = None
    try:
        if EXECUTAVEL:
            release = atualizacao_do_programa.ler_json(URL_RELEASE)
            dados["nova"] = str(release["tag_name"]).lstrip("v")
            dados["novidades"] = _novidades_da_versao(release["tag_name"])
        else:
            pedido = urllib.request.Request(URL_VERSAO, headers={"Cache-Control": "no-cache"})
            with urllib.request.urlopen(pedido, timeout=8) as resposta:
                remoto = json.load(resposta)
            dados["nova"] = remoto.get("versao")
            dados["novidades"] = remoto.get("novidades", [])
        dados["disponivel"] = _versao_como_tupla(dados["nova"]) > _versao_como_tupla(atual)
    except Exception as e:
        dados["motivo"] = f"Não foi possível verificar atualizações ({e})."
        return dados  # sem cache: tenta de novo na próxima vez

    if dados["disponivel"]:
        forma, motivo = como_atualizar(release)
        dados["pode_atualizar"] = forma is not None
        dados["motivo"] = motivo

    _cache.update(momento=agora, dados=dados, release=release)
    return dados


def _novidades_da_versao(tag):
    """As novidades do versao.json daquela versão (o mesmo texto do aviso de quem usa o código)."""
    try:
        return atualizacao_do_programa.ler_json(URL_VERSAO_DA_TAG.format(tag=tag)).get("novidades", [])
    except Exception:
        return []


def _protegido(caminho_relativo):
    caminho = caminho_relativo.replace("\\", "/")
    return caminho.endswith(".log") or any(
        caminho == p or caminho.startswith(p + "/") for p in PROTEGIDOS
    )


def _atualizar_pelo_zip():
    with urllib.request.urlopen(URL_ZIP, timeout=60) as resposta:
        conteudo = resposta.read()

    with zipfile.ZipFile(io.BytesIO(conteudo)) as pacote:
        # O ZIP do GitHub tem tudo dentro de uma pasta "REPOSITORIO-RAMO/"
        raiz = pacote.namelist()[0].split("/")[0] + "/"
        arquivos = {
            nome[len(raiz):]: nome for nome in pacote.namelist()
            if nome.startswith(raiz) and not nome.endswith("/") and nome != raiz
        }
        if "app.py" not in arquivos or "versao.json" not in arquivos:
            raise ValueError("o pacote baixado não parece ser deste programa")

        # Extrai tudo numa pasta temporária primeiro: se algo falhar no meio,
        # o programa instalado continua intacto
        with tempfile.TemporaryDirectory() as temporaria:
            for relativo, nome in arquivos.items():
                if _protegido(relativo):
                    continue
                destino_temporario = os.path.join(temporaria, relativo)
                os.makedirs(os.path.dirname(destino_temporario), exist_ok=True)
                with pacote.open(nome) as origem, open(destino_temporario, "wb") as destino:
                    shutil.copyfileobj(origem, destino)

            # Copia por cima dos arquivos do projeto
            novos = set()
            for pasta, _, nomes in os.walk(temporaria):
                for nome in nomes:
                    origem = os.path.join(pasta, nome)
                    relativo = os.path.relpath(origem, temporaria).replace("\\", "/")
                    destino = os.path.join(PASTA_PROJETO, relativo)
                    os.makedirs(os.path.dirname(destino), exist_ok=True)
                    shutil.copy2(origem, destino)
                    novos.add(relativo)

    # Apaga arquivos que existiam na versão anterior e saíram do projeto
    try:
        with open(ARQUIVO_MANIFESTO, encoding="utf-8") as f:
            antigos = {linha.strip() for linha in f if linha.strip()}
    except OSError:
        antigos = set()  # primeira atualização: não apaga nada
    for relativo in antigos - novos:
        caminho = os.path.join(PASTA_PROJETO, relativo)
        if not _protegido(relativo) and os.path.isfile(caminho):
            os.remove(caminho)

    with open(ARQUIVO_MANIFESTO, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(novos)))


def _atualizar_pelo_git():
    codigo, saida = _git("pull", "--ff-only", "origin", RAMO)
    if codigo != 0:
        raise RuntimeError(f"git pull falhou: {saida}")


def aplicar():
    """Baixa e instala a versão nova. Não reinicia (veja reiniciar()). Devolve a versão nova."""
    release = None
    if EXECUTAVEL:
        release = _cache["release"] or atualizacao_do_programa.ler_json(URL_RELEASE)
    forma, motivo = como_atualizar(release)
    if forma is None:
        raise RuntimeError(motivo)
    print(f"[ATUALIZAÇÃO] Atualizando pelo {forma} (versão atual: {versao_instalada()})...")
    if forma == "programa":
        # Só baixa e prepara: os arquivos são trocados depois que o programa fechar
        atualizacao_do_programa.baixar_e_preparar(release)
        nova = str(release["tag_name"]).lstrip("v")
    else:
        if forma == "git":
            _atualizar_pelo_git()
        else:
            _atualizar_pelo_zip()
        nova = versao_instalada()
    _cache.update(momento=0, dados=None, release=None)
    print(f"[ATUALIZAÇÃO] Versão {nova} pronta.")
    return nova


def andamento():
    """Quanto do arquivo do programa já foi baixado (para a porcentagem no painel)."""
    return dict(atualizacao_do_programa.andamento)


def reiniciar():
    """Abre o iniciar.bat (ou iniciar.sh) daqui a 2 segundos (tempo de este processo fechar).
    Ele instala bibliotecas novas, se houver, e abre o programa de novo.
    No programa gerado, abre o script que troca os arquivos e abre a versão nova."""
    if EXECUTAVEL:
        atualizacao_do_programa.trocar_e_reabrir()
        return
    if sys.platform != "win32":
        # "sh iniciar.sh" e não "./iniciar.sh": a atualização pelo ZIP não guarda a permissão de executar
        subprocess.Popen(["sh", "-c", 'sleep 2; exec sh "$0"', os.path.join(PASTA_PROJETO, "iniciar.sh")],
                         cwd=PASTA_PROJETO, start_new_session=True, close_fds=True)
        return
    iniciar = os.path.join(PASTA_PROJETO, "iniciar.bat")
    sem_janela = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    # "ping" para esperar: o "timeout" do Windows falha quando não há janela de console
    subprocess.Popen(
        f'cmd /c ping -n 3 127.0.0.1 >nul & "{iniciar}"',
        cwd=PASTA_PROJETO, creationflags=sem_janela, close_fds=True,
    )
