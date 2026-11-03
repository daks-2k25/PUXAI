# Puxaí

Programa para **Windows** e **Linux** que baixa vídeos do **YouTube**, **TikTok**, **Instagram** e de mais de mil sites em **MP4** ou extrai o áudio em **MP3**, além de converter e comprimir fotos e vídeos. Abre numa **janela própria**, com uma **API REST** por trás, feita em Python com Flask e [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## ⬇ Baixar o Puxaí (Windows)

### **[Clique aqui para baixar o Puxaí](https://github.com/daks-2k25/API-BAIXAR-YOUTUBE/releases/latest/download/Puxai-windows.zip)**

Esse link baixa sempre a **versão mais nova**. Não precisa ter conta no GitHub.

1. **Baixe** pelo link acima (o arquivo **Puxai-windows.zip**, cerca de 100 MB).
2. Clique com o botão direito no arquivo baixado e escolha **Extrair tudo**.
3. Abra a pasta **Puxai** e dê dois cliques em **Puxai.exe**. Não precisa instalar nada (nem Python, nem FFmpeg: tudo vem junto).
4. Se o Windows mostrar **"O Windows protegeu o computador"**, clique em **Mais informações → Executar assim mesmo**. O aviso aparece porque o programa não tem assinatura digital (que é paga), não porque tenha algo errado.

**Dica:** clique com o botão direito no **Puxai.exe** → **Enviar para → Área de trabalho (criar atalho)**, para abrir pela Área de Trabalho.

**Para atualizar:** o Puxaí avisa quando sai uma versão nova. Clique em **Atualizar agora**: ele baixa a versão nova, fecha, troca os arquivos e abre de novo sozinho. Suas configurações e o histórico continuam. (Quem tem a versão 2.3.0 ou anterior precisa baixar a versão nova pelo link uma última vez e extrair **por cima** da pasta antiga; daí em diante, atualiza sozinho.)

## ⬇ Baixar o Puxaí (Linux)

### **[Clique aqui para baixar o Puxaí para Linux](https://github.com/daks-2k25/API-BAIXAR-YOUTUBE/releases/latest/download/Puxai-linux.tar.xz)**

Para PCs de 64 bits (x86_64) com Ubuntu 22.04, Debian 12, Fedora 37, Linux Mint 21 ou mais novos.

1. **Baixe** pelo link acima (o arquivo **Puxai-linux.tar.xz**).
2. Clique com o botão direito no arquivo baixado e escolha **Extrair aqui** (ou, no terminal: `tar -xJf Puxai-linux.tar.xz`).
3. Abra a pasta **Puxai** e dê dois cliques em **Puxai** (ou rode `./Puxai/Puxai`). Não precisa instalar nada: o FFmpeg e o Deno vêm junto.
4. Na primeira vez, o Puxaí cria o atalho **Puxaí** no **menu de aplicativos**. Depois é só abrir por ele.

**Para atualizar:** como no Windows, pelo botão **Atualizar agora** (na versão 2.3.0, baixe de novo pelo link e extraia **por cima** da pasta antiga).

As novidades de cada versão ficam na página [**Releases**](https://github.com/daks-2k25/API-BAIXAR-YOUTUBE/releases).

## Início rápido pelo código (Windows)

1. Baixe o projeto: **Code → Download ZIP** no GitHub (e descompacte) ou `git clone https://github.com/daks-2k25/API-BAIXAR-YOUTUBE.git`.
2. Dê dois cliques em **`iniciar.bat`**.

Pronto. **Na primeira vez**, ele instala sozinho o que estiver faltando no PC:

- **uv**: cuida do Python e das bibliotecas. Usa o Python que já estiver no PC ou baixa um, sem instalar nada no Windows
- **FFmpeg**: junta vídeo e áudio, gera MP3 e converte as fotos
- **Deno**: o yt-dlp usa para ler o YouTube

O uv, o FFmpeg e o Deno vêm pelo winget, que já vem no Windows 10 e 11. Isso leva alguns minutos e mostra o andamento numa janela. **Nas próximas vezes**, ele vê que está tudo pronto e abre o programa em cerca de 2 segundos.

No primeiro clique ele também cria o atalho **Puxaí**, com a logo, na **Área de Trabalho** (quem já tinha o atalho antigo, **Baixar YouTube**, tem ele renomeado sozinho). Depois é só usar o atalho. Se você apagar o atalho, ele não é criado de novo; se mover a pasta do projeto, o atalho é corrigido no próximo uso do `iniciar.bat`. O yt-dlp é atualizado automaticamente uma vez por dia, porque o YouTube muda com frequência.

> Se o Windows mostrar "O Windows protegeu o computador" ao abrir o `iniciar.bat` baixado da internet, clique em **Mais informações → Executar assim mesmo**.

## Início rápido pelo código (Linux)

1. Baixe o projeto (`git clone https://github.com/daks-2k25/API-BAIXAR-YOUTUBE.git` ou **Code → Download ZIP**).
2. Abra um terminal na pasta do projeto e rode **`sh iniciar.sh`**.

**Na primeira vez**, ele prepara sozinho o que faltar, **sem pedir senha** (nada é instalado no sistema): o **uv** (em `~/.local/bin`), o Python e as bibliotecas (na pasta `.ambiente`, incluindo o Deno e a janela do programa, que usa o Qt) e, se o sistema não tiver o FFmpeg, um FFmpeg pronto (na pasta `.ffmpeg`, cerca de 150 MB, conferido pelo SHA-256). Precisa do `curl` ou do `wget`. Depois, o Puxaí cria o atalho **Puxaí** no menu de aplicativos, que roda o mesmo `iniciar.sh`; se a pasta do projeto mudar de lugar, o atalho é corrigido no próximo uso. As mensagens ficam no `Puxai.log`.

No Linux, o programa funciona igual ao do Windows, com estas diferenças:

- **Janela própria:** usa o Qt. Se ela não abrir (ex.: PC sem tela, ou faltando uma biblioteca do sistema), o painel abre no navegador. No Ubuntu/Debian com X11, a falta mais comum é a `libxcb-cursor0`: `sudo apt install libxcb-cursor0`. O motivo fica no `Puxai.log`.
- **Link copiado:** o Puxaí lê a área de transferência pelo `xclip`, `xsel` ou `wl-paste` (o primeiro que estiver instalado). Sem nenhum deles, o aviso de link copiado não aparece: `sudo apt install xclip` (ou `wl-clipboard`, no Wayland).
- **Escolher pasta:** usa a janela do sistema (zenity no GNOME, kdialog no KDE).
- **Abrir** e **Mostrar na pasta** usam o programa padrão do sistema e o gerenciador de arquivos (Arquivos, Dolphin, Nemo, Thunar...).
- **Tema automático:** segue o modo escuro do GNOME ou do KDE.
- **Ícone perto do relógio:** igual ao do Windows (abrir, abrir no navegador, abrir a pasta e encerrar). Aparece no KDE, XFCE, Cinnamon, MATE, Budgie e no Ubuntu. No GNOME puro (ex.: Fedora, Debian), a área de ícones só existe com a extensão **AppIndicator** (pacote `gnome-shell-extension-appindicator`); sem ela, o Puxaí segue sem o ícone. Nesse caso, no modo navegador, feche pelo botão **Encerrar** do painel (ou ele fecha sozinho 3 minutos depois que nenhuma aba estiver aberta).

## Extensão do navegador: "Baixar com o Puxaí"

Com a extensão, não precisa copiar e colar o link: num vídeo aberto no navegador, um clique manda ele para a fila do Puxaí. Funciona no **Chrome, Edge, Brave, Opera** e **Firefox**. O Puxaí precisa estar aberto (a extensão avisa se não estiver).

- **Botão da extensão** (na barra do navegador): mostra o vídeo da aba, com **Baixar MP4** (e a qualidade) e **Baixar MP3**.
- **Botão direito** num link, num vídeo ou na página: **Baixar vídeo com o Puxaí (MP4)** ou **Baixar MP3 com o Puxaí**.
- **Atalhos:** **Alt+Shift+P** (MP4) e **Alt+Shift+M** (MP3) baixam o vídeo da aba aberta. Dá para trocar em `chrome://extensions/shortcuts`.
- Uma notificação confirma que entrou na fila, e o download aparece sozinho na lista do Puxaí. O arquivo vai para a pasta escolhida no Puxaí.

**Instalar no Chrome, Edge, Brave ou Opera:**

1. Baixe o **[Puxai-extensao.zip](https://github.com/daks-2k25/API-BAIXAR-YOUTUBE/releases/latest/download/Puxai-extensao.zip)** e extraia numa pasta que você não vá apagar (ou use a pasta `extensao/` do projeto).
2. Abra `chrome://extensions` (no Edge, `edge://extensions`), ligue o **Modo do desenvolvedor** e clique em **Carregar sem compactação**. Escolha a pasta.
3. Clique no ícone de quebra-cabeça da barra e fixe o **Baixar com o Puxaí**.

**No Firefox:** abra `about:debugging#/runtime/this-firefox`, clique em **Carregar extensão temporária** e escolha o `manifest.json` da pasta. Nesse modo, o Firefox tira a extensão quando fecha. Para ficar instalada de vez, ela precisa ser publicada na loja do Firefox (grátis).

**Segurança:** a extensão só consegue usar as rotas `/api/extensao/...` do Puxaí (pôr um link na fila, ver se o programa está aberto e trazê-lo para a frente). O resto da API (encerrar, atualizar, pastas, preferências...) continua só para o painel. Um site comum não consegue se passar pela extensão. A extensão não coleta nem envia dados para lugar nenhum: só fala com o Puxaí, no seu computador.

## Funcionalidades

- **Janela própria ou navegador**: abre como aplicativo (fechar a janela fecha o programa) ou, se preferir, no navegador. Dá para escolher em **⚙ Configurações**
- **Atualização pelo próprio programa**: quando sai uma versão nova, aparece um aviso com as novidades e o botão **Atualizar agora**
- **Notificações**: sino 🔔 com bolinha quando há versão nova, notificação no canto da janela e verificação automática a cada 30 minutos com o programa aberto
- **Prévia do vídeo** ao colar o link: miniatura, título, canal e duração, com opção de assistir ali mesmo para conferir antes de baixar
- **YouTube, TikTok, Instagram e mais de mil sites**: X (Twitter), Facebook, Twitch, SoundCloud, Dailymotion, Vimeo, Reddit, Pinterest, Bilibili, Bandcamp, 9GAG e todos os outros que o [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) conhece. É só colar o link
- Download de vídeo em **MP4** com **escolha de resolução** (360p, 480p, 720p ou 1080p), inclusive em vídeos verticais (TikTok, Reels, Shorts). No TikTok, sempre a versão **sem marca d'água**
- Extração de áudio em **MP3** (192 kbps) com **capa e informações**: a miniatura do vídeo vira a capa (quadrada, como a de um álbum), e o MP3 leva título, artista, álbum (quando o YouTube informa) e ano, para aparecer certinho no player e no celular. O título sai sem o artista na frente e sem "(Official Video)", "[Lyrics]" e parecidos; no comentário vai o link do vídeo
- **Até 3 downloads ao mesmo tempo**, com acompanhamento de progresso
- **Extensão do navegador** ("Baixar com o Puxaí"): manda o vídeo da página para o Puxaí com um clique, pelo botão da extensão, pelo botão direito ou por atalho de teclado
- **Relatório de erro com um clique**: num download que deu erro (ou em Configurações), **⚠ Relatar problema** monta um relatório sem dados pessoais, que a pessoa confere e envia pelo GitHub, por e-mail ou copia
- **Fila que não se perde**: se o programa (ou o PC) fechar no meio, os downloads que não terminaram voltam para a fila na próxima vez que ele abrir, e continuam de onde pararam
- **Nova tentativa automática** quando o YouTube falha momentaneamente
- **Playlists e canais**: cole o link e aparece a lista de vídeos (até 200) com caixinhas para marcar quais baixar. Os arquivos podem ir para uma pasta com o nome da playlist, numerados na ordem (`01 - Título`), bom para álbuns. Se o link for de um vídeo aberto dentro de uma playlist, o painel pergunta: **Usar só este vídeo** ou **Baixar a playlist**
- **Vários links de uma vez**: cole uma lista de links (até 200) e todos entram na fila, na ordem
- **Cancelar todos**: com 2 ou mais downloads em andamento, um botão cancela todos de uma vez
- **Salva direto na pasta Downloads** (ou na pasta que você escolher: uma para tudo ou uma para vídeos, outra para músicas e outra para fotos), com o **título do vídeo** no nome (sem sobrescrever arquivos que já existem)
- **Cortar um trecho**: baixa só o pedaço escolhido (ex.: de 1:20 a 2:05), cortado no segundo exato
- **Cancelar** downloads na fila ou em andamento
- **Conversão de fotos**: HEIC para JPG, e HEIC, JPG ou PNG para WebP (bem menor, mantém a transparência do PNG), salvo direto em Downloads
- **Compressor de fotos**: JPG, PNG, WebP e HEIC, uma ou várias de uma vez. Testa algumas qualidades em cada foto e fica com o menor arquivo que continua visualmente igual (medido pelo SSIM), em três níveis. Nunca deixa o arquivo maior, corrige a orientação das fotos de celular, remove a localização (GPS) e pode reduzir o tamanho (2560, 1920 ou 1280 px)
- **Compressor de vídeos**: MP4, MOV, MKV, WebM, AVI e outros viram MP4 (H.264), que abre em qualquer lugar. Para **caber num tamanho** (WhatsApp 16 MB, Discord 10 MB, E-mail 25 MB ou outro), em duas passadas e reduzindo a resolução sozinho quando o vídeo é longo; ou por **qualidade** (alta, equilibrada ou máxima compressão). Resolução máxima opcional (1080p, 720p, 480p), andamento em %, cancelar no meio e vídeos de celular continuam em pé. Nunca deixa o arquivo maior
- **Meus downloads**: lista do que o programa já salvou (vídeos, músicas e fotos), com filtros, **Abrir** e **Mostrar na pasta**, mesmo depois de fechar e abrir o programa
- **Programa pronto para Windows e Linux**, que não precisa de Python instalado e mantém o yt-dlp atualizado sozinho

## Usando o programa

- **Baixar:** cole o link do vídeo (YouTube, TikTok, Instagram ou outro site) e confira a prévia do vídeo (no YouTube, clique na miniatura para assistir ali mesmo). Escolha MP4 ou MP3 e a resolução, e clique em **Baixar agora**. O arquivo é salvo na sua pasta **Downloads**; o botão **Mostrar na pasta** abre o Explorador com ele selecionado.
- **Vários links:** cole vários links de uma vez no campo (o painel percebe e abre uma caixa com um link por linha) ou clique em **+ Colar vários links de uma vez**. Os links podem estar um por linha, separados por espaço ou no meio de outro texto; repetidos contam uma vez só (inclusive o mesmo vídeo do YouTube escrito de jeitos diferentes). O formato e a qualidade escolhidos valem para todos. Vídeo aberto dentro de uma playlist baixa só o vídeo; o link de uma playlist inteira precisa ser colado sozinho, para escolher os vídeos.
- **Link copiado:** copiou o link de um vídeo (no navegador, no WhatsApp...) e voltou para o Puxaí? Aparece **"Você copiou um link do YouTube"** com o botão **Colar**. Funciona com qualquer site que o yt-dlp baixa (YouTube, TikTok, Instagram, X, Vimeo, Reddit, Facebook...), mesmo com o link no meio de uma mensagem. O **✕** dispensa aquele link (ele não é oferecido de novo). O Puxaí só olha o que está copiado quando você abre ou volta para ele, com o campo de link vazio, e só usa o texto se for um link de vídeo: qualquer outra coisa copiada é ignorada e não fica guardada. Para desligar: **⚙ Configurações → Avisar quando eu copiar um link de vídeo**.
- **Cortar trecho:** clique em **✂ Cortar trecho** e preencha o início e o fim (ex.: `1:20` e `2:05`). Deixe o fim vazio para ir até o final do vídeo.
- **Cancelar:** cada download tem um botão **✕ Cancelar** enquanto está na fila ou baixando.
- **Converter foto:** escolha **JPG** (a partir de HEIC) ou **WebP** (a partir de HEIC, JPG ou PNG), depois arraste uma ou várias fotos (ou clique para escolher). Elas são convertidas uma de cada vez, cada uma aparece na lista com o resultado, e as convertidas vão para a pasta Downloads. Se uma foto não for aceita (ex.: PNG para JPG), só ela mostra o erro e as outras continuam.
- **Comprimir foto:** escolha o nível (**Alta qualidade**, **Equilibrado** ou **Máxima compressão**) e, se quiser, um tamanho máximo, e arraste uma ou várias fotos. Cada foto aparece com o tamanho antes e depois, e a versão comprimida vai para Downloads com "(comprimida)" no nome. JPG, PNG e WebP continuam no mesmo formato; HEIC vira JPG. Se a foto já estiver bem comprimida, nada é salvo.
- **Comprimir vídeo:** escolha **Caber num tamanho** (WhatsApp, Discord, E-mail ou **Outro**, em MB) ou **Escolher a qualidade**, e, se quiser, uma resolução máxima. Arraste um ou vários vídeos: eles são comprimidos um de cada vez, com o andamento em % e o botão **✕ Cancelar**. O vídeo comprimido vai para a pasta de vídeos com "(comprimido)" no nome. Leva mais ou menos metade do tempo do vídeo (um vídeo de 3 minutos em 1080p fica pronto em cerca de 1 minuto para o WhatsApp). Se o vídeo já couber no tamanho, ou já estiver bem comprimido (como os baixados do YouTube), nada é salvo. Se for longo demais para o tamanho escolhido, o programa avisa.
- **Meus downloads:** mostra tudo o que o programa salvou, do mais novo para o mais antigo, com data e tamanho. Filtre por **Vídeos**, **Músicas** ou **Fotos**, e use **Abrir** (abre no player ou visualizador do Windows) ou **Mostrar na pasta**. **Remover da lista** e **Limpar lista** só tiram da lista: os arquivos continuam na pasta Downloads. Se um arquivo foi apagado ou movido, ele aparece riscado.
- **Atualizar:** quando sair uma versão nova, aparece uma notificação no canto da janela, um aviso no topo e uma bolinha no sino 🔔. Clique em **Atualizar agora**: o programa baixa a versão nova, reinicia sozinho e continua com seus arquivos e configurações. Com o programa aberto, ele confere se saiu versão nova a cada 30 minutos. A versão instalada aparece no rodapé.
- **Depois:** se preferir atualizar mais tarde, clique em **Depois**. A notificação não volta para essa versão (o sino continua com a bolinha, e a atualização fica disponível nele). Se sair uma versão ainda mais nova, o programa avisa de novo.
- **Sino 🔔:** mostra a atualização disponível ou confirma que você está na versão mais recente, com o botão **Verificar agora**.
- **Para fechar:** feche a janela. Se ainda houver download em andamento, o programa pergunta antes.
- **Ícone perto do relógio (bandeja do Windows e do Linux):** enquanto o Puxaí está aberto, o ícone dele fica ali. **Clique** para abrir (traz a janela para a frente, ou abre o painel no navegador); com o **botão direito**, o menu tem **Abrir o Puxaí**, **Abrir no navegador**, **Abrir a pasta dos arquivos** e **Encerrar o Puxaí** (que pergunta antes se ainda há downloads ou compressões em andamento). Parando o mouse em cima, aparece quantos itens estão em andamento. No modo navegador, é o jeito mais fácil de fechar o programa. Se o ícone estiver escondido, ele fica na setinha **^** ao lado do relógio.
- **Relatar um problema:** num download que deu erro, clique em **⚠ Relatar problema** (para outros problemas: **⚙ Configurações → Algo deu errado? Relatar um problema**). Abre uma janela com o relatório pronto: versões do Puxaí, do yt-dlp e do FFmpeg, o sistema, o site e o erro do download, e as últimas linhas de erro do `Puxai.log`. Ele sai **sem dados pessoais**: o nome de usuário e as pastas viram `~`, os links ficam só com o site (ex.: `youtube.com`) e e-mails e o código dos vídeos são tirados. Dá para escrever o que aconteceu e apagar o que quiser do texto antes de enviar. **Enviar pelo GitHub** abre a página de novo *Issue* já preenchida (precisa de conta, grátis); **Enviar por e-mail** abre o programa de e-mail (aparece quando o e-mail de suporte estiver configurado em `servicos/relatorio.py`, `EMAIL_SUPORTE`); **Copiar** põe o texto na área de transferência, para mandar por WhatsApp, por exemplo.
- **Fechou no meio de um download?** Na próxima vez que o Puxaí abrir, os downloads que estavam na fila ou baixando voltam sozinhos, e continuam de onde pararam (o que já tinha sido baixado não se perde). Um aviso no painel diz quantos voltaram. Os que você cancelou não voltam. A fila fica guardada no arquivo `.fila.json`, ao lado do programa.
- **Arquivos temporários:** se o programa fechar no meio de uma compressão, os arquivos incompletos são apagados (na hora, ou na próxima vez que ele abrir). As compressões de vídeo não voltam sozinhas: envie o vídeo de novo.
- **Tema claro ou escuro:** em **⚙ Configurações**, em **Tema**, escolha **Automático** (segue o modo claro/escuro do Windows, inclusive se ele mudar com o Puxaí aberto), **☀ Claro** ou **☾ Escuro**. Vale para o painel no navegador e para a janela do aplicativo (a barra de título também fica escura).
- **Onde salvar:** em **⚙ Configurações**, em **Salvar os arquivos em**, escolha **Uma pasta para tudo** ou **Pastas separadas** (Vídeos, Músicas e Fotos). Clique em **Escolher…** para abrir a janela do Windows e escolher a pasta; **Usar Downloads** volta para a pasta Downloads. Se a pasta escolhida não estiver disponível (ex.: HD externo desconectado), o arquivo vai para Downloads.
- **Janela ou navegador:** em **⚙ Configurações** (ao lado do sino), escolha se o programa abre na **Janela do aplicativo** ou no **Navegador**. A escolha fica salva para as próximas vezes. Para trocar na hora:
  - Na janela, o botão **↗** (ou **Abrir no navegador agora**, nas Configurações) abre o painel no navegador e fecha a janela; o programa continua rodando.
  - No navegador, **Reabrir como aplicativo** (nas Configurações) reinicia o programa na janela.
  - No navegador, o programa fecha pelo botão **Encerrar programa** ou sozinho, 3 minutos depois de fechar todas as abas (se não houver downloads).

Se clicar no atalho com o programa já aberto, ele só traz a janela para a frente (ou abre o painel no navegador, se estiver nesse modo). As mensagens do programa ficam no arquivo `Puxai.log`, útil se algo der errado. Se a janela própria não puder ser criada no PC (ex.: sem o componente WebView2 do Windows), o painel abre no navegador, como alternativa.

### Outros sites

Funciona com qualquer site da [lista do yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md): é só colar o link do vídeo (o do próprio vídeo, não o do perfil ou da página inicial). A prévia mostra o nome do site, e o aviso de **link copiado** também reconhece todos eles.

Testados na prática: YouTube, TikTok, Instagram, Twitch, SoundCloud, Dailymotion, Bandcamp, Streamable, Pinterest, Bilibili, Internet Archive, Imgur, 9GAG e Mixcloud.

Alguns sites mudam com frequência ou bloqueiam programas; quando algo falha, o Puxaí diz o motivo (vídeo privado, post sem vídeo, site fora do ar, site que mudou...). O yt-dlp é atualizado sozinho, então um site que parou de funcionar costuma voltar em poucos dias. Sites que bloqueiam quem não é navegador são acessados se passando por um navegador (o pacote `curl_cffi`, que já vem junto).

### Vídeos que pedem login (Instagram, Reddit, Vimeo, restrição de idade...)

Vídeos **públicos** baixam sem login. Alguns sites (ou posts) só abrem com uma conta logada: posts do Instagram, o Reddit, o Vimeo, vídeos do YouTube com restrição de idade... O programa avisa quando é o caso. Para usar o seu login:

1. No Chrome, logado no site, instale a extensão **Get cookies.txt LOCALLY**.
2. Abra o site, clique na extensão e exporte os cookies.
3. Salve o arquivo com o nome **`cookies.txt`** na pasta do programa (ao lado do `iniciar.bat`, ou dentro de `Puxai\` no programa gerado).

O programa passa a usar esse login automaticamente, em todos os sites (dá para exportar os cookies de vários sites no mesmo arquivo). O `cookies.txt` dá acesso às suas contas: não compartilhe esse arquivo. Ele não vai para o Git e o botão de atualizar não mexe nele.

> O yt-dlp não consegue ler os cookies do Chrome direto no Windows (o Chrome protege esses dados), por isso o caminho é exportar o arquivo. No Instagram, os vídeos são baixados; fotos de posts não.

### Como a atualização funciona

- **Projeto baixado como ZIP:** o programa baixa o ZIP novo do GitHub e substitui os arquivos do projeto. A pasta `downloads`, o ambiente do Python (`.ambiente`), os logs e o atalho não são tocados. Arquivos que saíram do projeto na versão nova são apagados.
- **Projeto clonado com git:** o programa roda `git pull`, mas só se a pasta estiver na branch `main` e sem alterações locais no código. Assim, quem está desenvolvendo não tem o trabalho sobrescrito.
- **Programa gerado (`Puxai.exe` ou o do Linux):** a versão nova é a da última **Release** (o aviso só aparece quando o arquivo para o seu sistema já está publicado). O botão baixa o `Puxai-windows.zip` (ou `Puxai-linux.tar.xz`), confere o SHA-256 que o GitHub publica para ele e extrai na pasta `.atualizacao`, ao lado do programa. Como um programa aberto não consegue trocar os próprios arquivos, um script pequeno (PowerShell no Windows, `sh` no Linux) espera o Puxaí fechar, põe os arquivos novos no lugar e abre o programa de novo. Se algo falhar no meio (ex.: um antivírus segurando um arquivo), ele volta os arquivos antigos e anota o motivo no `Puxai.log`. Configurações, histórico, cookies e logs não vêm no pacote, então continuam. Se a pasta do programa não aceitar arquivos novos (ex.: em *Arquivos de Programas*), o aviso explica como atualizar à mão.

## Publicando uma versão nova

1. Faça as mudanças e aumente o número em **`versao.json`** (ex.: de `2.0.0` para `2.1.0`), escrevendo as novidades na lista `novidades`. É esse texto que aparece no aviso para os usuários.
2. Suba para a branch `main` do GitHub.

Na próxima vez que alguém abrir o programa, o aviso de atualização aparece.

## Estrutura do projeto

```
API-BAIXAR-YOUTUBE/
├── iniciar.bat          # Dois cliques: prepara tudo e abre o programa
├── iniciar.sh           # O mesmo, no Linux ("sh iniciar.sh")
├── app.py               # Início do programa: liga o servidor e abre a janela ou o navegador
├── versao.json          # Versão do programa e novidades (usado na atualização)
├── pyproject.toml       # Bibliotecas do Python (usado pelo uv)
├── extensao/            # Extensão do navegador "Baixar com o Puxaí" (Chrome, Edge, Firefox...)
│   ├── manifest.json    # Nome, permissões, atalhos de teclado
│   ├── fundo.js         # Fala com o Puxaí; menu do botão direito e atalhos
│   └── janela.html/.css/.js # Janelinha do botão da barra
├── painel/              # Painel (index.html, style.css, script.js)
│                        # + logo.webp, favicon.svg, icone.ico e icone.png (ícone do programa)
├── rotas/               # Endereços da API (/api/...), um arquivo por área
│   ├── __init__.py      # Cria o app Flask e registra todas as rotas
│   ├── seguranca.py     # Só o painel pode usar a API (bloqueia pedidos de outros sites)
│   ├── videos.py        # Baixar, prévia, qualidades, progresso e cancelar
│   ├── fotos.py         # Converter e comprimir fotos
│   ├── arquivos.py      # Mostrar na pasta, abrir e "Meus downloads"
│   ├── programa.py      # Janela ou navegador, preferências, encerrar
│   ├── atualizacao.py   # Versão nova e "Atualizar agora"
│   ├── extensao.py      # As rotas que a extensão do navegador pode usar
│   ├── relatorio.py     # "Relatar problema": montar o relatório e abrir o GitHub ou o e-mail
│   └── utilidades.py    # O que as rotas compartilham (arquivos enviados, salvar em Downloads)
├── servicos/            # O que o programa faz (as rotas só chamam estes arquivos)
│   ├── programa.py      # Porta, uma instância só, reiniciar, encerrar e estado da janela
│   ├── janela.py        # Janela própria (pywebview: WebView2 no Windows, Qt no Linux) e ícone na barra de tarefas
│   ├── sistema.py       # O que muda entre Windows e Linux: abrir arquivo, mostrar na pasta
│   ├── atalho.py        # Linux: atalho "Puxaí" no menu de aplicativos
│   ├── bandeja.py       # Ícone perto do relógio, com menu (feito direto com o Windows, sem biblioteca; só no Windows)
│   ├── bandeja_linux.py # O mesmo ícone no Linux, com o Qt (que já vem junto para a janela)
│   ├── relatorio.py     # Relatório de erro sem dados pessoais (e o e-mail de suporte, EMAIL_SUPORTE)
│   ├── area_de_transferencia.py # Link de vídeo copiado (o painel oferece "Colar")
│   ├── caminhos.py      # Pastas do projeto e pasta Downloads do usuário
│   ├── preferencias.py  # Preferências salvas (.preferencias.json): modo de abertura, pastas, atualização adiada
│   ├── destinos.py      # Onde salvar os arquivos (uma pasta ou separadas) e a janela de escolher pasta
│   ├── historico.py     # Aba "Meus downloads": o que o programa salvou (.historico.json)
│   ├── compressor.py    # Aba "Comprimir foto": menor arquivo sem perda visível (FFmpeg + SSIM)
│   ├── compressor_video.py # Aba "Comprimir vídeo": caber num tamanho (2 passadas) ou por qualidade
│   ├── autoatualizacao.py # Botão "Atualizar agora": baixa e instala a versão nova
│   ├── atualizacao_do_programa.py # O mesmo no programa gerado: baixa a Release e troca os arquivos
│   ├── atualizador.py   # Mantém o yt-dlp atualizado dentro do executável
│   ├── downloader.py    # Fila de downloads, corte de trecho e cancelamento (yt-dlp)
│   ├── informacoes.py   # Prévia do vídeo (título, canal, duração, miniatura)
│   ├── sites.py         # O que é comum aos sites (nomes, títulos, login, mensagens de erro)
│   └── conversor.py     # Conversão de fotos: HEIC -> JPG e HEIC/JPG/PNG -> WebP (FFmpeg)
├── logos/               # Identidade visual: logo e ícones em SVG, PNG e WebP
├── ferramentas/
│   ├── iniciar.ps1      # Usado pelo iniciar.bat: instala o que faltar, cria o atalho e abre o programa
│   ├── gerar_exe.bat    # Gera o executável (PyInstaller), com o FFmpeg junto
│   ├── testar_exe.ps1   # Testa o executável gerado (usado também pelo GitHub)
│   ├── gerar_linux.sh   # O mesmo para o Linux, com o FFmpeg e o Deno junto
│   └── testar_linux.sh  # Testa o programa gerado para Linux (usado também pelo GitHub)
├── .github/workflows/
│   └── gerar-exe.yml    # Gera e publica o programa (Windows e Linux) numa Release quando a versão muda
└── README.md
```

Ao rodar, a aplicação cria a pasta `.ambiente/` (Python e bibliotecas, preparada pelo uv), a pasta `downloads/` (arquivos temporários enquanto baixa; os prontos vão para a pasta Downloads do usuário) e o `Puxai.log`. No Linux, o `iniciar.sh` pode criar a pasta `.ffmpeg/`. O `gerar_exe.bat` cria a pasta `Puxai/` e o atalho `Puxaí.lnk`. Nada disso vai para o Git.

## Gerar o executável (Windows)

1. Rode o `iniciar.bat` pelo menos uma vez (ele instala o uv).
2. Dê dois cliques em `ferramentas\gerar_exe.bat`. Ele gera o programa na pasta `Puxai\` e cria o atalho **Puxaí** na pasta principal.
3. Dê dois cliques no atalho **Puxaí** da pasta principal.

O programa é gerado como pasta, e não como um `.exe` único, porque assim abre bem mais rápido. Para levar para outro PC, copie a pasta `Puxai\` inteira. Sempre que alterar o código, gere o executável de novo.

O yt-dlp vai empacotado no programa, mas **se atualiza sozinho**: uma vez por dia o programa procura uma versão nova no PyPI, baixa (conferindo o SHA-256) e passa a usá-la na próxima abertura. As versões baixadas ficam em `Puxai\atualizacoes\`.

O `gerar_exe.bat` copia o FFmpeg deste PC (`ffmpeg.exe` e `ffprobe.exe`) para dentro da pasta `Puxai\`, então o programa gerado funciona em outro PC sem instalar nada.

Para conferir o programa gerado: `powershell -File ferramentas\testar_exe.ps1`. Ele abre uma cópia do programa (sem o FFmpeg instalado no PC, para garantir que o incluído funciona), testa a API, converte e comprime uma imagem e fecha.

## Gerar o programa (Linux)

Com o uv e o FFmpeg instalados (o `iniciar.sh` instala o uv), rode `sh ferramentas/gerar_linux.sh`. Ele gera o programa na pasta `Puxai/`, com o FFmpeg deste PC e o Deno das bibliotecas junto. Para conferir: `sh ferramentas/testar_linux.sh` (com o `xvfb-run` instalado, também testa se a janela Qt abre).

O programa vale para os Linux com a mesma versão da glibc do PC onde foi gerado, ou mais nova. Por isso o GitHub gera no Ubuntu 22.04.

### Gerado automaticamente pelo GitHub

Sempre que a versão muda no `versao.json` e vai para a `main`, o GitHub gera o programa sozinho (`.github/workflows/gerar-exe.yml`), para Windows e Linux ao mesmo tempo: baixa o FFmpeg (conferindo o SHA-256), roda o mesmo `gerar_exe.bat` / `gerar_linux.sh`, testa com o `testar_exe.ps1` / `testar_linux.sh` e publica os arquivos numa **Release** `vX.Y.Z`, com as novidades da versão. Só publica se o teste do Windows passar e se ainda não existir uma Release dessa versão. Se só o Linux falhar, a Release sai com o Windows (e um aviso na execução).

Os arquivos se chamam sempre **`Puxai-windows.zip`** e **`Puxai-linux.tar.xz`** (sem a versão no nome), por isso estes links baixam sempre a versão mais nova, direto. São os links para divulgar (site, WhatsApp, redes sociais):

- Windows: `https://github.com/daks-2k25/API-BAIXAR-YOUTUBE/releases/latest/download/Puxai-windows.zip`
- Linux: `https://github.com/daks-2k25/API-BAIXAR-YOUTUBE/releases/latest/download/Puxai-linux.tar.xz`

Pela aba **Actions → Gerar o Puxaí (Windows e Linux) → Run workflow**:
- **Sem marcar "publicar":** só gera e testa. Os arquivos ficam para baixar em **Artifacts**, na página da execução, por 7 dias.
- **Marcando "publicar":** gera, testa e coloca os arquivos na Release da versão atual (cria a Release, ou troca os arquivos e o texto se ela já existir). Útil para refazer os arquivos de uma versão já lançada.

## Rodando no macOS

Não é testado, mas deve funcionar no navegador. Instale o [uv](https://docs.astral.sh/uv/) e o FFmpeg (`brew install ffmpeg`), depois:

```bash
uv run app.py
```

## API

A aplicação roda em `http://127.0.0.1:5000`.

**Segurança:** só o painel do programa pode usar a API pelo navegador. Pedidos vindos de outros sites (ou de outro programa local em outra porta, ou com um endereço que não seja `127.0.0.1`/`localhost`) recebem `403`, e a recusa fica registrada no `Puxai.log`. Programas fora do navegador, como `curl` e scripts, continuam podendo usar a API normalmente. Detalhes em `rotas/seguranca.py`.

### `POST /api/download`

Coloca um vídeo na fila de download.

| Campo       | Tipo   | Obrigatório | Descrição |
|-------------|--------|-------------|-----------|
| `url`       | string | Sim         | URL do vídeo |
| `formato`   | string | Não         | `mp4` (padrão) ou `mp3` |
| `qualidade` | string | Não         | Resolução máxima do MP4: `360p`, `480p`, `720p` (padrão) ou `1080p`. Ignorado no MP3 |
| `id`        | string | Não         | ID próprio do download: letras, números, `-` e `_`, até 64 caracteres. Se omitido, gera um UUID |
| `inicio`    | string | Não         | Início do trecho a baixar: `1:20`, `1:02:05` ou segundos |
| `fim`       | string | Não         | Fim do trecho. Sem `fim`, vai até o final do vídeo |
| `pasta`     | string | Não         | Subpasta dentro de Downloads (usada nas playlists, com o nome delas) |
| `numero`    | número | Não         | Posição do vídeo na playlist: vai na frente do nome (`03 - Título`) |
| `total`     | número | Não         | Tamanho da playlist, para saber quantos zeros usar no número (`03` de 40, `003` de 150) |

O arquivo pronto é salvo na pasta **Downloads** do usuário, com o título do vídeo no nome (e o trecho, se houver).

```bash
curl -X POST http://127.0.0.1:5000/api/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=XXXXXXXXXXX", "formato": "mp4", "qualidade": "1080p"}'
```

**Resposta `202 Accepted`:**

```json
{
  "mensagem": "Vídeo enfileirado com sucesso!",
  "id": "3f2b8c1e-....",
  "formato": "mp4",
  "qualidade": "1080p",
  "trecho": null,
  "status": "Na fila..."
}
```

**Resposta `400 Bad Request`** quando falta a URL, quando `formato`, `qualidade`, `id` ou o trecho são inválidos, ou quando o link é de uma playlist inteira (`youtube.com/playlist?list=...`). Para baixar uma playlist, liste os vídeos com `GET /api/playlist` e envie um pedido por vídeo, como faz o painel. Um vídeo dentro de uma playlist (`watch?v=...&list=...`) é aceito, e só o vídeo é baixado:

```json
{ "erro": "Qualidade inválida. Opções: 360p, 480p, 720p, 1080p." }
```

Se o vídeo não tiver a resolução pedida, a API baixa a maior disponível abaixo dela. Alguns sites oferecem uma qualidade só (por exemplo, clipes da Twitch só em 1080p); nesse caso vem essa, mesmo acima da escolhida. Em sites só de áudio (SoundCloud, Bandcamp, Mixcloud), escolha MP3: em MP4 o arquivo sai só com o som.

### `GET /api/info?url=<link>`

Prévia do vídeo, sem baixar nada. Usada pelo painel ao colar um link.

```json
{
  "id": "TO-_3tck2tg",
  "titulo": "Imagine Dragons - Bones (Official Music Video)",
  "canal": "ImagineDragons",
  "duracao": "2:45",
  "miniatura": "https://i.ytimg.com/vi/TO-_3tck2tg/maxresdefault.jpg",
  "youtube": true
}
```

Responde `400` para links de playlist e `404` quando o vídeo não é encontrado. Se o link for de um canal ou de outra lista de vídeos sem `list=` no endereço, a resposta é `{"playlist": true, "titulo": "..."}`, e o painel abre a lista de vídeos.

### `GET /api/link-copiado`

Se o texto copiado agora (área de transferência do sistema) tiver um link de um site que o yt-dlp baixa, devolve `{"url": "...", "site": "YouTube"}`; senão (ou com a opção desligada nas Configurações), `{"url": null, "site": null}`. Nenhum outro texto copiado é devolvido.

### `GET /api/playlist?url=<link>`

Lista os vídeos de uma playlist (ou de um canal) sem baixar nada, até os primeiros 200. Na página inicial de um canal do YouTube, lista a aba **Vídeos**.

```json
{
  "titulo": "Python Tutorials",
  "canal": "Corey Schafer",
  "site": "YouTube",
  "total": 158,
  "limite": 200,
  "itens": [
    { "numero": 1, "url": "https://www.youtube.com/watch?v=YYXdXT2l-Gg", "titulo": "Python Tutorial for Beginners 1: ...",
      "duracao": "15:29", "miniatura": "https://i.ytimg.com/vi/...", "disponivel": true }
  ]
}
```

`disponivel` é `false` para vídeos privados ou apagados. Responde `400` quando o link não é de uma playlist.

### `GET /api/qualidades`

Lista as resoluções aceitas.

```json
{ "qualidades": ["360p", "480p", "720p", "1080p"], "padrao": "720p" }
```

### `GET /api/extensao/estado`, `POST /api/extensao/enviar` e `POST /api/extensao/abrir`

As únicas rotas que a extensão do navegador pode usar (pedidos com `Origin: chrome-extension://...` ou `moz-extension://...`; em qualquer outra rota, eles recebem `403`). `estado` responde `{"puxai": true, "versao", "qualidades", "padrao"}`. `enviar` recebe `{"url", "formato": "mp4"|"mp3", "qualidade": "720p", "titulo"}`, confere se o yt-dlp sabe baixar daquele link e põe na fila: `202` com `{"id", "site", "formato", "qualidade"}`, ou `400` com o motivo (página que não é de vídeo, link de playlist). `abrir` traz a janela do Puxaí para a frente (ou abre o painel).

### `POST /api/relatorio` e `POST /api/relatorio/enviar`

`POST /api/relatorio` com `{"id": "<download>"}` (opcional) monta o relatório de erro, já sem dados pessoais: `{"titulo", "texto", "email": true|false}` (`email`: se há um e-mail de suporte configurado). `POST /api/relatorio/enviar` com `{"destino": "github"|"email", "titulo", "descricao", "texto"}` abre o novo *Issue* do GitHub no navegador (ou o programa de e-mail) com o relatório preenchido. Se o texto for grande demais para caber no endereço, o fim é cortado (avisando no próprio relatório).

### `GET /api/fila`

Os downloads que ainda não terminaram, na ordem da fila: `[{"id_download", "url", "formato", "qualidade", "titulo", "origem": "painel"|"extensao", "trecho": [inicio, fim|null] | null, "status", "retomado"}]`. `retomado` é `true` para os que voltaram de quando o programa fechou. O painel usa ao abrir (e ao recarregar a página) para mostrar a lista. No `POST /api/download`, o campo opcional `titulo` (o da prévia) é o que aparece aqui.

### `GET /api/progresso/<id>`

Retorna o status do download. Quando fica pronto, `titulo` e `arquivo` (nome do arquivo na pasta Downloads) são preenchidos.

```json
{ "id": "3f2b8c1e-....", "status": "Pronto", "titulo": "Me at the zoo", "arquivo": "Me at the zoo.mp4" }
```

| Status                   | Significado |
|--------------------------|-------------|
| `Na fila...`             | Aguardando a vez na fila |
| `Baixando...`            | Download iniciado |
| `xx.x%`                  | Progresso do download |
| `Processando arquivo...` | Download concluído, convertendo/juntando vídeo e áudio |
| `Pronto`                 | Arquivo salvo na pasta Downloads |
| `Erro`                   | Falha no download (depois de 2 tentativas) |
| `Cancelado`              | Cancelado pelo usuário |
| `Desconhecido`           | ID não encontrado |

### `POST /api/progresso`

O mesmo que a rota acima, para vários downloads de uma vez (o painel usa esta, para não fazer um pedido por vídeo numa playlist). Corpo: `{"ids": ["id1", "id2"]}` (até 500). A resposta tem um objeto por ID, no mesmo formato de `GET /api/progresso/<id>`.

### `POST /api/cancelar/<id>`

Cancela um download na fila ou em andamento; os arquivos parciais são apagados. Responde `404` se o download não existe ou já terminou.

### `POST /api/mostrar/<id>`

Abre o Explorador de Arquivos com o arquivo pronto selecionado (usado pelo botão **Mostrar na pasta**).

### `GET /api/arquivo/<id>`

Envia o arquivo pronto pela resposta HTTP, para quem usa a API a partir de outro programa. O arquivo continua na pasta Downloads.

```bash
curl -OJ http://127.0.0.1:5000/api/arquivo/3f2b8c1e-....
```

Responde `404` se o arquivo ainda não estiver pronto ou não for encontrado.

### `POST /api/converter/imagem`

Converte uma foto. Envie como `multipart/form-data` o arquivo no campo `arquivo` e o formato de saída no campo `formato`; a resposta é a foto convertida.

| `formato` | Aceita |
|-----------|--------|
| `jpg` (padrão) | HEIC/HEIF |
| `webp` | HEIC/HEIF, JPG e PNG (mantém a transparência) |

```bash
curl -X POST http://127.0.0.1:5000/api/converter/imagem \
  -F "arquivo=@foto.png" -F "formato=webp" -OJ
```

O endereço antigo `POST /api/converter/heic` continua funcionando (sem `formato`, converte para JPG).

| Código | Quando |
|--------|--------|
| `400`  | Nenhum arquivo enviado, formato inválido ou tipo de foto não aceito para esse formato |
| `500`  | Falha na conversão (o arquivo não é uma foto válida) |

### `POST /api/comprimir`

Comprime uma foto (JPG, PNG, WebP ou HEIC). Envie como `multipart/form-data`:

| Campo | Valores |
|-------|---------|
| `arquivo` | a foto |
| `nivel` | `alta`, `equilibrado` (padrão) ou `forte` |
| `tamanho` | maior lado da foto: `original` (padrão), `2560`, `1920` ou `1280` |

A resposta é a foto comprimida. Com `?salvar=1` (usado pelo painel), ela vai para a pasta Downloads e a resposta é um JSON com `arquivo`, `antes` e `depois` (bytes), `largura` e `altura`. Se não der para diminuir sem perder qualidade, a resposta é um JSON com `"ja_otimizada": true` e nada é salvo.

```bash
curl -X POST http://127.0.0.1:5000/api/comprimir \
  -F "arquivo=@foto.jpg" -F "nivel=equilibrado" -F "tamanho=1920" -OJ
```

### `POST /api/comprimir-video`

Coloca um vídeo na fila de compressão (um por vez). Envie como `multipart/form-data`:

| Campo | Valores |
|-------|---------|
| `arquivo` | o vídeo (MP4, MOV, MKV, WebM, AVI, M4V, 3GP, WMV, FLV, MPG, TS) |
| `modo` | `tamanho` (padrão) ou `qualidade` |
| `tamanho` | com `modo=tamanho`: `whatsapp` (16 MB), `discord` (10 MB), `email` (25 MB) ou um número de MB (1 a 4000) |
| `qualidade` | com `modo=qualidade`: `alta`, `equilibrada` (padrão) ou `forte` |
| `resolucao` | maior resolução: `original` (padrão), `1080`, `720` ou `480` |

Responde `202` com `{"id": "...", "status": "Na fila..."}`. Acompanhe por `GET /api/progresso/<id>` (o `status` vai de `"0.0%"` a `"99.0%"` e termina em `Pronto`, `Erro` ou `Cancelado`) e cancele por `POST /api/cancelar/<id>`. Quando fica pronto, `extra` traz `antes` e `depois` (bytes), `largura`, `altura` e `ja_otimizada` (`true` quando não havia o que diminuir e nada foi salvo).

```bash
curl -X POST http://127.0.0.1:5000/api/comprimir-video \
  -F "arquivo=@video.mov" -F "modo=tamanho" -F "tamanho=whatsapp"
```

### `GET /api/historico`

Lista o que o programa já salvou, do mais novo para o mais antigo. Cada item traz `id`, `titulo`, `arquivo`, `caminho`, `tipo` (`video`, `musica` ou `foto`), `formato`, `data` (segundos desde 1970), `origem` (link do vídeo, se houver), `existe` (se o arquivo ainda está lá) e `tamanho` em bytes.

### `DELETE /api/historico/<id>` e `DELETE /api/historico`

Tiram um item da lista, ou limpam a lista toda. Os arquivos continuam na pasta Downloads.

### `POST /api/abrir/<id>`

Abre o arquivo no programa padrão do sistema. Responde `404` se o arquivo foi movido ou apagado. A rota `POST /api/mostrar/<id>` também passa a achar os arquivos do histórico.

### `POST /api/ping` e `POST /api/encerrar`

Usadas pelo painel: o `ping` avisa a cada 30 segundos que o painel continua aberto, e o `encerrar` fecha o programa.

### `GET /api/versao`

Versão instalada e, se houver, a versão nova no GitHub. Adicione `?forcar=1` para não usar a consulta guardada (o resultado fica guardado por 10 minutos).

```json
{ "atual": "2.0.0", "nova": "2.1.0", "novidades": ["..."], "disponivel": true, "pode_atualizar": true, "motivo": null }
```

`pode_atualizar` é `false` no programa gerado (`.exe`) e em pastas git fora da `main` ou com alterações locais; `motivo` explica o porquê.

### `POST /api/versao/adiar`

Corpo: `{"versao": "2.1.0"}`. Usado pelo botão **Depois**: o painel não mostra de novo a notificação dessa versão (o `GET /api/versao` passa a responder `"adiada": true`). Fica guardado em `.preferencias.json`.

### `POST /api/atualizar`

Baixa e instala a versão nova e reinicia o programa. Responde `{"versao": "<versão nova>"}`, ou `409` se houver downloads em andamento.

### `GET /api/atualizar/andamento`

No programa gerado, enquanto o `POST /api/atualizar` baixa a versão nova: `{"etapa": "baixando" | "extraindo" | null, "baixado": <bytes>, "total": <bytes>}`. O painel usa para mostrar a porcentagem.

### `GET /api/preferencias` e `POST /api/preferencias`

Lê ou salva como o programa abre (`modo_abertura`: `janela` ou `navegador`, vale a partir da próxima vez que o programa abrir) e o tema (`tema`: `automatico`, `claro` ou `escuro`). Dá para enviar um ou os dois. A resposta traz também `tema_em_uso` (`claro` ou `escuro`: no automático, o do sistema).

```json
{ "modo_abertura": "janela", "tema": "automatico", "tema_em_uso": "escuro" }
```

### `GET /api/pastas` e `POST /api/pastas`

Lê ou salva onde os arquivos prontos são salvos. `modo` é `uma` (uma pasta para tudo, em `tudo`) ou `separadas` (`video`, `musica` e `foto`). Uma pasta vazia (`""`) volta para Downloads; uma pasta que não existe responde `400`.

```json
{ "modo": "separadas", "tudo": "C:\\Users\\Fulano\\Downloads", "video": "D:\\Videos",
  "musica": "D:\\Musicas", "foto": "C:\\Users\\Fulano\\Downloads", "padrao": "C:\\Users\\Fulano\\Downloads" }
```

### `POST /api/pastas/escolher`

Abre a janela do sistema para escolher uma pasta e devolve `{"pasta": "D:\\Videos"}` (ou `{"pasta": null}` se a pessoa cancelar). Só escolhe: para salvar, envie a pasta em `POST /api/pastas`. Corpo opcional: `{"atual": "<pasta onde a janela abre>"}`.

### `POST /api/abrir-no-navegador` e `POST /api/reabrir-como-aplicativo`

Trocam o modo na hora: a primeira abre o painel no navegador e fecha a janela (o programa continua rodando); a segunda reinicia o programa na janela do aplicativo.

### `GET /api/modo` e `POST /api/focar`

Usadas pela janela do programa: `modo` diz se o painel está na janela própria (`{"janela": true}`) ou no navegador, e `focar` traz a janela para a frente (é o que acontece ao clicar no atalho com o programa já aberto).

## Observações

- A fila de downloads fica guardada em `.fila.json` (só os que não terminaram); o status de cada um, em memória.
- O servidor (Waitress) atende só o próprio PC (`127.0.0.1`). Para hospedar num servidor de verdade, use **um único processo**, porque a fila de downloads fica em memória.
- Respeite os termos de uso das plataformas e os direitos autorais do conteúdo baixado.

## Licença

Este projeto está sob a licença MIT. Sinta-se à vontade para usar e modificar.
