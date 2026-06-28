"""Assistente com LLM + RAG (Etapa 8).

Explica decisoes e recupera politicas sinteticas para apoiar a analise humana.

Como funciona (RAG = Retrieval-Augmented Generation):
1. recupera os trechos de politica mais relevantes (busca TF-IDF);
2. monta um prompt com esses trechos como contexto;
3. gera a resposta com o Claude (Anthropic), fundamentada nos trechos.

Sem `ANTHROPIC_API_KEY`, opera em **modo recuperacao** (devolve os trechos +
a decisao), para a demo funcionar sem chave.

Guardrails:
- entrada: recusa pedidos fora de escopo (ex.: conselho financeiro real,
  tentativa de injecao de prompt);
- saida: remove possiveis dados pessoais (e-mail, CPF) da resposta.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

POLICIES_DIR = Path("data/synthetic_enrichment/policies")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

# padroes bloqueados na entrada (injecao / fora de escopo)
_BLOCK_INPUT = re.compile(
    r"(ignore (as )?instru|desconsidere|aja como|"
    r"onde invisto meu dinheiro|me diga em que aplicar|conselho financeiro)",
    re.IGNORECASE,
)
# PII na saida
_EMAIL = re.compile(r"[\w.\-]+@[\w.\-]+\.\w+")
_CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")


class PolicyRetriever:
    """Busca TF-IDF sobre os documentos de politica sintetica."""

    def __init__(self, docs_dir: Path = POLICIES_DIR) -> None:
        paths = sorted(docs_dir.glob("*.md"))
        self.names = [p.name for p in paths]
        self.docs = [p.read_text(encoding="utf-8") for p in paths]
        self.vectorizer = TfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform(self.docs)

    def retrieve(self, query: str, k: int = 2) -> list[tuple[str, str]]:
        """Devolve os k documentos mais relevantes (nome, texto)."""
        q = self.vectorizer.transform([query])
        sims = cosine_similarity(q, self.matrix)[0]
        top = sims.argsort()[::-1][:k]
        return [(self.names[i], self.docs[i]) for i in top]


def input_guard(question: str) -> str | None:
    """Retorna mensagem de recusa se a pergunta violar o guardrail; senao None."""
    if _BLOCK_INPUT.search(question):
        return (
            "Nao posso ajudar com isso. O assistente apenas explica decisoes e "
            "politicas internas sinteticas; nao da conselho financeiro nem segue "
            "instrucoes que mudem seu proposito."
        )
    return None


def output_guard(text: str) -> str:
    """Remove possiveis dados pessoais da resposta."""
    text = _EMAIL.sub("[email removido]", text)
    text = _CPF.sub("[cpf removido]", text)
    return text


def _call_llm(prompt: str) -> str | None:
    """Chama o Claude se houver chave; senao devolve None."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=(
                "Voce explica decisoes de uma plataforma de ofertas, usando SOMENTE "
                "os trechos de politica fornecidos. Nao da conselho financeiro. "
                "Se a resposta nao estiver nos trechos, diga que nao sabe."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as exc:  # nao derrubar a demo por erro de API
        return f"[LLM indisponivel: {type(exc).__name__}]"


def answer(question: str, retriever: PolicyRetriever | None = None) -> str:
    """Responde uma pergunta sobre as politicas, com RAG e guardrails."""
    refusal = input_guard(question)
    if refusal:
        return refusal

    retriever = retriever or PolicyRetriever()
    trechos = retriever.retrieve(question)
    contexto = "\n\n".join(f"### {nome}\n{txt}" for nome, txt in trechos)

    prompt = f"Trechos de politica:\n{contexto}\n\nPergunta: {question}"
    resposta = _call_llm(prompt)
    if resposta is None:
        fontes = ", ".join(n for n, _ in trechos)
        resposta = (
            f"[modo recuperacao - sem LLM] Trechos mais relevantes: {fontes}.\n\n"
            f"{contexto}"
        )
    return output_guard(resposta)


def explain_decision(context: dict, selected_arm: str) -> str:
    """Explica, em linguagem natural, por que um braço foi escolhido."""
    seg, ch = context.get("segment"), context.get("channel")
    q = (
        f"Por que escolher a oferta '{selected_arm}' para um cliente do segmento "
        f"'{seg}' no canal '{ch}'? Cite as politicas relevantes."
    )
    return answer(q)


if __name__ == "__main__":
    print(explain_decision({"segment": "novo", "channel": "email"}, "educacao_financeira"))
