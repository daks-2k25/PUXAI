# Teste rápido do programa gerado (Puxai\Puxai.exe), antes de publicar.
#
# Abre uma cópia do programa no modo navegador, confere se a API responde,
# converte e comprime uma imagem (prova que o FFmpeg incluído funciona) e
# fecha. Roda numa cópia da pasta, para o que o programa cria ao rodar (log,
# pasta downloads\) não ir junto no .zip.
#
# Uso: powershell -File ferramentas\testar_exe.ps1 [-Pasta Puxai] [-Porta 5097]
# Também é usado pelo GitHub (.github\workflows\gerar-exe.yml).
param(
    [string]$Pasta = (Join-Path (Split-Path -Parent $PSScriptRoot) "Puxai"),
    [int]$Porta = 5097
)
$ErrorActionPreference = "Stop"

$copia = Join-Path ([IO.Path]::GetTempPath()) "puxai-teste-$PID"
$endereco = "http://127.0.0.1:$Porta"
$programa = $null
$falhas = 0

function Conferir($nome, $ok, $detalhe = "") {
    if ($ok) { Write-Host "  OK      $nome $detalhe" -ForegroundColor Green }
    else { Write-Host "  FALHOU  $nome $detalhe" -ForegroundColor Red; $script:falhas++ }
}

try {
    if (-not (Test-Path (Join-Path $Pasta "Puxai.exe"))) { throw "Não achei $Pasta\Puxai.exe" }
    Write-Host "Copiando o programa para $copia..."
    Copy-Item $Pasta $copia -Recurse

    Conferir "ffmpeg.exe incluído" (Test-Path "$copia\ffmpeg.exe")
    Conferir "ffprobe.exe incluído" (Test-Path "$copia\ffprobe.exe")

    # Tira do PATH o FFmpeg instalado no PC: o teste só passa se o incluído no programa funcionar
    $env:PATH = ($env:PATH -split ";" | Where-Object { $_ -and -not (Test-Path (Join-Path $_ "ffmpeg.exe")) }) -join ";"
    Conferir "sem FFmpeg instalado no PATH" (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue))

    # Modo navegador, sem abrir navegador de verdade (o "navegador" é um comando que não faz nada)
    $env:PORTA = "$Porta"
    $env:PUXAI_MODO = "navegador"
    $env:BROWSER = "cmd /c rem %s"
    $programa = Start-Process -FilePath "$copia\Puxai.exe" -WorkingDirectory $copia -PassThru

    $respondeu = $false
    for ($i = 0; $i -lt 90 -and -not $respondeu; $i++) {
        Start-Sleep -Seconds 1
        try { $qualidades = Invoke-RestMethod "$endereco/api/qualidades"; $respondeu = $true } catch { }
    }
    Conferir "programa abriu e a API responde" $respondeu
    if (-not $respondeu) { throw "O programa não respondeu em 90 segundos." }
    Conferir "lista de qualidades" ($qualidades.qualidades.Count -ge 4)

    $versao = Invoke-RestMethod "$endereco/api/versao"
    Conferir "versão" ([bool]$versao.atual) "($($versao.atual))"
    Conferir "painel (index.html)" ((Invoke-WebRequest "$endereco/" -UseBasicParsing).StatusCode -eq 200)

    # Uma imagem PNG de teste, feita pelo próprio FFmpeg incluído
    $imagem = Join-Path $copia "teste.png"
    & "$copia\ffmpeg.exe" -v error -y -f lavfi -i "testsrc2=s=320x240" -frames:v 1 $imagem
    Conferir "FFmpeg incluído roda" (Test-Path $imagem)

    $saida = Join-Path $copia "teste.webp"
    $codigo = & curl.exe -s -o $saida -w "%{http_code}" -F "arquivo=@$imagem" -F "formato=webp" "$endereco/api/converter/imagem"
    Conferir "converter PNG para WebP" ($codigo -eq "200" -and (Get-Item $saida).Length -gt 0) "(HTTP $codigo)"

    $resposta = & curl.exe -s -F "arquivo=@$imagem" -F "nivel=forte" "$endereco/api/comprimir"
    Conferir "comprimir foto (usa o ffprobe)" ($LASTEXITCODE -eq 0 -and $resposta.Length -gt 0)

    # Segurança: um pedido "de outro site" tem que ser recusado
    $codigo = & curl.exe -s -o NUL -w "%{http_code}" -H "Origin: https://site-ruim.com" -H "Sec-Fetch-Site: cross-site" "$endereco/api/qualidades"
    Conferir "pedido de outro site recusado" ($codigo -eq "403") "(HTTP $codigo)"

    Invoke-RestMethod "$endereco/api/encerrar" -Method Post | Out-Null
    $fechou = $programa.WaitForExit(15000)
    Conferir "programa fechou" $fechou

    # Atualização automática: uma "Release" falsa (versão 9.9.9, com o mesmo programa)
    # servida aqui. O programa baixa, fecha, troca os arquivos e abre já na versão nova.
    Write-Host "Testando a atualização automática..."
    $release = "$copia-release"
    New-Item -ItemType Directory "$release\pacote" | Out-Null
    Copy-Item $Pasta "$release\pacote\Puxai" -Recurse
    $arquivoVersao = "$release\pacote\Puxai\_internal\versao.json"
    (Get-Content $arquivoVersao -Raw -Encoding UTF8) -replace '"versao": *"[^"]*"', '"versao": "9.9.9"' | Set-Content $arquivoVersao -Encoding utf8
    "veio na 9.9.9" | Set-Content "$release\pacote\Puxai\novidade.txt"
    & tar.exe -a -c -f "$release\Puxai-windows.zip" -C "$release\pacote" Puxai
    $zip = Get-Item "$release\Puxai-windows.zip"
    @{ tag_name = "v9.9.9"; assets = @(@{ name = "Puxai-windows.zip"; size = $zip.Length
       digest = "sha256:" + (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
       browser_download_url = "http://127.0.0.1:8766/Puxai-windows.zip" }) } | ConvertTo-Json -Depth 4 | Set-Content "$release\release.json"
    $servidor = Start-Process python -ArgumentList "-m", "http.server", "8766", "--bind", "127.0.0.1", "--directory", $release -PassThru -WindowStyle Hidden
    '{"modo_abertura": "navegador"}' | Set-Content "$copia\.preferencias.json"

    $env:PUXAI_MODO = "navegador"
    $env:PUXAI_URL_RELEASE = "http://127.0.0.1:8766/release.json"
    $programa = Start-Process -FilePath "$copia\Puxai.exe" -WorkingDirectory $copia -PassThru
    function Esperar-Api { for ($i = 0; $i -lt 90; $i++) { try { Invoke-RestMethod "$endereco/api/modo" -TimeoutSec 2 | Out-Null; return $true } catch { Start-Sleep 1 } }; return $false }
    Conferir "programa abriu (antes de atualizar)" (Esperar-Api)
    $v = Invoke-RestMethod "$endereco/api/versao?forcar=1"
    Conferir "versão nova encontrada" ($v.pode_atualizar -and $v.nova -eq "9.9.9") "$($v.motivo)"
    $resposta = Invoke-RestMethod "$endereco/api/atualizar" -Method Post -TimeoutSec 300
    Conferir "atualizar respondeu" ($resposta.versao -eq "9.9.9")
    Conferir "versão antiga fechou" ($programa.WaitForExit(20000))
    Conferir "abriu de novo sozinho" (Esperar-Api)
    $v = Invoke-RestMethod "$endereco/api/versao"
    Conferir "já na versão nova" ($v.atual -eq "9.9.9") "($($v.atual))"
    Conferir "arquivo novo do pacote chegou" (Test-Path "$copia\novidade.txt")
    Conferir "configurações continuaram" ((Get-Content "$copia\.preferencias.json" -Raw) -match "navegador")
    Start-Sleep 5
    Conferir "pasta temporária apagada" (-not (Test-Path "$copia\.atualizacao"))
    Invoke-RestMethod "$endereco/api/encerrar" -Method Post | Out-Null
    Start-Sleep 2
}
catch {
    Write-Host "  ERRO    $($_.Exception.Message)" -ForegroundColor Red
    $falhas++
}
finally {
    if ($programa -and -not $programa.HasExited) { Stop-Process -Id $programa.Id -Force }
    # A versão reaberta pela atualização (outro processo) e o servidor da Release falsa
    Get-Process Puxai -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$copia*" } | Stop-Process -Force
    if ($servidor) { Stop-Process -Id $servidor.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item "$copia-release" -Recurse -Force -ErrorAction SilentlyContinue
    if ($falhas -and (Test-Path "$copia\Puxai.log")) {
        Write-Host "`n--- Puxai.log ---"; Get-Content "$copia\Puxai.log" -Tail 40
    }
    Start-Sleep -Seconds 1
    Remove-Item $copia -Recurse -Force -ErrorAction SilentlyContinue
}

if ($falhas) { Write-Host "`n$falhas teste(s) falharam." -ForegroundColor Red; exit 1 }
Write-Host "`nTudo certo com o programa gerado." -ForegroundColor Green
exit 0
