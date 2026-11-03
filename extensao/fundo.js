// Extensão "Baixar com o Puxaí": a parte que fica rodando por trás.
//
// Manda o link para o Puxaí (o programa, aberto no mesmo computador), pela
// API dele em http://127.0.0.1:5000. Só usa as rotas /api/extensao/..., as
// únicas que o Puxaí aceita de uma extensão.
//
// - Botão direito num link, num vídeo ou na página: "Baixar vídeo/MP3 com o Puxaí"
// - Atalhos: Alt+Shift+P (MP4) e Alt+Shift+M (MP3), mudam em chrome://extensions/shortcuts
// - A janelinha do botão da barra (janela.js) também pede por aqui

const PORTA_PADRAO = 5000;
const QUALIDADE_PADRAO = "720p";

async function endereco() {
    const { porta } = await chrome.storage.local.get("porta");
    return `http://127.0.0.1:${porta || PORTA_PADRAO}`;
}

async function chamar(caminho, corpo) {
    let resposta;
    try {
        resposta = await fetch((await endereco()) + caminho, {
            method: corpo ? "POST" : "GET",
            headers: corpo ? { "Content-Type": "application/json" } : {},
            body: corpo ? JSON.stringify(corpo) : undefined,
            signal: AbortSignal.timeout(8000),
        });
    } catch {
        return { fechado: true, erro: "O Puxaí está fechado. Abra o programa e tente de novo." };
    }
    const dados = await resposta.json().catch(() => ({}));
    if (resposta.status === 403) {
        return { erro: "O Puxaí recusou o pedido. Atualize o Puxaí para a versão mais nova." };
    }
    if (resposta.status === 404) {
        return { erro: "Este Puxaí ainda não aceita a extensão. Atualize o Puxaí para a versão mais nova." };
    }
    return resposta.ok ? dados : { erro: dados.erro || "O Puxaí não conseguiu colocar na fila." };
}

const estado = () => chamar("/api/extensao/estado");

async function enviar(url, formato, titulo) {
    const { qualidade } = await chrome.storage.local.get("qualidade");
    return chamar("/api/extensao/enviar", { url, formato, qualidade: qualidade || QUALIDADE_PADRAO, titulo });
}

function avisar(mensagem) {
    chrome.notifications.create({
        type: "basic",
        iconUrl: chrome.runtime.getURL("icones/icone-128.png"),
        title: "Puxaí",
        message: mensagem,
    });
}

async function enviarEAvisar(url, formato, titulo) {
    if (!/^https?:/i.test(url || "")) {
        avisar("Abra a página de um vídeo (YouTube, TikTok, Instagram...) e tente de novo.");
        return;
    }
    const resultado = await enviar(url, formato, titulo);
    if (resultado.erro) {
        avisar(resultado.erro);
        return;
    }
    const tipo = formato === "mp3" ? "MP3" : `MP4 ${resultado.qualidade}`;
    avisar(`Na fila do Puxaí (${resultado.site}, ${tipo}): ${titulo || url}`);
}

// Menu do botão direito
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.removeAll(() => {
        for (const [id, titulo] of [["puxai-mp4", "Baixar vídeo com o Puxaí (MP4)"], ["puxai-mp3", "Baixar MP3 com o Puxaí"]]) {
            chrome.contextMenus.create({
                id, title: titulo, contexts: ["link", "page", "video"],
                documentUrlPatterns: ["http://*/*", "https://*/*"],
            });
        }
    });
});

chrome.contextMenus.onClicked.addListener((info, aba) => {
    const formato = info.menuItemId === "puxai-mp3" ? "mp3" : "mp4";
    if (info.linkUrl) {
        // Num link: o vídeo é o do link (o título vem quando o download terminar)
        enviarEAvisar(info.linkUrl, formato, info.linkText || null);
    } else {
        // Na página ou no vídeo da página (o "src" do vídeo quase sempre é um blob: que não dá para baixar)
        enviarEAvisar(info.pageUrl || aba?.url, formato, aba?.title);
    }
});

// Atalhos de teclado
chrome.commands.onCommand.addListener(async (comando, aba) => {
    aba = aba || (await chrome.tabs.query({ active: true, currentWindow: true }))[0];
    enviarEAvisar(aba?.url, comando === "baixar-mp3" ? "mp3" : "mp4", aba?.title);
});

// Pedidos da janelinha do botão da barra
chrome.runtime.onMessage.addListener((pedido, _remetente, responder) => {
    const tarefas = {
        estado: () => estado(),
        enviar: () => enviar(pedido.url, pedido.formato, pedido.titulo),
        abrir: () => chamar("/api/extensao/abrir", {}),
    };
    if (!tarefas[pedido.tipo]) return false;
    tarefas[pedido.tipo]().then(responder);
    return true; // a resposta vem depois (assíncrona)
});
