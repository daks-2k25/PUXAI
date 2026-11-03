// Escolhas atuais do formulário
let formatoEscolhido = "mp4";
let qualidadeEscolhida = "720p";

// ==========================================
// ABAS
// ==========================================
document.querySelectorAll(".aba").forEach((aba) => {
    aba.addEventListener("click", () => {
        document.querySelectorAll(".aba").forEach((a) => a.classList.remove("ativa"));
        aba.classList.add("ativa");
        // Cada aba mostra a seção com o mesmo id (youtube, heic, meus-downloads)
        document.querySelectorAll("main > section.card").forEach((secao) => {
            secao.classList.toggle("escondido", secao.id !== aba.dataset.aba);
        });
        if (aba.dataset.aba === "meus-downloads") carregarHistorico();
    });
});

// ==========================================
// FERRAMENTA 1: YOUTUBE
// ==========================================

// Formato (MP4 / MP3)
document.querySelectorAll("#formatos .chip").forEach((chip) => {
    chip.addEventListener("click", () => {
        document.querySelectorAll("#formatos .chip").forEach((c) => c.classList.remove("ativo"));
        chip.classList.add("ativo");
        formatoEscolhido = chip.dataset.formato;

        // Qualidade só vale para vídeo
        document.querySelectorAll("#qualidades .chip").forEach((c) => (c.disabled = formatoEscolhido === "mp3"));
    });
});

// Busca as qualidades na API e cria os botões
async function carregarQualidades() {
    const resposta = await fetch("/api/qualidades");
    const dados = await resposta.json();
    qualidadeEscolhida = dados.padrao;

    const grupo = document.getElementById("qualidades");
    dados.qualidades.forEach((qualidade) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip" + (qualidade === dados.padrao ? " ativo" : "");
        chip.textContent = qualidade;
        chip.addEventListener("click", () => {
            grupo.querySelectorAll(".chip").forEach((c) => c.classList.remove("ativo"));
            chip.classList.add("ativo");
            qualidadeEscolhida = qualidade;
        });
        grupo.appendChild(chip);
    });
}

// ==========================================
// PLAYLISTS: escolher quais vídeos baixar
// ==========================================
const campoUrl = document.getElementById("url");
const botaoBaixar = document.querySelector("#form-download .botao");
const avisoPlaylist = document.getElementById("aviso-playlist");
const avisoTexto = document.getElementById("aviso-texto");
const botaoUsarSoVideo = document.getElementById("usar-so-video");
const botaoVerPlaylist = document.getElementById("ver-playlist");
const painelPlaylist = document.getElementById("playlist");
const playlistTitulo = document.getElementById("playlist-titulo");
const playlistInfo = document.getElementById("playlist-info");
const playlistCorpo = document.getElementById("playlist-corpo");
const playlistItens = document.getElementById("playlist-itens");
const playlistTodos = document.getElementById("playlist-todos");
const playlistContagem = document.getElementById("playlist-contagem");
const playlistPasta = document.getElementById("playlist-pasta");
const blocoCortar = document.getElementById("cortar");

// Playlist aberta no painel: { url, dados } (dados = resposta de /api/playlist, ou null carregando)
let playlistAtual = null;
let consultaPlaylist = null;

function marcados() {
    return [...playlistItens.querySelectorAll("input:checked")].map((c) => playlistAtual.dados.itens[c.dataset.indice]);
}

// O botão principal mostra quantos vídeos vão ser baixados
function atualizarBotaoBaixar() {
    if (modoVarios) return atualizarVariosLinks();
    if (!playlistAtual) {
        botaoBaixar.textContent = "Baixar agora";
        botaoBaixar.disabled = analisarLink(campoUrl.value).tipo === "video-na-playlist";
        return;
    }
    const quantos = playlistAtual.dados ? marcados().length : 0;
    botaoBaixar.textContent = quantos === 1 ? "Baixar 1 vídeo" : `Baixar ${quantos} vídeos`;
    botaoBaixar.disabled = quantos === 0;
    if (playlistAtual.dados) {
        const disponiveis = playlistAtual.dados.itens.filter((i) => i.disponivel).length;
        playlistContagem.textContent = `${quantos} de ${disponiveis} marcados`;
        playlistTodos.checked = quantos === disponiveis;
        playlistTodos.indeterminate = quantos > 0 && quantos < disponiveis;
    }
}

function fecharPlaylist() {
    if (!playlistAtual) return;
    playlistAtual = null;
    consultaPlaylist?.abort();
    playlistItens.replaceChildren();
    painelPlaylist.classList.add("escondido");
    blocoCortar.classList.remove("escondido");
    atualizarBotaoBaixar();
}

function abrirPlaylist(url) {
    if (playlistAtual?.url === url) return;
    playlistAtual = { url, dados: null };
    esconderPrevia();
    painelPlaylist.classList.remove("escondido");
    painelPlaylist.classList.add("carregando");
    playlistCorpo.classList.add("escondido");
    playlistItens.replaceChildren(); // não mostra a lista anterior enquanto carrega
    blocoCortar.classList.add("escondido"); // cortar trecho vale para um vídeo só
    playlistTitulo.textContent = "Carregando a playlist...";
    playlistInfo.textContent = "";
    atualizarBotaoBaixar();

    consultaPlaylist?.abort();
    consultaPlaylist = new AbortController();
    const pedido = playlistAtual;
    fetch(`/api/playlist?url=${encodeURIComponent(url)}`, { signal: consultaPlaylist.signal })
        .then(async (resposta) => {
            const dados = await resposta.json();
            if (playlistAtual !== pedido) return; // o link mudou nesse meio-tempo
            painelPlaylist.classList.remove("carregando");
            if (!resposta.ok) {
                playlistTitulo.textContent = dados.erro;
                return;
            }
            pedido.dados = dados;
            mostrarPlaylist(dados);
        })
        .catch(() => {});
}

function mostrarPlaylist(dados) {
    playlistTitulo.textContent = dados.titulo;
    // Canais nem sempre dizem o total: se chegou no limite, pode haver mais
    const quantos = dados.itens.length;
    const quantidade = dados.total > quantos
        ? `mostrando os primeiros ${quantos} de ${dados.total} vídeos (limite de ${dados.limite})`
        : quantos >= dados.limite
            ? `mostrando os primeiros ${quantos} vídeos (limite de ${dados.limite})`
            : `${quantos} ${quantos === 1 ? "vídeo" : "vídeos"}`;
    playlistInfo.textContent = [dados.canal, dados.site, quantidade].filter(Boolean).join(" · ");

    playlistItens.replaceChildren();
    dados.itens.forEach((video, indice) => {
        const linha = document.createElement("li");
        linha.className = "playlist-item" + (video.disponivel ? "" : " indisponivel");
        linha.innerHTML = `
            <label>
                <input type="checkbox" />
                <span class="playlist-numero"></span>
                <img alt="" loading="lazy" />
                <span class="playlist-nome"></span>
                <span class="playlist-duracao"></span>
            </label>
        `;
        const caixa = linha.querySelector("input");
        caixa.dataset.indice = indice;
        caixa.checked = video.disponivel;
        caixa.disabled = !video.disponivel;
        caixa.addEventListener("change", atualizarBotaoBaixar);
        linha.querySelector(".playlist-numero").textContent = video.numero;
        // textContent (e não innerHTML): o título vem do site e pode ter qualquer caractere
        linha.querySelector(".playlist-nome").textContent = video.titulo;
        linha.querySelector(".playlist-duracao").textContent = video.disponivel ? video.duracao || "" : "indisponível";
        const miniatura = linha.querySelector("img");
        if (video.miniatura) miniatura.src = video.miniatura;
        else miniatura.hidden = true;
        miniatura.addEventListener("error", () => (miniatura.style.visibility = "hidden"));
        playlistItens.appendChild(linha);
    });
    playlistCorpo.classList.remove("escondido");
    atualizarBotaoBaixar();
}

playlistTodos.addEventListener("change", () => {
    playlistItens.querySelectorAll("input:not(:disabled)").forEach((c) => (c.checked = playlistTodos.checked));
    atualizarBotaoBaixar();
});

// Põe cada vídeo marcado na fila, na ordem da playlist
async function baixarPlaylist() {
    const { dados } = playlistAtual;
    const videos = marcados();
    const pasta = playlistPasta.checked ? dados.titulo : null;
    const descricao = formatoEscolhido === "mp3" ? "MP3" : `MP4 ${qualidadeEscolhida}`;
    botaoBaixar.disabled = true;
    botaoBaixar.textContent = "Colocando na fila...";

    const lote = document.createDocumentFragment();
    for (const video of videos) {
        const pedido = {
            url: video.url, formato: formatoEscolhido, qualidade: qualidadeEscolhida, titulo: video.titulo,
            ...(pasta ? { pasta, numero: video.numero, total: dados.total } : {}),
        };
        const resposta = await fetch("/api/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(pedido),
        }).catch(() => null);
        const resultado = resposta ? await resposta.json().catch(() => ({})) : {};
        const item = criarItem(resultado.id, descricao, video.titulo, { inserir: false });
        if (!resposta || !resposta.ok) marcarErro(item, resultado.erro || "Não foi possível colocar na fila.");
        lote.appendChild(item);
    }
    document.getElementById("lista-downloads").prepend(lote);

    campoUrl.value = "";
    aoMudarLink();
}

// ==========================================
// LINK COPIADO: oferece "Colar" quando há um link de vídeo copiado
// ==========================================
// O programa lê a área de transferência e só responde se for um link de vídeo.
// Pergunta ao abrir e ao voltar para o Puxaí (trocar de janela ou de aba), com
// o campo vazio. Link dispensado no ✕ não é oferecido de novo.
const avisoLinkCopiado = document.getElementById("link-copiado");
const CHAVE_DISPENSADOS = "puxai-links-dispensados";
let linkOferecido = null;
let ultimaVerificacao = 0;

function linksDispensados() {
    try {
        return JSON.parse(localStorage.getItem(CHAVE_DISPENSADOS) || "[]");
    } catch {
        return [];
    }
}

function dispensarLink(url) {
    try {
        localStorage.setItem(CHAVE_DISPENSADOS, JSON.stringify([url, ...linksDispensados()].slice(0, 30)));
    } catch {
        // Sem armazenamento: só não lembra depois de fechar
    }
}

function esconderLinkCopiado() {
    avisoLinkCopiado.classList.add("escondido");
    linkOferecido = null;
}

async function verificarLinkCopiado() {
    // Só faz sentido na aba Vídeos, com o campo vazio e o Puxaí na frente
    const abaVideos = !document.getElementById("youtube").classList.contains("escondido");
    if (!abaVideos || modoVarios || campoUrl.value.trim() || document.visibilityState !== "visible") return;
    if (Date.now() - ultimaVerificacao < 1000) return; // foco e visibilidade chegam juntos
    ultimaVerificacao = Date.now();

    const dados = await fetch("/api/link-copiado").then((r) => r.json()).catch(() => ({}));
    if (!dados.url || campoUrl.value.trim() || linksDispensados().includes(dados.url)) {
        if (!dados.url) esconderLinkCopiado();
        return;
    }
    linkOferecido = dados.url;
    document.getElementById("link-copiado-site").textContent = dados.site;
    document.getElementById("link-copiado-url").textContent = dados.url.replace(/^https?:\/\/(www\.)?/, "");
    document.getElementById("link-copiado-url").title = dados.url;
    avisoLinkCopiado.classList.remove("escondido");
}

document.getElementById("link-copiado-colar").addEventListener("click", () => {
    const url = linkOferecido;
    dispensarLink(url); // já usado: não oferece de novo
    esconderLinkCopiado();
    campoUrl.value = url;
    aoMudarLink();
    campoUrl.focus();
});
document.getElementById("link-copiado-fechar").addEventListener("click", () => {
    dispensarLink(linkOferecido);
    esconderLinkCopiado();
});
campoUrl.addEventListener("input", () => {
    if (campoUrl.value.trim()) esconderLinkCopiado();
});
window.addEventListener("focus", verificarLinkCopiado);
document.addEventListener("visibilitychange", verificarLinkCopiado);
document.querySelector('[data-aba="youtube"]').addEventListener("click", () => setTimeout(verificarLinkCopiado, 50));
setTimeout(verificarLinkCopiado, 600);

// ==========================================
// VÁRIOS LINKS DE UMA VEZ
// ==========================================
const campoVarios = document.getElementById("varios-links");
const botaoModoVarios = document.getElementById("modo-varios");
const linksEncontrados = document.getElementById("links-encontrados");
const LIMITE_LINKS = 200;
let modoVarios = false;

// Acha os links no texto (um por linha, separados por espaço ou no meio de outro texto), sem repetir.
// O mesmo vídeo do YouTube escrito de jeitos diferentes (watch?v=, youtu.be/, shorts/) conta uma vez.
function extrairLinks(texto) {
    const achados = (texto.match(/https?:\/\/[^\s<>"']+/gi) || []).map((link) => link.replace(/[),.;]+$/, ""));
    const vistos = new Set();
    return achados.filter((link) => {
        const analise = analisarLink(link);
        // Vídeo dentro de playlist conta pelo vídeo; playlist inteira, pelo link
        const chave = analise.tipo === "playlist" ? link : idDoYoutube(analise.linkLimpo || link) || link;
        if (vistos.has(chave)) return false;
        vistos.add(chave);
        return true;
    }).slice(0, LIMITE_LINKS);
}

function trocarModo(varios, texto = "") {
    modoVarios = varios;
    campoUrl.classList.toggle("escondido", varios);
    campoVarios.classList.toggle("escondido", !varios);
    // O campo escondido não pode ser obrigatório, senão o formulário não envia
    campoUrl.required = !varios;
    botaoModoVarios.textContent = varios ? "← Voltar para um link só" : "+ Colar vários links de uma vez";
    if (varios) {
        campoVarios.value = texto || campoUrl.value.trim();
        campoUrl.value = "";
        aoMudarLink(); // fecha prévia, playlist e aviso do link único
        campoVarios.focus();
    } else {
        const links = extrairLinks(campoVarios.value);
        campoVarios.value = "";
        campoUrl.value = links[0] || "";
        aoMudarLink();
        campoUrl.focus();
    }
    blocoCortar.classList.toggle("escondido", varios); // cortar trecho vale para um vídeo só
    atualizarVariosLinks();
}

function atualizarVariosLinks() {
    if (!modoVarios) {
        linksEncontrados.textContent = "";
        return;
    }
    const quantos = extrairLinks(campoVarios.value).length;
    linksEncontrados.textContent = quantos === 0 ? "Nenhum link ainda"
        : quantos === 1 ? "1 link encontrado"
        : `${quantos} links encontrados${quantos === LIMITE_LINKS ? ` (limite de ${LIMITE_LINKS})` : ""}`;
    botaoBaixar.textContent = quantos === 1 ? "Baixar 1 link" : `Baixar ${quantos} links`;
    botaoBaixar.disabled = quantos === 0;
}

botaoModoVarios.addEventListener("click", () => trocarModo(!modoVarios));
campoVarios.addEventListener("input", atualizarVariosLinks);

// Colou vários links no campo de um link só: muda para o modo de vários sozinho
// (o campo de uma linha juntaria todos num link só, inválido)
campoUrl.addEventListener("paste", (evento) => {
    const texto = evento.clipboardData?.getData("text") || "";
    if (extrairLinks(texto).length < 2) return;
    evento.preventDefault();
    trocarModo(true, texto.trim());
});

// Põe cada link na fila, na ordem em que foram colados
async function baixarVariosLinks() {
    const links = extrairLinks(campoVarios.value);
    const descricao = formatoEscolhido === "mp3" ? "MP3" : `MP4 ${qualidadeEscolhida}`;
    botaoBaixar.disabled = true;
    botaoBaixar.textContent = "Colocando na fila...";

    const lote = document.createDocumentFragment();
    for (const link of links) {
        const analise = analisarLink(link);
        // Até o download terminar, o item mostra o link (o título vem quando fica pronto)
        const nome = link.replace(/^https?:\/\/(www\.)?/, "");
        if (analise.tipo === "playlist") {
            const item = criarItem(null, descricao, nome, { inserir: false });
            marcarErro(item, "É o link de uma playlist: cole ele sozinho para escolher os vídeos.");
            lote.appendChild(item);
            continue;
        }
        const resposta = await fetch("/api/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // Vídeo dentro de playlist: baixa só o vídeo
            body: JSON.stringify({ url: analise.linkLimpo || link, formato: formatoEscolhido, qualidade: qualidadeEscolhida, titulo: nome }),
        }).catch(() => null);
        const resultado = resposta ? await resposta.json().catch(() => ({})) : {};
        const item = criarItem(resultado.id, descricao, nome, { inserir: false });
        if (!resposta || !resposta.ok) marcarErro(item, resultado.erro || "Não foi possível colocar na fila.");
        lote.appendChild(item);
    }
    document.getElementById("lista-downloads").prepend(lote);

    campoVarios.value = "";
    atualizarVariosLinks();
}

// Vídeo aberto dentro de uma playlist: "https://youtube.com/watch?v=X&list=Y" -> link só da playlist
function linkDaPlaylist(texto) {
    const lista = new URL(texto.trim()).searchParams.get("list");
    return `https://www.youtube.com/playlist?list=${encodeURIComponent(lista)}`;
}

// Diz se o link é de uma playlist inteira, de um vídeo dentro de uma playlist
// ou de um vídeo comum. Para o vídeo dentro da playlist, devolve o link limpo.
function analisarLink(texto) {
    let link;
    try {
        link = new URL(texto.trim());
    } catch {
        return { tipo: "comum" };
    }
    if (!link.searchParams.has("list")) return { tipo: "comum" };

    const temVideo =
        link.searchParams.has("v") ||
        (link.hostname.endsWith("youtu.be") && link.pathname.length > 1) ||
        /^\/(shorts|live|embed)\//.test(link.pathname);

    if (!temVideo) return { tipo: "playlist" };

    ["list", "index", "start_radio", "pp"].forEach((p) => link.searchParams.delete(p));
    return { tipo: "video-na-playlist", linkLimpo: link.toString() };
}

function atualizarAvisoPlaylist() {
    const analise = analisarLink(campoUrl.value);

    // Link de playlist: abre a lista para escolher os vídeos
    if (analise.tipo === "playlist") abrirPlaylist(campoUrl.value.trim());
    // Outro link: fecha a lista (exceto se ela foi aberta pela prévia, ex.: link de canal)
    else if (playlistAtual?.url !== campoUrl.value.trim()) fecharPlaylist();

    // Vídeo dentro de uma playlist: pergunta se é o vídeo ou a playlist
    avisoPlaylist.classList.toggle("escondido", analise.tipo !== "video-na-playlist");
    if (analise.tipo === "video-na-playlist") {
        avisoTexto.textContent = "Este vídeo faz parte de uma playlist. O que você quer baixar?";
        botaoUsarSoVideo.onclick = () => {
            campoUrl.value = analise.linkLimpo;
            aoMudarLink();
        };
        botaoVerPlaylist.onclick = () => {
            campoUrl.value = linkDaPlaylist(campoUrl.value);
            aoMudarLink();
        };
    }
    atualizarBotaoBaixar();
}

// ==========================================
// PRÉVIA DO VÍDEO
// ==========================================
const previa = document.getElementById("previa");
const previaMidia = document.getElementById("previa-midia");
const previaMiniatura = document.getElementById("previa-miniatura");
const previaPlay = document.getElementById("previa-play");
const previaDuracao = document.getElementById("previa-duracao");
const previaTitulo = document.getElementById("previa-titulo");
const previaCanal = document.getElementById("previa-canal");

let previaAtual = null; // { chave, id, titulo } do vídeo mostrado
let esperaDigitacao = null;
let consultaEmAndamento = null;

// Pega o ID do vídeo em links do YouTube (watch?v=, youtu.be/, shorts/...)
function idDoYoutube(texto) {
    try {
        const link = new URL(texto.trim());
        if (!/(^|\.)(youtube\.com|youtu\.be)$/.test(link.hostname)) return null;
        if (link.searchParams.get("v")) return link.searchParams.get("v");
        if (link.hostname.endsWith("youtu.be")) return link.pathname.slice(1) || null;
        const caminho = link.pathname.match(/^\/(shorts|live|embed)\/([^/?]+)/);
        return caminho ? caminho[2] : null;
    } catch {
        return null;
    }
}

function esconderPrevia() {
    previa.classList.add("escondido");
    previaAtual = null;
    campoFim.placeholder = "fim";
}

// Volta a mostrar a miniatura (tira o vídeo que estava tocando)
function mostrarMiniatura(endereco) {
    previa.classList.remove("assistindo");
    previaMidia.querySelector("iframe")?.remove();
    previaMiniatura.hidden = false;
    previaMiniatura.src = endereco || "";
}

function atualizarPrevia() {
    const texto = campoUrl.value.trim();
    const tipo = analisarLink(texto).tipo;
    if (!texto || tipo === "playlist" || playlistAtual?.url === texto) {
        esconderPrevia();
        return;
    }

    const id = idDoYoutube(texto);
    const chave = id || texto;
    if (previaAtual && previaAtual.chave === chave) return; // mesmo vídeo: mantém

    // Mostra na hora a miniatura (vem direto do YouTube) e busca o resto na API
    previaAtual = { chave, id, titulo: null };
    previa.classList.remove("escondido", "nao-encontrado");
    previa.classList.add("carregando");
    mostrarMiniatura(id ? `https://i.ytimg.com/vi/${id}/hqdefault.jpg` : "");
    previaPlay.hidden = !id;
    previaDuracao.textContent = "";
    previaTitulo.textContent = "Carregando prévia...";
    previaCanal.textContent = "";

    consultaEmAndamento?.abort();
    consultaEmAndamento = new AbortController();
    const consultaDestePedido = previaAtual;

    fetch(`/api/info?url=${encodeURIComponent(texto)}`, { signal: consultaEmAndamento.signal })
        .then(async (resposta) => {
            const dados = await resposta.json();
            if (previaAtual !== consultaDestePedido) return; // o link mudou nesse meio-tempo
            previa.classList.remove("carregando");

            // Link de canal, álbum...: na verdade é uma lista de vídeos
            if (resposta.ok && dados.playlist) {
                abrirPlaylist(texto);
                return;
            }

            if (!resposta.ok) {
                previa.classList.add("nao-encontrado");
                previaTitulo.textContent = dados.erro;
                return;
            }

            previaAtual.titulo = dados.titulo;
            previaTitulo.textContent = dados.titulo;
            // Ex.: "clinicavittace · Instagram"
            previaCanal.textContent = [dados.canal, dados.site].filter(Boolean).join(" · ");
            previaDuracao.textContent = dados.duracao || "";
            campoFim.placeholder = dados.duracao || "fim"; // dica para o corte
            if (!id && dados.miniatura) mostrarMiniatura(dados.miniatura);
        })
        .catch(() => {});
}

// Clicar no play: o vídeo toca dentro do card
previaPlay.addEventListener("click", () => {
    if (!previaAtual?.id) return;
    const player = document.createElement("iframe");
    player.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(previaAtual.id)}?autoplay=1`;
    player.allow = "autoplay; encrypted-media; picture-in-picture";
    player.allowFullscreen = true;
    previaMiniatura.hidden = true;
    previaMidia.appendChild(player);
    previa.classList.add("assistindo");
});

// Se a miniatura não existir, mostra o fundo vazio em vez de uma imagem quebrada
previaMiniatura.addEventListener("error", () => (previaMiniatura.hidden = true));

function aoMudarLink() {
    atualizarAvisoPlaylist();
    // Espera a pessoa parar de digitar antes de consultar a API
    clearTimeout(esperaDigitacao);
    esperaDigitacao = setTimeout(atualizarPrevia, 400);
}

campoUrl.addEventListener("input", aoMudarLink);

// ==========================================
// CORTAR TRECHO
// ==========================================
const botaoCortar = document.getElementById("botao-cortar");
const camposTrecho = document.getElementById("campos-trecho");
const campoInicio = document.getElementById("trecho-inicio");
const campoFim = document.getElementById("trecho-fim");
const erroTrecho = document.getElementById("erro-trecho");

botaoCortar.addEventListener("click", () => {
    const ativo = botaoCortar.classList.toggle("ativo");
    camposTrecho.classList.toggle("escondido", !ativo);
    if (ativo) {
        campoInicio.focus();
    } else {
        campoInicio.value = campoFim.value = "";
        mostrarErroTrecho("");
    }
});

// "1:20" -> 80 | "" -> null | texto inválido -> NaN
function lerTempo(texto) {
    texto = texto.trim();
    if (!texto) return null;
    const partes = texto.split(":");
    if (partes.length > 3 || partes.some((p) => !/^\d+(\.\d+)?$/.test(p))) return NaN;
    return partes.reduce((total, parte) => total * 60 + Number(parte), 0);
}

function mostrarErroTrecho(mensagem, campo) {
    erroTrecho.textContent = mensagem;
    [campoInicio, campoFim].forEach((c) => c.classList.toggle("invalido", c === campo));
}

[campoInicio, campoFim].forEach((campo) => campo.addEventListener("input", () => mostrarErroTrecho("")));

// Devolve { inicio, fim } (ou null se não for cortar); false se os tempos forem inválidos
function trechoEscolhido() {
    if (!botaoCortar.classList.contains("ativo")) return null;
    const inicio = lerTempo(campoInicio.value);
    const fim = lerTempo(campoFim.value);

    if (Number.isNaN(inicio)) return mostrarErroTrecho("Início inválido. Use minutos:segundos, ex.: 1:20", campoInicio), false;
    if (Number.isNaN(fim)) return mostrarErroTrecho("Fim inválido. Use minutos:segundos, ex.: 2:05", campoFim), false;
    if (inicio === null && fim === null) return null; // nada preenchido: baixa o vídeo inteiro
    if (fim !== null && fim <= (inicio || 0)) return mostrarErroTrecho("O fim precisa ser depois do início.", campoFim), false;

    return { inicio: campoInicio.value.trim() || "0:00", fim: campoFim.value.trim() || null };
}

// Envia o link para a fila
document.getElementById("form-download").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    if (modoVarios) {
        baixarVariosLinks();
        return;
    }
    if (playlistAtual) {
        if (playlistAtual.dados) baixarPlaylist();
        return;
    }
    if (analisarLink(campoUrl.value).tipo !== "comum") return;

    const trecho = trechoEscolhido();
    if (trecho === false) return;

    const linkEnviado = campoUrl.value;
    const tituloEnviado = previaAtual?.titulo;
    const resposta = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: linkEnviado, formato: formatoEscolhido, qualidade: qualidadeEscolhida, titulo: tituloEnviado, ...trecho }),
    });
    const dados = await resposta.json();

    if (!resposta.ok) {
        alert(dados.erro);
        return;
    }

    let descricao = formatoEscolhido === "mp3" ? "MP3" : `MP4 ${qualidadeEscolhida}`;
    if (trecho) descricao += ` · trecho ${trecho.inicio} a ${trecho.fim || "fim"}`;
    criarItem(dados.id, descricao, tituloEnviado);
    // Só limpa o campo se a pessoa ainda não colou outro link enquanto o pedido ia
    if (campoUrl.value === linkEnviado) {
        campoUrl.value = "";
        aoMudarLink();
    }
});

// Downloads em andamento: id -> função que atualiza o item na lista.
// Uma consulta só pergunta o progresso de todos (playlists têm até 200).
const acompanhando = new Map();
let consultandoProgresso = false;

setInterval(async () => {
    if (!acompanhando.size || consultandoProgresso) return;
    consultandoProgresso = true;
    try {
        const resposta = await fetch("/api/progresso", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ids: [...acompanhando.keys()] }),
        });
        const todos = await resposta.json();
        for (const [id, dados] of Object.entries(todos)) {
            // A função devolve true quando o download terminou (deu certo ou não)
            if (acompanhando.get(id)?.(dados)) acompanhando.delete(id);
        }
    } catch {
        // Programa reiniciando ou fechado: tenta de novo na próxima volta
    } finally {
        consultandoProgresso = false;
        atualizarTopoDownloads();
    }
}, 700);

// "3 downloads em andamento · ✕ Cancelar todos" (aparece com 2 ou mais).
// Conta só os downloads: as compressões de vídeo usam a mesma consulta de progresso.
const topoDownloads = document.getElementById("downloads-topo");
const idsDeDownload = new Set();
const downloadsAtivos = () => [...acompanhando.keys()].filter((id) => idsDeDownload.has(id));

function atualizarTopoDownloads() {
    const ativos = downloadsAtivos().length;
    topoDownloads.classList.toggle("escondido", ativos < 2);
    document.getElementById("downloads-contagem").textContent = `${ativos} downloads em andamento`;
}

document.getElementById("cancelar-todos").addEventListener("click", async () => {
    const ativos = downloadsAtivos();
    if (!confirm(`Cancelar os ${ativos.length} downloads em andamento e na fila?`)) return;
    await Promise.all(ativos.map((id) => fetch(`/api/cancelar/${id}`, { method: "POST" }).catch(() => {})));
});

function marcarErro(item, mensagem) {
    item.classList.add("erro");
    item.querySelector(".item-status").textContent = "Erro ao baixar";
    item.querySelector(".item-acoes").textContent = mensagem || ""; // motivo (ex.: o post exige login)
}

// Cria um item na lista e acompanha o progresso dele.
// inserir: false quando quem chama coloca o item na lista (lote de uma playlist).
function criarItem(id, descricao, tituloDaPrevia, { inserir = true } = {}) {
    const item = document.createElement("li");
    item.className = "item";
    item.innerHTML = `
        <div class="item-topo">
            <span class="item-titulo"></span>
            <span class="item-status">Na fila...</span>
        </div>
        <div class="barra"><div class="barra-preenchida"></div></div>
        <div class="item-acoes">
            <button type="button" class="item-botao cancelar">✕ Cancelar</button>
        </div>
    `;
    // textContent (e não innerHTML): o título vem do vídeo e pode ter qualquer caractere
    item.querySelector(".item-titulo").textContent = tituloDaPrevia ? `${tituloDaPrevia} (${descricao})` : descricao;
    if (inserir) document.getElementById("lista-downloads").prepend(item);
    if (!id) return item; // nem entrou na fila (quem chamou marca o erro)

    const titulo = item.querySelector(".item-titulo");
    const status = item.querySelector(".item-status");
    const barra = item.querySelector(".barra-preenchida");
    const acoes = item.querySelector(".item-acoes");
    const botaoCancelar = item.querySelector(".cancelar");

    botaoCancelar.addEventListener("click", async () => {
        botaoCancelar.disabled = true;
        botaoCancelar.textContent = "Cancelando...";
        await fetch(`/api/cancelar/${id}`, { method: "POST" }).catch(() => {});
    });

    // Chamada pela consulta única de progresso; devolve true quando terminou
    idsDeDownload.add(id);
    acompanhando.set(id, (dados) => {
        status.textContent = dados.status;

        // "45.3%" -> barra em 45.3%
        if (dados.status.endsWith("%")) barra.style.width = dados.status;
        if (dados.status === "Processando arquivo...") barra.style.width = "100%";

        if (dados.status === "Pronto") {
            barra.style.width = "100%";
            item.classList.add("pronto");
            titulo.textContent = `${dados.titulo} (${descricao})`;

            // O arquivo já foi salvo na pasta Downloads (ou na pasta da playlist)
            acoes.innerHTML = `<span></span>
                <button type="button" class="item-botao">📂 Mostrar na pasta</button>`;
            // Pasta escolhida em Configurações (ou a da playlist)
            acoes.querySelector("span").textContent = `✓ Salvo em ${dados.pasta || "Downloads"}`;
            acoes.querySelector("span").title = dados.arquivo;
            acoes.querySelector("button").addEventListener("click", () => {
                fetch(`/api/mostrar/${id}`, { method: "POST" })
                    .then((r) => (r.ok ? null : r.json().then((d) => alert(d.erro))))
                    .catch(() => {});
            });
            return true;
        }

        if (dados.status === "Cancelado") {
            item.classList.add("cancelado");
            acoes.innerHTML = "";
            return true;
        }

        if (dados.status === "Erro" || dados.status === "Desconhecido") {
            marcarErro(item, dados.erro);
            const relatar = document.createElement("button");
            relatar.type = "button";
            relatar.className = "item-botao";
            relatar.textContent = "⚠ Relatar problema";
            relatar.addEventListener("click", () => abrirRelatorio(id));
            acoes.append(" ", relatar);
            return true;
        }
        return false;
    });
    atualizarTopoDownloads();
    return item;
}

// Ao abrir (ou recarregar a página): mostra os downloads que ainda não terminaram.
// Inclui os que voltaram para a fila porque o programa fechou no meio deles.
// Depois, a cada 3 segundos: mostra os que chegaram pela extensão do navegador.
function textoDoTempo(segundos) {
    const s = Math.round(segundos);
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = String(s % 60).padStart(2, "0");
    return h ? `${h}:${String(m).padStart(2, "0")}:${r}` : `${m}:${r}`;
}

async function mostrarFilaAtual({ primeiraVez = false } = {}) {
    const fila = await (await fetch("/api/fila")).json().catch(() => []);
    for (const tarefa of fila) {
        // Depois da primeira vez, só os da extensão: os do painel ele mesmo já pôs na lista
        if (acompanhando.has(tarefa.id_download) || (!primeiraVez && tarefa.origem !== "extensao")) continue;
        let descricao = tarefa.formato === "mp3" ? "MP3" : `MP4 ${tarefa.qualidade}p`;
        if (tarefa.trecho) {
            const [inicio, fim] = tarefa.trecho;
            descricao += ` · trecho ${textoDoTempo(inicio)} a ${fim === null ? "fim" : textoDoTempo(fim)}`;
        }
        criarItem(tarefa.id_download, descricao, tarefa.titulo || tarefa.url.replace(/^https?:\/\/(www\.)?/, ""));
    }
    if (!primeiraVez) return;
    const retomados = fila.filter((tarefa) => tarefa.retomado).length;
    const aviso = document.getElementById("fila-retomada");
    aviso.textContent = retomados === 1
        ? "↻ 1 download que não terminou da última vez continuou de onde parou."
        : `↻ ${retomados} downloads que não terminaram da última vez continuaram de onde pararam.`;
    aviso.classList.toggle("escondido", !retomados);
}
mostrarFilaAtual({ primeiraVez: true }).catch(() => {});
setInterval(() => mostrarFilaAtual().catch(() => {}), 3000);

// ==========================================
// RELATÓRIO DE ERRO ("Relatar problema"): monta, a pessoa confere e envia
// ==========================================
// O programa monta o texto sem dados pessoais; a pessoa pode apagar o que
// quiser antes. Enviar abre o GitHub (novo Issue) ou o e-mail já preenchido.
const fundoRelatorio = document.getElementById("relatorio");
const descricaoRelatorio = document.getElementById("relatorio-descricao");
const textoRelatorio = document.getElementById("relatorio-texto");
const mensagemRelatorio = document.getElementById("relatorio-mensagem");
const botaoEmailRelatorio = document.getElementById("relatorio-email");
let relatorioAtual = null;

async function abrirRelatorio(id = null) {
    fundoRelatorio.classList.remove("escondido");
    descricaoRelatorio.value = "";
    textoRelatorio.value = "Montando o relatório...";
    mensagemRelatorio.textContent = "";
    const resposta = await fetch("/api/relatorio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
    }).catch(() => null);
    relatorioAtual = resposta && resposta.ok ? await resposta.json() : null;
    if (!relatorioAtual) {
        textoRelatorio.value = "";
        mensagemRelatorio.textContent = "Não foi possível montar o relatório. Tente de novo.";
        return;
    }
    textoRelatorio.value = relatorioAtual.texto;
    botaoEmailRelatorio.hidden = !relatorioAtual.email;
    mensagemRelatorio.textContent = "Enviar pelo GitHub precisa de uma conta (grátis). Sem conta, use Copiar e mande o texto para quem te ajuda.";
    descricaoRelatorio.focus();
}

function fecharRelatorio() {
    fundoRelatorio.classList.add("escondido");
}

async function enviarRelatorio(destino) {
    if (!relatorioAtual) return;
    const resposta = await fetch("/api/relatorio/enviar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            destino, titulo: relatorioAtual.titulo, descricao: descricaoRelatorio.value, texto: textoRelatorio.value,
        }),
    }).catch(() => null);
    if (!resposta || !resposta.ok) {
        mensagemRelatorio.textContent = "Não foi possível abrir. Use Copiar e mande o texto para quem te ajuda.";
        return;
    }
    mensagemRelatorio.textContent = destino === "github"
        ? "✓ O GitHub abriu no navegador com o relatório preenchido: confira e clique em Create (ou Submit new issue)."
        : "✓ O seu programa de e-mail abriu com o relatório preenchido: é só enviar.";
}

async function copiarRelatorio() {
    const descricao = descricaoRelatorio.value.trim() || "(não descrito)";
    const texto = `${relatorioAtual?.titulo || "Problema no Puxaí"}\n\n## O que aconteceu\n\n${descricao}\n\n${textoRelatorio.value}`;
    try {
        await navigator.clipboard.writeText(texto);
    } catch {
        // Na janela do aplicativo a área de transferência do navegador pode estar bloqueada
        const temporario = document.createElement("textarea");
        temporario.value = texto;
        document.body.appendChild(temporario);
        temporario.select();
        document.execCommand("copy");
        temporario.remove();
    }
    mensagemRelatorio.textContent = "✓ Copiado. Cole numa mensagem (WhatsApp, e-mail...) para quem te ajuda.";
}

document.getElementById("relatorio-github").addEventListener("click", () => enviarRelatorio("github"));
botaoEmailRelatorio.addEventListener("click", () => enviarRelatorio("email"));
document.getElementById("relatorio-copiar").addEventListener("click", copiarRelatorio);
document.getElementById("relatorio-fechar").addEventListener("click", fecharRelatorio);
fundoRelatorio.addEventListener("click", (evento) => {
    if (evento.target === fundoRelatorio) fecharRelatorio(); // clicou fora da janela
});
document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !fundoRelatorio.classList.contains("escondido")) fecharRelatorio();
});
document.getElementById("config-relatar").addEventListener("click", (evento) => {
    evento.stopPropagation();
    painelConfig.classList.add("escondido");
    botaoConfig.classList.remove("aberto");
    abrirRelatorio();
});

// ==========================================
// FERRAMENTA 2: CONVERTER FOTO (HEIC -> JPG, HEIC/JPG/PNG -> WebP)
// ==========================================
const areaArquivo = document.getElementById("area-arquivo");
const campoArquivo = document.getElementById("arquivo-heic");
const textoArquivo = document.getElementById("texto-arquivo");
const listaConversao = document.getElementById("lista-conversao");
const resumoConversao = document.getElementById("resumo-conversao");
let filaConversao = Promise.resolve();
const totalConversao = { enviadas: 0, convertidas: 0 };

// Mesmas regras do servicos/conversor.py: JPG só a partir de HEIC (PNG transparente ficaria com fundo preto)
const ENTRADAS_POR_FORMATO = {
    jpg: { aceita: ".heic,.heif", texto: "<b>.heic</b>" },
    webp: { aceita: ".heic,.heif,.jpg,.jpeg,.png", texto: "<b>.heic</b>, <b>.jpg</b> ou <b>.png</b>" },
};
let formatoFoto = "jpg";

document.querySelectorAll("#formatos-foto .chip").forEach((chip) => {
    chip.addEventListener("click", () => {
        document.querySelectorAll("#formatos-foto .chip").forEach((c) => c.classList.remove("ativo"));
        chip.classList.add("ativo");
        formatoFoto = chip.dataset.formato;
        campoArquivo.accept = ENTRADAS_POR_FORMATO[formatoFoto].aceita;
        textoArquivo.innerHTML = `Clique ou arraste uma ou várias fotos ${ENTRADAS_POR_FORMATO[formatoFoto].texto}`;
    });
});

campoArquivo.addEventListener("change", () => {
    converterFotos([...campoArquivo.files]);
    campoArquivo.value = ""; // permite escolher as mesmas fotos de novo
});

// Arrastar e soltar
areaArquivo.addEventListener("dragover", (e) => {
    e.preventDefault();
    areaArquivo.classList.add("arrastando");
});
areaArquivo.addEventListener("dragleave", () => areaArquivo.classList.remove("arrastando"));
areaArquivo.addEventListener("drop", (e) => {
    e.preventDefault();
    areaArquivo.classList.remove("arrastando");
    converterFotos([...e.dataTransfer.files]);
});

function converterFotos(arquivos) {
    // Uma de cada vez, na ordem em que chegaram; o lote novo entra no topo da lista.
    // Cada foto guarda o formato escolhido na hora em que foi enviada.
    const lote = document.createDocumentFragment();
    arquivos.forEach((arquivo) => {
        const item = criarItemFoto(arquivo.name);
        lote.appendChild(item);
        const formato = formatoFoto;
        filaConversao = filaConversao.then(() => converterUma(arquivo, formato, item));
    });
    listaConversao.prepend(lote);
}

async function converterUma(arquivo, formato, item) {
    const status = item.querySelector(".item-status");
    const acoes = item.querySelector(".item-acoes");
    status.textContent = "Convertendo...";
    item.classList.add("trabalhando");

    const formulario = new FormData();
    formulario.append("arquivo", arquivo);
    formulario.append("formato", formato);

    let dados = {};
    let resposta = null;
    try {
        // ?salvar=1: a foto vai direto para a pasta Downloads, igual aos vídeos
        resposta = await fetch("/api/converter/imagem?salvar=1", { method: "POST", body: formulario });
        dados = await resposta.json();
    } catch {
        dados = { erro: "Não foi possível falar com o programa." };
    }
    item.classList.remove("trabalhando");
    totalConversao.enviadas++;

    if (!resposta || !resposta.ok) {
        item.classList.add("erro");
        status.textContent = "Erro";
        acoes.textContent = dados.erro || "Não foi possível converter.";
    } else {
        totalConversao.convertidas++;
        item.classList.add("pronto");
        status.textContent = formato === "webp" ? "✓ WebP" : "✓ JPG";
        item.querySelector(".barra-preenchida").style.width = "100%";
        mostrarSalvo(acoes, dados);
        totalConversao.pasta = dados.pasta;
    }

    const { enviadas, convertidas } = totalConversao;
    const ondeFicaram = `salvas em ${totalConversao.pasta || "Downloads"}`;
    resumoConversao.textContent = convertidas === enviadas
        ? `${convertidas} ${convertidas === 1 ? "foto convertida" : "fotos convertidas"} · ${ondeFicaram}`
        : `${convertidas} de ${enviadas} fotos convertidas · ${ondeFicaram}`;
}

// "nome.jpg em Downloads" + botão "Mostrar na pasta" (converter e comprimir)
function mostrarSalvo(acoes, dados, detalhes = `${dados.arquivo} em ${dados.pasta || "Downloads"}`) {
    acoes.innerHTML = `<span></span> <button type="button" class="item-botao">📂 Mostrar na pasta</button>`;
    acoes.querySelector("span").textContent = detalhes;
    acoes.querySelector("span").title = dados.arquivo;
    acoes.querySelector("button").addEventListener("click", () => {
        fetch(`/api/mostrar/${dados.id}`, { method: "POST" }).catch(() => {});
    });
}

// ==========================================
// FERRAMENTA 3: COMPRIMIR FOTO (uma ou várias de uma vez)
// ==========================================
const areaCompressao = document.getElementById("area-compressao");
const campoCompressao = document.getElementById("arquivos-compressao");
const listaCompressao = document.getElementById("lista-compressao");
const resumoCompressao = document.getElementById("resumo-compressao");
const dicaCompressao = document.getElementById("dica-compressao");
const DICAS_NIVEL = {
    alta: "Diferença praticamente nula, mesmo com zoom. Economiza menos.",
    equilibrado: "Menor arquivo sem diferença visível. Recomendado.",
    forte: "Arquivo bem menor; de perto, pode perder um pouco de detalhe.",
};
let nivelCompressao = "equilibrado";
let tamanhoCompressao = "original";
let filaCompressao = Promise.resolve();
const totalCompressao = { fotos: 0, antes: 0, depois: 0 };

function escolherChip(seletor, aoEscolher) {
    document.querySelectorAll(`${seletor} .chip`).forEach((chip) => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(`${seletor} .chip`).forEach((c) => c.classList.remove("ativo"));
            chip.classList.add("ativo");
            aoEscolher(chip.dataset);
        });
    });
}
escolherChip("#niveis-compressao", (d) => {
    nivelCompressao = d.nivel;
    dicaCompressao.textContent = DICAS_NIVEL[nivelCompressao];
});
escolherChip("#tamanhos-compressao", (d) => (tamanhoCompressao = d.tamanho));
dicaCompressao.textContent = DICAS_NIVEL[nivelCompressao];

campoCompressao.addEventListener("change", () => {
    comprimirFotos([...campoCompressao.files]);
    campoCompressao.value = "";
});
areaCompressao.addEventListener("dragover", (e) => {
    e.preventDefault();
    areaCompressao.classList.add("arrastando");
});
areaCompressao.addEventListener("dragleave", () => areaCompressao.classList.remove("arrastando"));
areaCompressao.addEventListener("drop", (e) => {
    e.preventDefault();
    areaCompressao.classList.remove("arrastando");
    comprimirFotos([...e.dataTransfer.files]);
});

function comprimirFotos(arquivos) {
    // Uma de cada vez (cada foto já testa várias qualidades), na ordem em que chegaram.
    // O lote novo entra no topo da lista, mantendo essa ordem.
    const lote = document.createDocumentFragment();
    arquivos.forEach((arquivo) => {
        const item = criarItemFoto(arquivo.name);
        lote.appendChild(item);
        const nivel = nivelCompressao;
        const tamanho = tamanhoCompressao;
        filaCompressao = filaCompressao.then(() => comprimirUma(arquivo, nivel, tamanho, item));
    });
    listaCompressao.prepend(lote);
}

// Uma linha da lista de fotos (converter e comprimir)
function criarItemFoto(nome) {
    const item = document.createElement("li");
    item.className = "item";
    item.innerHTML = `
        <div class="item-topo">
            <span class="item-titulo"></span>
            <span class="item-status">Na fila...</span>
        </div>
        <div class="barra barra-economia"><div class="barra-preenchida"></div></div>
        <div class="item-acoes"></div>
    `;
    item.querySelector(".item-titulo").textContent = nome; // textContent: o nome pode ter qualquer caractere
    return item;
}

async function comprimirUma(arquivo, nivel, tamanho, item) {
    const status = item.querySelector(".item-status");
    const barra = item.querySelector(".barra-preenchida");
    const acoes = item.querySelector(".item-acoes");
    status.textContent = "Comprimindo...";
    item.classList.add("trabalhando");

    const formulario = new FormData();
    formulario.append("arquivo", arquivo);
    formulario.append("nivel", nivel);
    formulario.append("tamanho", tamanho);

    let dados = {};
    let resposta = null;
    try {
        resposta = await fetch("/api/comprimir?salvar=1", { method: "POST", body: formulario });
        dados = await resposta.json();
    } catch {
        dados = { erro: "Não foi possível falar com o programa." };
    }
    item.classList.remove("trabalhando");

    if (!resposta || !resposta.ok) {
        item.classList.add("erro");
        status.textContent = "Erro";
        acoes.textContent = dados.erro || "Não foi possível comprimir.";
        return;
    }

    totalCompressao.fotos++;
    totalCompressao.antes += dados.antes;
    totalCompressao.depois += dados.depois;
    if (dados.pasta) totalCompressao.pasta = dados.pasta;
    atualizarResumoCompressao();

    if (dados.ja_otimizada) {
        status.textContent = "Já estava otimizada";
        item.classList.add("otimizada");
        barra.style.width = "100%";
        acoes.textContent = `${formatarTamanho(dados.antes)} · não deu para diminuir sem perder qualidade; nada foi salvo.`;
        return;
    }

    // A barra mostra o tamanho novo em relação ao original
    const economia = Math.round((1 - dados.depois / dados.antes) * 100);
    item.classList.add("pronto");
    status.textContent = `−${economia}%`;
    barra.style.width = `${Math.max(2, 100 - economia)}%`;
    mostrarSalvo(acoes, dados,
        `${formatarTamanho(dados.antes)} → ${formatarTamanho(dados.depois)} · ${dados.largura}×${dados.altura}`);
}

function atualizarResumoCompressao() {
    const { fotos, antes, depois } = totalCompressao;
    const economia = antes ? Math.round((1 - depois / antes) * 100) : 0;
    resumoCompressao.textContent = `${fotos} ${fotos === 1 ? "foto" : "fotos"} · `
        + `economizou ${formatarTamanho(antes - depois)} (−${economia}%) · salvas em ${totalCompressao.pasta || "Downloads"}`;
}

// ==========================================
// FERRAMENTA 4: COMPRIMIR VÍDEO
// ==========================================
const campoVideos = document.getElementById("arquivos-video");
const areaVideo = document.getElementById("area-video");
const listaVideo = document.getElementById("lista-video");
const resumoVideo = document.getElementById("resumo-video");
const dicaVideo = document.getElementById("dica-video");
const campoOutroMb = document.getElementById("outro-mb");
const opcoesVideo = { modo: "tamanho", tamanho: "whatsapp", qualidade: "equilibrada", resolucao: "original" };
const totalVideo = { videos: 0, antes: 0, depois: 0, pasta: null };
let filaEnvioVideo = Promise.resolve();

const DICAS_VIDEO = {
    tamanho: "O vídeo é ajustado para caber no tamanho. Se for longo, a resolução diminui sozinha para continuar nítido.",
    alta: "Quase sem diferença do original. Economiza menos.",
    equilibrada: "Bem menor, sem diferença visível na tela do celular. Recomendado.",
    forte: "O menor arquivo; pode perder um pouco de detalhe.",
};

function atualizarOpcoesVideo() {
    const porTamanho = opcoesVideo.modo === "tamanho";
    document.getElementById("opcoes-tamanho-video").classList.toggle("escondido", !porTamanho);
    document.getElementById("opcoes-qualidade-video").classList.toggle("escondido", porTamanho);
    document.getElementById("campo-outro-mb").classList.toggle("escondido", opcoesVideo.tamanho !== "outro");
    dicaVideo.textContent = porTamanho ? DICAS_VIDEO.tamanho : DICAS_VIDEO[opcoesVideo.qualidade];
}
escolherChip("#modos-video", (d) => { opcoesVideo.modo = d.modo; atualizarOpcoesVideo(); });
escolherChip("#tamanhos-video", (d) => {
    opcoesVideo.tamanho = d.tamanho;
    atualizarOpcoesVideo();
    if (d.tamanho === "outro") campoOutroMb.focus();
});
escolherChip("#qualidades-video", (d) => { opcoesVideo.qualidade = d.qualidade; atualizarOpcoesVideo(); });
escolherChip("#resolucoes-video", (d) => (opcoesVideo.resolucao = d.resolucao));
atualizarOpcoesVideo();

campoVideos.addEventListener("change", () => {
    comprimirVideos([...campoVideos.files]);
    campoVideos.value = "";
});
areaVideo.addEventListener("dragover", (e) => {
    e.preventDefault();
    areaVideo.classList.add("arrastando");
});
areaVideo.addEventListener("dragleave", () => areaVideo.classList.remove("arrastando"));
areaVideo.addEventListener("drop", (e) => {
    e.preventDefault();
    areaVideo.classList.remove("arrastando");
    comprimirVideos([...e.dataTransfer.files]);
});

function comprimirVideos(arquivos) {
    // Cada vídeo leva as opções escolhidas na hora em que foi enviado
    const opcoes = { ...opcoesVideo, tamanho: opcoesVideo.tamanho === "outro" ? campoOutroMb.value : opcoesVideo.tamanho };
    const lote = document.createDocumentFragment();
    arquivos.forEach((arquivo) => {
        const item = criarItemFoto(arquivo.name);
        lote.appendChild(item);
        // Envia um de cada vez (vídeos podem ter centenas de MB); a compressão em si também é um por vez
        filaEnvioVideo = filaEnvioVideo.then(() => enviarVideo(arquivo, opcoes, item));
    });
    listaVideo.prepend(lote);
}

async function enviarVideo(arquivo, opcoes, item) {
    const status = item.querySelector(".item-status");
    const acoes = item.querySelector(".item-acoes");
    status.textContent = "Enviando...";

    const formulario = new FormData();
    formulario.append("arquivo", arquivo);
    Object.entries(opcoes).forEach(([chave, valor]) => formulario.append(chave, valor));

    const resposta = await fetch("/api/comprimir-video", { method: "POST", body: formulario }).catch(() => null);
    const dados = resposta ? await resposta.json().catch(() => ({})) : {};
    if (!resposta || !resposta.ok) {
        item.classList.add("erro");
        status.textContent = "Erro";
        acoes.textContent = dados.erro || "Não foi possível enviar o vídeo.";
        return;
    }
    acompanharVideo(dados.id, item);
}

function acompanharVideo(id, item) {
    const status = item.querySelector(".item-status");
    const barra = item.querySelector(".barra-preenchida");
    const acoes = item.querySelector(".item-acoes");
    status.textContent = "Na fila...";
    acoes.innerHTML = `<button type="button" class="item-botao cancelar">✕ Cancelar</button>`;
    const botaoCancelar = acoes.querySelector("button");
    botaoCancelar.addEventListener("click", () => {
        botaoCancelar.disabled = true;
        botaoCancelar.textContent = "Cancelando...";
        fetch(`/api/cancelar/${id}`, { method: "POST" }).catch(() => {});
    });

    acompanhando.set(id, (dados) => {
        if (dados.status.endsWith("%")) {
            status.textContent = `Comprimindo ${Math.floor(parseFloat(dados.status))}%`;
            barra.style.width = dados.status;
            return false;
        }
        if (dados.status === "Na fila...") return false;

        if (dados.status === "Cancelado") {
            item.classList.add("cancelado");
            status.textContent = "Cancelado";
            acoes.innerHTML = "";
            return true;
        }
        if (dados.status !== "Pronto") {
            item.classList.add("erro");
            status.textContent = "Erro";
            acoes.textContent = dados.erro || "Não foi possível comprimir.";
            return true;
        }

        const extra = dados.extra || {};
        totalVideo.videos++;
        totalVideo.antes += extra.antes || 0;
        totalVideo.depois += extra.depois || extra.antes || 0;
        if (dados.pasta) totalVideo.pasta = dados.pasta;
        atualizarResumoVideo();

        if (extra.ja_otimizada) {
            item.classList.add("otimizada");
            status.textContent = "Já estava bom";
            barra.style.width = "100%";
            acoes.textContent = `${formatarTamanho(extra.antes)} · já cabe no tamanho ou já está bem comprimido; nada foi salvo.`;
            return true;
        }
        // A barra mostra o tamanho novo em relação ao original
        const economia = Math.round((1 - extra.depois / extra.antes) * 100);
        item.classList.add("pronto");
        status.textContent = `−${economia}%`;
        barra.style.width = `${Math.max(2, 100 - economia)}%`;
        mostrarSalvo(acoes, dados,
            `${formatarTamanho(extra.antes)} → ${formatarTamanho(extra.depois)} · ${extra.largura}×${extra.altura}`);
        return true;
    });
}

function atualizarResumoVideo() {
    const { videos, antes, depois } = totalVideo;
    const economia = antes ? Math.round((1 - depois / antes) * 100) : 0;
    resumoVideo.textContent = `${videos} ${videos === 1 ? "vídeo" : "vídeos"} · `
        + `economizou ${formatarTamanho(antes - depois)} (−${economia}%) · salvos em ${totalVideo.pasta || "Downloads"}`;
}

// ==========================================
// MEUS DOWNLOADS: histórico do que o programa salvou
// ==========================================
const listaHistorico = document.getElementById("lista-historico");
const historicoVazio = document.getElementById("historico-vazio");
const ICONES_HISTORICO = { video: "▶", musica: "♪", foto: "▣", outro: "•" };
let itensHistorico = [];
let filtroHistorico = "todos";

document.querySelectorAll("#filtros-historico .chip").forEach((chip) => {
    chip.addEventListener("click", () => {
        document.querySelectorAll("#filtros-historico .chip").forEach((c) => c.classList.remove("ativo"));
        chip.classList.add("ativo");
        filtroHistorico = chip.dataset.tipo;
        mostrarHistorico();
    });
});

document.getElementById("limpar-historico").addEventListener("click", async () => {
    if (!confirm("Limpar a lista? Os arquivos continuam na pasta Downloads.")) return;
    await fetch("/api/historico", { method: "DELETE" }).catch(() => {});
    carregarHistorico();
});

async function carregarHistorico() {
    try {
        itensHistorico = await (await fetch("/api/historico")).json();
    } catch {
        itensHistorico = [];
    }
    mostrarHistorico();
}

// 35651584 -> "34 MB"
function formatarTamanho(bytes) {
    if (bytes == null) return "";
    const unidades = ["B", "KB", "MB", "GB"];
    let valor = bytes;
    let i = 0;
    while (valor >= 1024 && i < unidades.length - 1) {
        valor /= 1024;
        i++;
    }
    return `${valor.toLocaleString("pt-BR", { maximumFractionDigits: valor < 10 && i > 1 ? 1 : 0 })} ${unidades[i]}`;
}

function formatarData(segundos) {
    return new Date(segundos * 1000).toLocaleString("pt-BR", {
        day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
    });
}

function mostrarHistorico() {
    const itens = itensHistorico.filter((i) => filtroHistorico === "todos" || i.tipo === filtroHistorico);
    listaHistorico.replaceChildren();
    document.getElementById("limpar-historico").hidden = itensHistorico.length === 0;

    historicoVazio.classList.toggle("escondido", itens.length > 0);
    historicoVazio.textContent = itensHistorico.length === 0
        ? "Nada por aqui ainda. Os vídeos, músicas e fotos que você salvar pelo programa aparecem nesta aba."
        : "Nenhum arquivo desse tipo na lista.";

    itens.forEach((dados) => {
        const item = document.createElement("li");
        item.className = "item historico-item" + (dados.existe ? "" : " ausente");
        item.innerHTML = `
            <div class="historico-linha">
                <span class="historico-icone"></span>
                <div class="historico-info">
                    <span class="item-titulo"></span>
                    <span class="historico-detalhes"></span>
                </div>
            </div>
            <div class="item-acoes"></div>
        `;
        // textContent (e não innerHTML): o título vem do vídeo e pode ter qualquer caractere
        item.querySelector(".historico-icone").textContent = ICONES_HISTORICO[dados.tipo] || ICONES_HISTORICO.outro;
        const titulo = item.querySelector(".item-titulo");
        titulo.textContent = dados.titulo;
        titulo.title = dados.arquivo;
        item.querySelector(".historico-detalhes").textContent = dados.existe
            ? [dados.formato, formatarData(dados.data), formatarTamanho(dados.tamanho)].join(" · ")
            : `${dados.formato} · ${formatarData(dados.data)} · arquivo não encontrado (movido ou apagado)`;

        const acoes = item.querySelector(".item-acoes");
        const acao = (texto, aoClicar, classe = "") => {
            const botao = document.createElement("button");
            botao.type = "button";
            botao.className = `item-botao ${classe}`.trim();
            botao.textContent = texto;
            botao.addEventListener("click", aoClicar);
            acoes.appendChild(botao);
        };
        const chamar = (rota) => fetch(rota, { method: "POST" })
            .then((r) => (r.ok ? null : r.json().then((d) => { alert(d.erro); carregarHistorico(); })))
            .catch(() => {});

        if (dados.existe) {
            acao("▶ Abrir", () => chamar(`/api/abrir/${dados.id}`));
            acao("📂 Mostrar na pasta", () => chamar(`/api/mostrar/${dados.id}`));
        }
        acao("✕ Remover da lista", async () => {
            await fetch(`/api/historico/${dados.id}`, { method: "DELETE" }).catch(() => {});
            carregarHistorico();
        }, "remover");

        listaHistorico.appendChild(item);
    });
}

// ==========================================
// PROGRAMA: manter aberto / encerrar
// ==========================================

// Na janela própria do programa, fechar a janela já encerra tudo: o botão
// "Encerrar" some. No navegador, o painel avisa a cada 30 segundos que continua
// aberto; sem esse aviso por 3 minutos (e sem downloads), o programa fecha sozinho.
function avisarQuePainelEstaAberto() {
    fetch("/api/ping", { method: "POST" }).catch(() => {});
}

// ==========================================
// CONFIGURAÇÕES: abrir na janela do aplicativo ou no navegador
// ==========================================
const botaoConfig = document.getElementById("config");
const painelConfig = document.getElementById("configuracoes");
const botaoAbrirNavegador = document.getElementById("abrir-navegador");
const botaoTrocarAgora = document.getElementById("config-trocar");
const dicaConfig = document.getElementById("config-dica");
let modoAtual = { janela: false, preferencia: "janela" };

fetch("/api/modo")
    .then((r) => r.json())
    .then((modo) => {
        modoAtual = modo;
        if (modo.janela) {
            document.getElementById("encerrar").hidden = true;
            botaoAbrirNavegador.hidden = false; // atalho ↗ só faz sentido na janela
        } else {
            avisarQuePainelEstaAberto();
            setInterval(avisarQuePainelEstaAberto, 30000);
        }
        montarConfiguracoes();
    })
    .catch(() => {});

function montarConfiguracoes() {
    document.querySelectorAll("#config-modo .chip").forEach((chip) => {
        chip.classList.toggle("ativo", chip.dataset.modo === modoAtual.preferencia);
    });
    botaoTrocarAgora.textContent = modoAtual.janela ? "↗ Abrir no navegador agora" : "Reabrir como aplicativo";
}

botaoConfig.addEventListener("click", (evento) => {
    evento.stopPropagation();
    const abrir = painelConfig.classList.contains("escondido");
    painelConfig.classList.toggle("escondido", !abrir);
    botaoConfig.classList.toggle("aberto", abrir);
    painelNotificacoes.classList.add("escondido");
    sino.classList.remove("aberto");
    dicaConfig.textContent = "";
});

// ==========================================
// CONFIGURAÇÕES: tema claro, escuro ou automático (segue o sistema)
// ==========================================
// A página já chega do programa com data-tema="claro"|"escuro" (sem piscar o
// tema errado). Aqui só troca na hora e acompanha o sistema no automático.
const raiz = document.documentElement;
const dicaTema = document.getElementById("config-tema-dica");
const sistemaEscuro = window.matchMedia("(prefers-color-scheme: dark)");

function aplicarTema(escolhido) {
    raiz.dataset.temaEscolhido = escolhido;
    raiz.dataset.tema = escolhido === "automatico" ? (sistemaEscuro.matches ? "escuro" : "claro") : escolhido;
    document.querySelectorAll("#config-tema .chip").forEach((chip) => {
        chip.classList.toggle("ativo", chip.dataset.tema === escolhido);
    });
    dicaTema.textContent = escolhido === "automatico"
        ? `Segue o sistema (agora: ${raiz.dataset.tema === "escuro" ? "escuro" : "claro"}).`
        : "";
}

// Automático: o sistema mudou de claro para escuro (ou o contrário) com o Puxaí aberto
sistemaEscuro.addEventListener("change", () => {
    if (raiz.dataset.temaEscolhido === "automatico") aplicarTema("automatico");
});

document.querySelectorAll("#config-tema .chip").forEach((chip) => {
    chip.addEventListener("click", async () => {
        const anterior = raiz.dataset.temaEscolhido;
        aplicarTema(chip.dataset.tema); // troca na hora; salva em seguida
        const resposta = await fetch("/api/preferencias", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tema: chip.dataset.tema }),
        }).catch(() => null);
        if (!resposta || !resposta.ok) {
            aplicarTema(anterior);
            dicaTema.textContent = "Não foi possível salvar. Tente de novo.";
        }
    });
});

aplicarTema(raiz.dataset.temaEscolhido || "automatico");

// Avisar quando copiar um link de vídeo (ligado por padrão)
const caixaDetectarLink = document.getElementById("config-detectar-link");
fetch("/api/preferencias")
    .then((r) => r.json())
    .then((dados) => {
        caixaDetectarLink.checked = dados.detectar_link !== false;
        mostrarEstatisticas(dados);
    })
    .catch(() => {});
caixaDetectarLink.addEventListener("change", async () => {
    const ligado = caixaDetectarLink.checked;
    if (!ligado) esconderLinkCopiado();
    const resposta = await fetch("/api/preferencias", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ detectar_link: ligado }),
    }).catch(() => null);
    if (!resposta || !resposta.ok) caixaDetectarLink.checked = !ligado;
});

// Estatísticas anônimas: só existem se o programa tiver para onde enviar.
// Pergunta uma vez (aviso no topo); depois, a caixinha nas Configurações.
const avisoEstatisticas = document.getElementById("aviso-estatisticas");
const caixaEstatisticas = document.getElementById("config-estatisticas");

function mostrarEstatisticas(dados) {
    if (!dados.estatisticas_disponivel) return;
    document.getElementById("config-estatisticas-linha").hidden = false;
    caixaEstatisticas.checked = dados.estatisticas === true;
    avisoEstatisticas.classList.toggle("escondido", dados.estatisticas !== null);
}

async function salvarEstatisticas(ligado) {
    const resposta = await fetch("/api/preferencias", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estatisticas: ligado }),
    }).catch(() => null);
    if (!resposta || !resposta.ok) return false;
    mostrarEstatisticas(await resposta.json());
    return true;
}

document.getElementById("estatisticas-sim").addEventListener("click", () => salvarEstatisticas(true));
document.getElementById("estatisticas-nao").addEventListener("click", () => salvarEstatisticas(false));
caixaEstatisticas.addEventListener("change", async () => {
    if (!(await salvarEstatisticas(caixaEstatisticas.checked))) caixaEstatisticas.checked = !caixaEstatisticas.checked;
});

// ==========================================
// CONFIGURAÇÕES: onde salvar os arquivos
// ==========================================
const listaPastas = document.getElementById("config-pastas");
const dicaPastas = document.getElementById("config-pastas-dica");
const PASTAS_POR_MODO = {
    uma: [["tudo", "Todos os arquivos"]],
    separadas: [["video", "Vídeos (MP4)"], ["musica", "Músicas (MP3)"], ["foto", "Fotos"]],
};
let pastas = null; // resposta de /api/pastas

// "C:\Users\Fulano\Videos\Puxaí\Clipes" -> "…\Videos\Puxaí\Clipes" (o caminho inteiro aparece ao parar o mouse)
function caminhoCurto(caminho) {
    const partes = caminho.split(/[\\/]/).filter(Boolean);
    return partes.length > 3 ? `…\\${partes.slice(-3).join("\\")}` : caminho;
}

async function salvarPastas(mudancas) {
    const resposta = await fetch("/api/pastas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mudancas),
    }).catch(() => null);
    const dados = resposta ? await resposta.json().catch(() => ({})) : {};
    if (!resposta || !resposta.ok) {
        dicaPastas.textContent = dados.erro || "Não foi possível salvar. Tente de novo.";
        return false;
    }
    pastas = dados;
    return true;
}

// Monta as linhas (uma ou três) só quando o modo muda; depois, só atualiza os textos.
// (Recriar o botão clicado fecharia o painel: o clique "sairia" de dentro dele.)
function montarPastas() {
    document.querySelectorAll("#config-pastas-modo .chip").forEach((chip) => {
        chip.classList.toggle("ativo", chip.dataset.modoPasta === pastas.modo);
    });
    if (listaPastas.dataset.modo !== pastas.modo) {
        listaPastas.dataset.modo = pastas.modo;
        listaPastas.replaceChildren(...PASTAS_POR_MODO[pastas.modo].map(([tipo, rotulo]) => {
            const linha = document.createElement("div");
            linha.className = "pasta-linha";
            linha.dataset.tipo = tipo;
            linha.innerHTML = `
                <span class="pasta-rotulo"></span>
                <span class="pasta-caminho"></span>
                <span class="pasta-botoes">
                    <button type="button" class="item-botao pasta-escolher">Escolher…</button>
                    <button type="button" class="botao-texto pasta-padrao">Usar Downloads</button>
                </span>
            `;
            linha.querySelector(".pasta-rotulo").textContent = rotulo;
            linha.querySelector(".pasta-escolher").addEventListener("click", () => escolherPasta(tipo, rotulo, linha));
            linha.querySelector(".pasta-padrao").addEventListener("click", async () => {
                if (await salvarPastas({ [tipo]: "" })) {
                    montarPastas();
                    dicaPastas.textContent = `✓ ${rotulo}: de volta para Downloads.`;
                }
            });
            return linha;
        }));
    }
    listaPastas.querySelectorAll(".pasta-linha").forEach((linha) => {
        const caminho = pastas[linha.dataset.tipo];
        const texto = linha.querySelector(".pasta-caminho");
        texto.textContent = caminhoCurto(caminho);
        texto.title = caminho;
        linha.querySelector(".pasta-padrao").hidden = caminho === pastas.padrao;
    });
}

async function escolherPasta(tipo, rotulo, linha) {
    const botao = linha.querySelector(".pasta-escolher");
    botao.disabled = true;
    botao.textContent = "Escolha na janela…";
    dicaPastas.textContent = "";
    try {
        const resposta = await fetch("/api/pastas/escolher", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ atual: pastas[tipo] }),
        });
        const dados = await resposta.json();
        if (!resposta.ok) {
            dicaPastas.textContent = dados.erro;
        } else if (dados.pasta && (await salvarPastas({ [tipo]: dados.pasta }))) {
            montarPastas();
            dicaPastas.textContent = `✓ ${rotulo} vão para ${dados.pasta}`;
        }
    } catch {
        dicaPastas.textContent = "Não foi possível abrir a janela de escolher pasta.";
    } finally {
        botao.disabled = false;
        botao.textContent = "Escolher…";
    }
}

document.querySelectorAll("#config-pastas-modo .chip").forEach((chip) => {
    chip.addEventListener("click", async () => {
        if (await salvarPastas({ modo: chip.dataset.modoPasta })) {
            montarPastas();
            dicaPastas.textContent = pastas.modo === "uma"
                ? "✓ Tudo vai para a mesma pasta."
                : "✓ Escolha uma pasta para cada tipo de arquivo.";
        }
    });
});

fetch("/api/pastas")
    .then((r) => r.json())
    .then((dados) => {
        pastas = dados;
        montarPastas();
    })
    .catch(() => {});

// Escolher como o programa abre (vale a partir da próxima vez)
document.querySelectorAll("#config-modo .chip").forEach((chip) => {
    chip.addEventListener("click", async () => {
        const resposta = await fetch("/api/preferencias", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ modo_abertura: chip.dataset.modo }),
        }).catch(() => null);
        if (!resposta || !resposta.ok) {
            dicaConfig.textContent = "Não foi possível salvar. Tente de novo.";
            return;
        }
        modoAtual.preferencia = chip.dataset.modo;
        montarConfiguracoes();
        dicaConfig.textContent = chip.dataset.modo === "navegador"
            ? "✓ Salvo. Das próximas vezes, o programa abre no navegador."
            : "✓ Salvo. Das próximas vezes, o programa abre na janela do aplicativo.";
    });
});

async function abrirNoNavegadorAgora() {
    // A janela fecha e o painel abre no navegador; o programa continua rodando
    await fetch("/api/abrir-no-navegador", { method: "POST" }).catch(() => {});
}

async function reabrirComoAplicativo() {
    await fetch("/api/reabrir-como-aplicativo", { method: "POST" }).catch(() => {});
    document.body.innerHTML = `
        <div class="brilho"></div>
        <div class="encerrado">
            <h1>Abrindo como aplicativo...</h1>
            <p>A janela do programa vai abrir em alguns segundos.</p>
        </div>
    `;
    const mensagem = document.querySelector(".encerrado p");

    // Espera o programa fechar e voltar já como aplicativo; aí fecha esta aba
    // sozinha. O navegador só deixa fechar a aba que o programa abriu (sem
    // outras páginas no histórico); se não deixar, fica o aviso para fechar.
    const pausa = (ms) => new Promise((pronto) => setTimeout(pronto, ms));
    const inicio = Date.now();
    let caiu = false;
    let voltouEm = null;

    while (Date.now() - inicio < 30000) {
        await pausa(700);
        try {
            const modo = await (await fetch("/api/modo", { cache: "no-store" })).json();
            if (!caiu) continue; // ainda é o programa antigo, fechando
            voltouEm ??= Date.now();
            // O servidor volta um instante antes de a janela existir: espera ela
            // aparecer (se não aparecer, o programa abriu no navegador)
            if (!modo.janela && Date.now() - voltouEm < 8000) continue;

            document.querySelector(".encerrado h1").textContent = "Pronto!";
            mensagem.textContent = modo.janela
                ? "O aplicativo foi aberto. Pode fechar esta aba."
                : "O painel abriu em outra aba. Pode fechar esta.";
            window.close();
            return;
        } catch {
            caiu = true;
        }
    }
    mensagem.textContent = "O aplicativo não abriu. Abra pelo atalho Puxaí na Área de Trabalho.";
}

botaoAbrirNavegador.addEventListener("click", abrirNoNavegadorAgora);
botaoTrocarAgora.addEventListener("click", () =>
    modoAtual.janela ? abrirNoNavegadorAgora() : reabrirComoAplicativo()
);

document.getElementById("encerrar").addEventListener("click", async () => {
    if (!confirm("Encerrar o programa? Downloads em andamento serão interrompidos.")) return;

    await fetch("/api/encerrar", { method: "POST" }).catch(() => {});
    document.body.innerHTML = `
        <div class="brilho"></div>
        <div class="encerrado">
            <h1>Programa encerrado</h1>
            <p>Pode fechar esta aba. Para usar de novo, abra o atalho Puxaí.</p>
        </div>
    `;
});

// ==========================================
// ATUALIZAÇÃO DO PROGRAMA E NOTIFICAÇÕES
// ==========================================
const avisoAtualizacao = document.getElementById("aviso-atualizacao");
const botaoAtualizar = document.getElementById("botao-atualizar");
const botaoDepois = document.getElementById("botao-depois");
const mensagemAtualizacao = document.getElementById("atualizacao-mensagem");
const sino = document.getElementById("sino");
const sinoPonto = document.getElementById("sino-ponto");
const painelNotificacoes = document.getElementById("notificacoes");
const conteudoNotificacoes = document.getElementById("notificacoes-conteudo");
const toast = document.getElementById("toast");

// Com o programa aberto, confere se saiu versão nova a cada 30 minutos
const VERIFICAR_A_CADA = 30 * 60 * 1000;

let infoVersao = null;
let toastMostradoPara = null; // a notificação aparece uma vez por versão
let atualizando = false;

async function verificarAtualizacao(forcar = false) {
    try {
        infoVersao = await (await fetch(`/api/versao${forcar ? "?forcar=1" : ""}`)).json();
    } catch {
        return;
    }
    mostrarVersao();
}

function mostrarVersao() {
    const dados = infoVersao;
    document.getElementById("versao").textContent = `Versão ${dados.atual}`;
    sinoPonto.hidden = !dados.disponivel;
    montarPainelNotificacoes();
    if (!dados.disponivel || atualizando) return;

    // Aviso no topo do painel
    document.getElementById("atualizacao-titulo").textContent = `✨ Nova versão ${dados.nova} disponível`;
    preencherNovidades(document.getElementById("atualizacao-novidades"), dados.novidades);
    botaoAtualizar.hidden = !dados.pode_atualizar;
    mensagemAtualizacao.textContent = dados.pode_atualizar ? "" : dados.motivo;

    // "Depois": o aviso e a notificação somem; o sino continua com a bolinha
    if (dados.adiada) {
        avisoAtualizacao.classList.add("escondido");
        return;
    }
    avisoAtualizacao.classList.remove("escondido");

    if (toastMostradoPara !== dados.nova) {
        toastMostradoPara = dados.nova;
        document.getElementById("toast-titulo").textContent = `✨ Nova versão ${dados.nova} disponível`;
        const primeira = dados.novidades[0];
        document.getElementById("toast-descricao").textContent = primeira
            ? primeira + (dados.novidades.length > 1 ? " e mais novidades." : "")
            : "";
        document.getElementById("toast-atualizar").hidden = !dados.pode_atualizar;
        toast.classList.remove("escondido");
    }
}

function preencherNovidades(lista, novidades) {
    lista.innerHTML = "";
    novidades.forEach((novidade) => {
        const item = document.createElement("li");
        item.textContent = novidade; // textContent: o texto vem de fora
        lista.appendChild(item);
    });
}

// Conteúdo do painelzinho que abre no sino
function montarPainelNotificacoes() {
    const dados = infoVersao;
    conteudoNotificacoes.innerHTML = "";
    const item = document.createElement("div");
    item.className = "notificacao-item";

    if (dados.disponivel) {
        item.innerHTML = `<strong></strong><ul></ul><div class="atualizacao-botoes"></div>`;
        item.querySelector("strong").textContent = `✨ Nova versão ${dados.nova} disponível`;
        preencherNovidades(item.querySelector("ul"), dados.novidades);
        if (dados.pode_atualizar) {
            const botao = document.createElement("button");
            botao.type = "button";
            botao.className = "botao-atualizar";
            botao.textContent = "⬆ Atualizar agora";
            botao.addEventListener("click", iniciarAtualizacao);
            item.querySelector(".atualizacao-botoes").appendChild(botao);
        } else {
            const motivo = document.createElement("p");
            motivo.textContent = dados.motivo;
            item.appendChild(motivo);
        }
    } else {
        item.innerHTML = `<p></p><button type="button" class="botao-depois">↻ Verificar agora</button>`;
        item.querySelector("p").textContent = dados.motivo || `✓ Você está na versão mais recente (${dados.atual}).`;
        const botaoVerificar = item.querySelector("button");
        botaoVerificar.addEventListener("click", async () => {
            botaoVerificar.disabled = true;
            botaoVerificar.textContent = "Verificando...";
            await verificarAtualizacao(true);
        });
    }
    conteudoNotificacoes.appendChild(item);
}

sino.addEventListener("click", (evento) => {
    evento.stopPropagation();
    const abrir = painelNotificacoes.classList.contains("escondido");
    painelNotificacoes.classList.toggle("escondido", !abrir);
    sino.classList.toggle("aberto", abrir);
    if (abrir) toast.classList.add("escondido");
    painelConfig.classList.add("escondido");
    botaoConfig.classList.remove("aberto");
});

// Clicar fora fecha os painelzinhos (notificações e configurações)
document.addEventListener("click", (evento) => {
    if (!painelNotificacoes.contains(evento.target)) {
        painelNotificacoes.classList.add("escondido");
        sino.classList.remove("aberto");
    }
    if (!painelConfig.contains(evento.target)) {
        painelConfig.classList.add("escondido");
        botaoConfig.classList.remove("aberto");
    }
});

async function adiarAtualizacao() {
    toast.classList.add("escondido");
    avisoAtualizacao.classList.add("escondido");
    if (!infoVersao || !infoVersao.nova) return;
    infoVersao.adiada = true;
    await fetch("/api/versao/adiar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ versao: infoVersao.nova }),
    }).catch(() => {});
}

botaoDepois.addEventListener("click", adiarAtualizacao);
document.getElementById("toast-depois").addEventListener("click", adiarAtualizacao);
document.getElementById("toast-atualizar").addEventListener("click", iniciarAtualizacao);
botaoAtualizar.addEventListener("click", iniciarAtualizacao);

async function iniciarAtualizacao() {
    if (atualizando) return;
    atualizando = true;

    // O andamento aparece no aviso do topo
    toast.classList.add("escondido");
    painelNotificacoes.classList.add("escondido");
    avisoAtualizacao.classList.remove("escondido");
    avisoAtualizacao.scrollIntoView({ behavior: "smooth", block: "start" });
    botaoDepois.hidden = true;
    botaoAtualizar.hidden = false;
    botaoAtualizar.disabled = true;
    botaoAtualizar.textContent = "Atualizando...";
    mensagemAtualizacao.textContent = "Baixando a versão nova. Não feche o programa.";

    // Programa gerado: o download tem dezenas de MB; mostra a porcentagem enquanto baixa
    const acompanhar = setInterval(async () => {
        const andamento = await (await fetch("/api/atualizar/andamento", { cache: "no-store" })).json().catch(() => null);
        if (!andamento || !andamento.etapa) return;
        if (andamento.etapa === "extraindo") {
            mensagemAtualizacao.textContent = "Preparando a versão nova. Não feche o programa.";
        } else if (andamento.total) {
            const mb = (bytes) => Math.round(bytes / 1048576);
            mensagemAtualizacao.textContent = `Baixando a versão nova: ${Math.floor((andamento.baixado / andamento.total) * 100)}% `
                + `(${mb(andamento.baixado)} de ${mb(andamento.total)} MB). Não feche o programa.`;
        }
    }, 700);

    const resposta = await fetch("/api/atualizar", { method: "POST" }).catch(() => null);
    clearInterval(acompanhar);
    const dados = resposta ? await resposta.json().catch(() => ({})) : {};

    if (!resposta || !resposta.ok) {
        atualizando = false;
        mensagemAtualizacao.textContent = dados.erro || "Não foi possível atualizar. Tente de novo.";
        botaoAtualizar.disabled = false;
        botaoAtualizar.textContent = "⬆ Tentar de novo";
        botaoDepois.hidden = false;
        return;
    }

    botaoAtualizar.hidden = true;
    mensagemAtualizacao.textContent = `✓ Atualizado para a versão ${dados.versao}. Reiniciando o programa...`;

    // No navegador: espera o programa voltar e recarrega a página.
    // Na janela própria, ela fecha e abre de novo sozinha.
    let caiu = false;
    const esperar = setInterval(async () => {
        try {
            await fetch("/api/modo", { cache: "no-store" });
            if (caiu) {
                clearInterval(esperar);
                location.reload();
            }
        } catch {
            caiu = true;
        }
    }, 1000);
}

carregarQualidades();
verificarAtualizacao();
setInterval(() => verificarAtualizacao(), VERIFICAR_A_CADA);
