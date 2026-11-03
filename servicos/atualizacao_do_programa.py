"""Atualização do programa gerado (Puxai.exe no Windows, Puxai no Linux).

O botão "Atualizar agora" baixa o arquivo do programa da última Release do
GitHub (o mesmo que a pessoa baixaria pelo site), confere o SHA-256 que o
GitHub publica para ele e extrai numa pasta ao lado do programa (.atualizacao).

Um programa aberto não consegue trocar os próprios arquivos (no Windows, o
.exe e as DLLs ficam presos enquanto ele roda). Por isso, quem troca é um
script pequeno (PowerShell no Windows, sh no Linux): ele espera o Puxaí
fechar, põe os arquivos novos no lugar e abre o programa de novo. Se algo
falhar no meio, volta os arquivos antigos.

Configurações, histórico, cookies e logs não vêm no pacote, então continuam
como estão.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

from servicos import sistema
from servicos.caminhos import PASTA_BASE

WINDOWS = sys.platform == "win32"
ARQUIVO = "Puxai-windows.zip" if WINDOWS else "Puxai-linux.tar.xz"
EXECUTAVEL = "Puxai.exe" if WINDOWS else "Puxai"
PASTA_PREPARO = os.path.join(PASTA_BASE, ".atualizacao")
PASTA_NOVA = os.path.join(PASTA_PREPARO, "Puxai")

# Andamento do download, para o painel mostrar a porcentagem
andamento = {"etapa": None, "baixado": 0, "total": 0}


def sistema_suportado():
    return WINDOWS or sys.platform.startswith("linux")


def arquivo_da_release(release):
    """O arquivo deste sistema na Release (com o SHA-256), ou None se ainda não tem."""
    for arquivo in release.get("assets", []):
        if arquivo.get("name") == ARQUIVO and str(arquivo.get("digest", "")).startswith("sha256:"):
            return arquivo
    return None


def pasta_permite_escrever():
    """A pasta do programa aceita arquivos novos? (Ex.: em "Arquivos de Programas", não.)"""
    teste = os.path.join(PASTA_BASE, ".teste_de_escrita")
    try:
        with open(teste, "w") as f:
            f.write("ok")
        os.remove(teste)
        return True
    except OSError:
        return False


def baixar_e_preparar(release):
    """Baixa, confere e extrai a versão nova em .atualizacao/Puxai. Não troca nada ainda."""
    arquivo = arquivo_da_release(release)
    if arquivo is None:
        raise RuntimeError("a versão nova ainda não está pronta para este sistema")

    shutil.rmtree(PASTA_PREPARO, ignore_errors=True)
    os.makedirs(PASTA_PREPARO)
    pacote = os.path.join(PASTA_PREPARO, ARQUIVO)

    andamento.update(etapa="baixando", baixado=0, total=int(arquivo.get("size") or 0))
    resumo = hashlib.sha256()
    try:
        with urllib.request.urlopen(arquivo["browser_download_url"], timeout=60) as resposta, open(pacote, "wb") as destino:
            while bloco := resposta.read(1024 * 1024):
                destino.write(bloco)
                resumo.update(bloco)
                andamento["baixado"] += len(bloco)

        # Confere que o arquivo chegou inteiro e é o publicado na Release
        if resumo.hexdigest() != arquivo["digest"].split(":", 1)[1].lower():
            raise RuntimeError("o arquivo baixado não confere com o do GitHub (SHA-256 diferente)")

        andamento["etapa"] = "extraindo"
        if pacote.endswith(".zip"):
            with zipfile.ZipFile(pacote) as zipado:
                zipado.extractall(PASTA_PREPARO)
        else:
            with tarfile.open(pacote) as compactado:
                # filter="data": não deixa o pacote escrever fora da pasta nem criar links perigosos
                if hasattr(tarfile, "data_filter"):
                    compactado.extractall(PASTA_PREPARO, filter="data")
                else:
                    compactado.extractall(PASTA_PREPARO)
        os.remove(pacote)

        if not os.path.isfile(os.path.join(PASTA_NOVA, EXECUTAVEL)):
            raise RuntimeError("o pacote baixado não parece ser deste programa")
    except Exception:
        shutil.rmtree(PASTA_PREPARO, ignore_errors=True)
        raise
    finally:
        andamento["etapa"] = None


def limpar_sobras():
    """Ao abrir: apaga uma atualização que ficou pela metade (ex.: o PC desligou no meio).
    (cwd=PASTA_BASE no script de troca: o Windows não apaga a pasta em que um programa está.)"""
    if os.path.isdir(PASTA_PREPARO):
        shutil.rmtree(PASTA_PREPARO, ignore_errors=True)


def trocar_e_reabrir():
    """Abre o script que espera este processo fechar, troca os arquivos e abre a versão nova."""
    executavel = os.path.join(PASTA_BASE, EXECUTAVEL)
    if WINDOWS:
        script = os.path.join(PASTA_PREPARO, "trocar.ps1")
        # utf-8-sig: o PowerShell do Windows só lê os acentos certos com o BOM
        with open(script, "w", encoding="utf-8-sig") as f:
            f.write(SCRIPT_WINDOWS)
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", script,
             "-Processo", str(os.getpid()), "-Nova", PASTA_NOVA, "-Destino", PASTA_BASE, "-Programa", executavel],
            cwd=PASTA_BASE, close_fds=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    else:
        script = os.path.join(PASTA_PREPARO, "trocar.sh")
        with open(script, "w", encoding="utf-8") as f:
            f.write(SCRIPT_LINUX)
        # Com o ambiente do sistema: o do programa gerado aponta para as bibliotecas dele
        subprocess.Popen(["sh", script, str(os.getpid()), PASTA_NOVA, PASTA_BASE, executavel],
                         cwd=PASTA_BASE, env=sistema.ambiente(), close_fds=True, start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ler_json(url):
    pedido = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(pedido, timeout=10) as resposta:
        return json.load(resposta)


# Os dois scripts fazem o mesmo: esperar o Puxaí fechar; para cada item do pacote
# novo, guardar o antigo em .atualizacao/antigo e pôr o novo no lugar; se der
# erro, devolver os antigos. Depois, abrir o programa e apagar a .atualizacao.
# O yt-dlp baixado antes (atualizacoes/) sai: a versão nova já traz um mais novo.

SCRIPT_WINDOWS = r"""
param([int]$Processo, [string]$Nova, [string]$Destino, [string]$Programa)
$ErrorActionPreference = "Stop"
$preparo = Split-Path -Parent $Nova
$antigo = Join-Path $preparo "antigo"
$registro = Join-Path $Destino "Puxai.log"
function Escrever($texto) { Add-Content -LiteralPath $registro -Value "[ATUALIZAÇÃO] $texto" -Encoding utf8 -ErrorAction SilentlyContinue }

# Espera o Puxaí fechar (até 60 segundos)
Wait-Process -Id $Processo -Timeout 60 -ErrorAction SilentlyContinue

# O antivírus pode segurar um arquivo por um instante: tenta algumas vezes
function Mover($de, $para) {
    for ($tentativa = 1; ; $tentativa++) {
        try { Move-Item -LiteralPath $de -Destination $para -Force; return }
        catch { if ($tentativa -ge 20) { throw }; Start-Sleep -Milliseconds 500 }
    }
}

$trocados = @()
try {
    New-Item -ItemType Directory -Force $antigo | Out-Null
    foreach ($item in Get-ChildItem -LiteralPath $Nova -Force) {
        $alvo = Join-Path $Destino $item.Name
        if (Test-Path -LiteralPath $alvo) { Mover $alvo (Join-Path $antigo $item.Name) }
        $trocados += $item.Name
        Mover $item.FullName $alvo
    }
    Remove-Item (Join-Path $Destino "atualizacoes\*") -Force -ErrorAction SilentlyContinue
    Escrever "Programa atualizado."
}
catch {
    Escrever "Não foi possível trocar os arquivos ($($_.Exception.Message)); voltando para a versão anterior."
    foreach ($nome in $trocados) {
        $alvo = Join-Path $Destino $nome
        $guardado = Join-Path $antigo $nome
        if (Test-Path -LiteralPath $guardado) {
            Remove-Item -LiteralPath $alvo -Recurse -Force -ErrorAction SilentlyContinue
            Move-Item -LiteralPath $guardado -Destination $alvo -Force -ErrorAction SilentlyContinue
        }
    }
}

try { Start-Process -FilePath $Programa -WorkingDirectory $Destino }
catch { Escrever "Não foi possível abrir o programa de novo ($($_.Exception.Message)). Abra o Puxai.exe." }
Start-Sleep -Seconds 3
Remove-Item -LiteralPath $preparo -Recurse -Force -ErrorAction SilentlyContinue
"""

SCRIPT_LINUX = r"""#!/bin/sh
processo=$1 nova=$2 destino=$3 programa=$4
preparo=$(dirname "$nova")
antigo="$preparo/antigo"
registro="$destino/Puxai.log"
escrever() { printf '[ATUALIZAÇÃO] %s\n' "$*" >> "$registro" 2>/dev/null; }

# Espera o Puxaí fechar (até 60 segundos)
espera=0
while kill -0 "$processo" 2>/dev/null && [ "$espera" -lt 120 ]; do sleep 0.5; espera=$((espera + 1)); done

trocados=""
falhou=""
mkdir -p "$antigo" || falhou=1
for item in "$nova"/* "$nova"/.[!.]*; do
    [ -z "$falhou" ] || break
    [ -e "$item" ] || continue
    nome=$(basename "$item")
    if [ -e "$destino/$nome" ]; then mv "$destino/$nome" "$antigo/$nome" || { falhou=1; break; }; fi
    trocados="$trocados
$nome"
    mv "$item" "$destino/$nome" || falhou=1
done

if [ -n "$falhou" ]; then
    escrever "Não foi possível trocar os arquivos; voltando para a versão anterior."
    printf '%s\n' "$trocados" | while IFS= read -r nome; do
        [ -n "$nome" ] && [ -e "$antigo/$nome" ] || continue
        rm -rf "$destino/$nome"
        mv "$antigo/$nome" "$destino/$nome"
    done
else
    rm -f "$destino"/atualizacoes/*
    escrever "Programa atualizado."
fi

cd "$destino" && nohup "$programa" >/dev/null 2>&1 &
sleep 3
rm -rf "$preparo"
"""
