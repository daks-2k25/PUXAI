"""Servidor MCP do Puxaí: deixa agentes de IA usarem o Puxaí aberto neste computador."""
import json
import urllib.error
import urllib.request

from mcp.server.mcpserver import MCPServer

ENDERECO = "http://127.0.0.1:5000"

servidor = MCPServer("Puxaí", instructions="Baixa vídeos e músicas e cuida de fotos e PDFs, usando o Puxaí aberto neste PC.")


def chamar(caminho):
    """GET na API do Puxaí; devolve o JSON da resposta."""
    with urllib.request.urlopen(ENDERECO + caminho, timeout=10) as resposta:
        return json.load(resposta)


@servidor.tool()
def estado_do_puxai() -> dict:
    """Diz se o Puxaí está aberto neste computador e qual a versão dele.
    Use antes das outras ferramentas: se o Puxaí estiver fechado, peça para a pessoa abrir."""
    try:
        dados = chamar("/api/versao")
    except urllib.error.URLError:
        return {"aberto": False, "dica": "O Puxaí está fechado. Abra o programa e tente de novo."}
    return {"aberto": True, "versao": dados["atual"]}


if __name__ == "__main__":
    servidor.run()
