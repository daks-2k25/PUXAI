#!/bin/sh
# Teste rápido do programa gerado para Linux (Puxai/Puxai), antes de publicar.
# O equivalente do testar_exe.ps1.
#
# Abre uma cópia do programa no modo navegador, confere se a API responde,
# converte e comprime uma imagem (prova que o FFmpeg incluído funciona) e
# fecha. Roda numa cópia da pasta, para o que o programa cria ao rodar (log,
# pasta downloads/) não ir junto no pacote.
#
# Uso: sh ferramentas/testar_linux.sh [pasta do programa] [porta]
# Também é usado pelo GitHub (.github/workflows/gerar-exe.yml).
PASTA=${1:-"$(cd "$(dirname "$0")/.." && pwd)/Puxai"}
PORTA=${2:-5097}
ENDERECO="http://127.0.0.1:$PORTA"
COPIA=$(mktemp -d)/Puxai
falhas=0
pid=""

conferir() {  # conferir NOME DETALHE COMANDO...
    nome=$1 detalhe=$2
    shift 2
    if "$@" >/dev/null 2>&1; then
        printf '  OK      %s %s\n' "$nome" "$detalhe"
    else
        printf '  FALHOU  %s %s\n' "$nome" "$detalhe"
        falhas=$((falhas + 1))
    fi
}

terminar() {
    [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null
    if [ "$falhas" -gt 0 ] && [ -f "$COPIA/registro.txt" ]; then
        printf '\n--- mensagens do programa ---\n'; tail -n 40 "$COPIA/registro.txt"
    fi
    rm -rf "$(dirname "$COPIA")"
    if [ "$falhas" -gt 0 ]; then printf '\n%s teste(s) falharam.\n' "$falhas"; exit 1; fi
    printf '\nTudo certo com o programa gerado.\n'
    exit 0
}

[ -x "$PASTA/Puxai" ] || { echo "Não achei $PASTA/Puxai"; falhas=1; terminar; }
echo "Copiando o programa para $COPIA..."
cp -a "$PASTA" "$COPIA"

conferir "ffmpeg incluído" "" test -x "$COPIA/ffmpeg"
conferir "ffprobe incluído" "" test -x "$COPIA/ffprobe"
conferir "deno incluído" "" test -x "$COPIA/deno"

# Tira do PATH o FFmpeg e o Deno instalados no PC: o teste só passa se os incluídos no programa funcionarem
PATH=$(printf '%s' "$PATH" | tr ':' '\n' | while read -r p; do
    [ -n "$p" ] && [ ! -e "$p/ffmpeg" ] && [ ! -e "$p/deno" ] && printf '%s:' "$p"
done)
export PATH="${PATH%:}"
conferir "sem FFmpeg instalado no PATH" "" sh -c '! command -v ffmpeg'

# Janela própria (Qt) numa tela virtual: prova que o Qt e o WebEngine vieram junto
if command -v xvfb-run >/dev/null 2>&1; then
    conferir "janela (Qt) abre" "" timeout 60 xvfb-run -a "$COPIA/Puxai" --testar-janela

    # Modo navegador com tela: o Qt fica rodando por causa do ícone da bandeja. A tela
    # virtual não tem área de ícones: o programa tem que perceber e seguir sem ele.
    PORTA=$PORTA PUXAI_MODO=navegador BROWSER=true timeout 120 xvfb-run -a "$COPIA/Puxai" > "$COPIA/registro-tela.txt" 2>&1 &
    pid=$!
    respondeu=""
    for _ in $(seq 90); do
        sleep 1
        if curl -sf "$ENDERECO/api/modo" -o /dev/null; then respondeu=1; break; fi
    done
    conferir "com tela: programa abre e responde (ícone da bandeja)" "" test -n "$respondeu"
    conferir "com tela: ícone da bandeja testado" "" grep -q "\[BANDEJA\]" "$COPIA/registro-tela.txt"
    curl -sf -X POST "$ENDERECO/api/encerrar" -o /dev/null
    fechou=""
    for _ in $(seq 15); do
        if ! kill -0 "$pid" 2>/dev/null; then fechou=1; break; fi
        sleep 1
    done
    conferir "com tela: programa fecha" "" test -n "$fechou"
    [ -n "$fechou" ] && pid=""
    cat "$COPIA/registro-tela.txt" >> "$COPIA/registro.txt"
fi

# Modo navegador, sem abrir navegador de verdade (o "navegador" é o comando true, que não faz nada)
PORTA=$PORTA PUXAI_MODO=navegador BROWSER=true "$COPIA/Puxai" >> "$COPIA/registro.txt" 2>&1 &
pid=$!

respondeu=""
for _ in $(seq 90); do
    sleep 1
    if curl -sf "$ENDERECO/api/qualidades" -o "$COPIA/qualidades.json"; then respondeu=1; break; fi
done
conferir "programa abriu e a API responde" "" test -n "$respondeu"
[ -n "$respondeu" ] || terminar
conferir "lista de qualidades" "" grep -q '"qualidades"' "$COPIA/qualidades.json"

versao=$(curl -sf "$ENDERECO/api/versao" | sed -n 's/.*"atual": *"\([^"]*\)".*/\1/p')
conferir "versão" "($versao)" test -n "$versao"
conferir "painel (index.html)" "" curl -sf "$ENDERECO/" -o /dev/null

# Uma imagem PNG de teste, feita pelo próprio FFmpeg incluído
imagem="$COPIA/teste.png"
"$COPIA/ffmpeg" -v error -y -f lavfi -i "testsrc2=s=320x240" -frames:v 1 "$imagem"
conferir "FFmpeg incluído roda" "" test -s "$imagem"

codigo=$(curl -s -o "$COPIA/teste.webp" -w "%{http_code}" -F "arquivo=@$imagem" -F "formato=webp" "$ENDERECO/api/converter/imagem")
conferir "converter PNG para WebP" "(HTTP $codigo)" sh -c "[ '$codigo' = 200 ] && [ -s '$COPIA/teste.webp' ]"

conferir "comprimir foto (usa o ffprobe)" "" sh -c "curl -s -F 'arquivo=@$imagem' -F 'nivel=forte' '$ENDERECO/api/comprimir' | grep -q ."

# Segurança: um pedido "de outro site" tem que ser recusado
codigo=$(curl -s -o /dev/null -w "%{http_code}" -H "Origin: https://site-ruim.com" -H "Sec-Fetch-Site: cross-site" "$ENDERECO/api/qualidades")
conferir "pedido de outro site recusado" "(HTTP $codigo)" test "$codigo" = 403

curl -sf -X POST "$ENDERECO/api/encerrar" -o /dev/null
fechou=""
for _ in $(seq 15); do
    if ! kill -0 "$pid" 2>/dev/null; then fechou=1; break; fi
    sleep 1
done
conferir "programa fechou" "" test -n "$fechou"
[ -n "$fechou" ] && pid=""

# Atualização automática: uma "Release" falsa (versão 9.9.9, com o mesmo programa)
# servida aqui. O programa baixa, fecha, troca os arquivos e abre já na versão nova.
echo "Testando a atualização automática..."
RELEASE="$(dirname "$COPIA")/release"
mkdir -p "$RELEASE/pacote"
cp -a "$PASTA" "$RELEASE/pacote/Puxai"
sed -i 's/"versao": *"[^"]*"/"versao": "9.9.9"/' "$RELEASE/pacote/Puxai/_internal/versao.json"
echo "veio na 9.9.9" > "$RELEASE/pacote/Puxai/novidade.txt"
XZ_OPT="-0 -T0" tar -cJf "$RELEASE/Puxai-linux.tar.xz" -C "$RELEASE/pacote" Puxai
printf '{"tag_name": "v9.9.9", "assets": [{"name": "Puxai-linux.tar.xz", "size": %s, "digest": "sha256:%s", "browser_download_url": "http://127.0.0.1:8766/Puxai-linux.tar.xz"}]}' \
    "$(stat -c %s "$RELEASE/Puxai-linux.tar.xz")" "$(sha256sum "$RELEASE/Puxai-linux.tar.xz" | cut -d' ' -f1)" > "$RELEASE/release.json"
python3 -m http.server 8766 --bind 127.0.0.1 --directory "$RELEASE" >/dev/null 2>&1 &
servidor=$!
echo '{"modo_abertura": "navegador"}' > "$COPIA/.preferencias.json"

PORTA=$PORTA PUXAI_MODO=navegador BROWSER=true PUXAI_URL_RELEASE=http://127.0.0.1:8766/release.json \
    "$COPIA/Puxai" >> "$COPIA/registro.txt" 2>&1 &
pid=$!
esperar_api() { for _ in $(seq 90); do sleep 1; curl -sf "$ENDERECO/api/modo" -o /dev/null && return 0; done; return 1; }
conferir "programa abriu (antes de atualizar)" "" esperar_api
conferir "versão nova encontrada" "" sh -c "curl -sf '$ENDERECO/api/versao?forcar=1' | grep -Eq '\"pode_atualizar\": *true'"
conferir "atualizar respondeu" "" sh -c "curl -sf -X POST '$ENDERECO/api/atualizar' | grep -q '9.9.9'"
fechou=""
for _ in $(seq 20); do
    if ! kill -0 "$pid" 2>/dev/null; then fechou=1; break; fi
    sleep 1
done
conferir "versão antiga fechou" "" test -n "$fechou"
[ -n "$fechou" ] && pid=""
conferir "abriu de novo sozinho" "" esperar_api
conferir "já na versão nova" "" sh -c "curl -sf '$ENDERECO/api/versao' | grep -Eq '\"atual\": *\"9.9.9\"'"
conferir "arquivo novo do pacote chegou" "" test -f "$COPIA/novidade.txt"
conferir "configurações continuaram" "" grep -q navegador "$COPIA/.preferencias.json"
sleep 4
conferir "pasta temporária apagada" "" test ! -e "$COPIA/.atualizacao"
curl -sf -X POST "$ENDERECO/api/encerrar" -o /dev/null
sleep 2
kill "$servidor" 2>/dev/null
pkill -f "$COPIA/Puxai" 2>/dev/null
terminar
