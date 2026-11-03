// Janelinha do botão da barra: mostra o vídeo da aba aberta e manda para o Puxaí.
// Quem fala com o Puxaí é o fundo.js (pedidos por chrome.runtime.sendMessage).

const mensagem = document.getElementById("mensagem");
const areaBaixar = document.getElementById("baixar");
const titulo = document.getElementById("titulo");
const qualidade = document.getElementById("qualidade");
const resultado = document.getElementById("resultado");
const botaoAbrir = document.getElementById("abrir");
const campoPorta = document.getElementById("porta");

const pedir = (pedido) => chrome.runtime.sendMessage(pedido);
let aba = null;

function mostrar(texto, tipo = "") {
    resultado.hidden = false;
    resultado.textContent = texto; // textContent: as mensagens têm texto de fora (título, erro)
    resultado.className = `mensagem ${tipo}`;
}

async function carregar() {
    areaBaixar.hidden = true;
    resultado.hidden = true;
    mensagem.hidden = false;
    mensagem.textContent = "Procurando o Puxaí...";

    [aba] = await chrome.tabs.query({ active: true, currentWindow: true });
    const estado = await pedir({ tipo: "estado" });
    if (estado.erro) {
        mensagem.textContent = estado.erro;
        mensagem.className = "mensagem erro";
        return;
    }
    if (!/^https?:/i.test(aba?.url || "")) {
        mensagem.textContent = "Abra a página de um vídeo (YouTube, TikTok, Instagram...) e clique de novo aqui.";
        mensagem.className = "mensagem";
        return;
    }

    // Qualidades que o Puxaí aceita; fica a última escolhida
    const salvo = (await chrome.storage.local.get("qualidade")).qualidade || estado.padrao;
    qualidade.innerHTML = "";
    for (const opcao of estado.qualidades) {
        qualidade.add(new Option(opcao, opcao, false, opcao === salvo));
    }

    mensagem.hidden = true;
    titulo.textContent = aba.title || aba.url;
    areaBaixar.hidden = false;
}

async function baixar(formato, botao) {
    botao.disabled = true;
    const texto = botao.textContent;
    botao.textContent = "Enviando...";
    const resposta = await pedir({ tipo: "enviar", url: aba.url, formato, titulo: aba.title });
    botao.disabled = false;
    botao.textContent = texto;
    if (resposta.erro) {
        mostrar(resposta.erro, "erro");
        return;
    }
    const tipo = formato === "mp3" ? "MP3" : `MP4 ${resposta.qualidade}`;
    mostrar(`✓ Na fila do Puxaí (${resposta.site}, ${tipo}). O arquivo vai para a pasta escolhida no Puxaí.`, "ok");
    botaoAbrir.hidden = false;
}

document.getElementById("mp4").addEventListener("click", (e) => baixar("mp4", e.currentTarget));
document.getElementById("mp3").addEventListener("click", (e) => baixar("mp3", e.currentTarget));
qualidade.addEventListener("change", () => chrome.storage.local.set({ qualidade: qualidade.value }));
botaoAbrir.addEventListener("click", async () => {
    await pedir({ tipo: "abrir" });
    window.close();
});

// Porta (só muda quem abriu o Puxaí com outra porta, ex.: PORTA=5001)
chrome.storage.local.get("porta").then(({ porta }) => { campoPorta.value = porta || ""; });
campoPorta.addEventListener("change", async () => {
    const porta = parseInt(campoPorta.value, 10);
    await chrome.storage.local.set({ porta: porta > 0 && porta < 65536 ? porta : null });
    carregar();
});

carregar();
