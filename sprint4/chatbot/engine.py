"""
chatbot/engine.py — Motor do Chatbot Local (Sprint 4)
100% local, sem API externa. Usa regras + TF-IDF para detecção de intenção
e templates de resposta contextualizados para o Tótem Cultural Inclusivo.
"""
from __future__ import annotations

import json
import random
import re
import sqlite3
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# Paths
# ============================================================
CHATBOT_DIR = Path(__file__).resolve().parent
SPRINT4_DIR = CHATBOT_DIR.parent
DB_PATH = SPRINT4_DIR / "database" / "totem.db"

# ============================================================
# Normalização de texto
# ============================================================

def normalize(text: str) -> str:
    """Remove acentos, lowercase, espaços extras."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", normalize(text))

# ============================================================
# Base de conhecimento do Tótem
# ============================================================

KNOWLEDGE_BASE: Dict[str, Any] = {
    "horarios": {
        "museu": "O Museu de Arte Contemporânea abre de terça a domingo, das 10h às 18h. Entrada gratuita às quartas-feiras.",
        "biblioteca": "A Biblioteca Municipal funciona de segunda a sexta das 8h às 20h, e sábados das 9h às 14h.",
        "centro_cultural": "O Centro Cultural está aberto todos os dias das 9h às 21h.",
        "default": "Os espaços culturais geralmente funcionam de terça a domingo, das 10h às 18h. Consulte a recepção para horários específicos.",
    },
    "exposicoes": [
        "🎨 'Raízes Brasileiras' — Exposição de arte indígena contemporânea. Sala 3, andar térreo.",
        "📸 'Olhares Urbanos' — Fotografia documental de cidades brasileiras. Galeria Norte.",
        "🖼️ 'Modernismo Revisitado' — Releitura do movimento modernista. Sala Principal.",
        "🌿 'Natureza e Cultura' — Instalações interativas sobre biodiversidade. Jardim Interno.",
    ],
    "eventos": [
        "🎭 Sarau Literário — toda sexta-feira às 19h. Auditório Principal.",
        "🎵 Concerto de Câmara — sábados às 16h. Sala de Música.",
        "📚 Clube do Livro — última quinta do mês, às 18h30. Biblioteca.",
        "🎬 Cinema Gratuito — domingos às 15h. Anfiteatro ao Ar Livre.",
    ],
    "acessibilidade": {
        "recursos": [
            "♿ Rampas de acesso em todas as entradas.",
            "🦮 Guia de áudio disponível para visitantes com deficiência visual.",
            "🤟 Intérpretes de Libras disponíveis mediante agendamento.",
            "🔠 Materiais em Braille na recepção.",
            "🎧 Audiodescrição disponível via QR Code em todas as obras.",
        ],
        "contato": "Para solicitar suporte de acessibilidade, contate a recepção ou ligue para (11) 3333-4444.",
    },
    "localizacao": {
        "banheiros": "Banheiros nos andares térreo e 1º andar. Banheiro adaptado no térreo, ao lado da recepção.",
        "estacionamento": "Estacionamento gratuito para visitantes por 2h. Convênio com estacionamento vizinho para períodos maiores.",
        "restaurante": "Café Cultural no térreo, aberto das 9h às 17h30. Opções veganas e sem glúten disponíveis.",
        "loja": "Loja de souvenirs na saída principal. Aceitamos cartão e PIX.",
        "wifi": "Wi-Fi gratuito disponível. Rede: TotemCultural | Senha: cultura2026",
    },
    "ingressos": {
        "preco": "Entrada gratuita para todos os visitantes.",
        "reserva": "Visitas em grupo (acima de 10 pessoas) devem ser agendadas com 48h de antecedência.",
        "educacional": "Visitas escolares têm prioridade de agendamento. Entre em contato pelo e-mail visitas@cultural.org.",
    },
}

# ============================================================
# Intenções e padrões de reconhecimento
# ============================================================

INTENTS: List[Dict[str, Any]] = [
    {
        "name": "saudacao",
        "keywords": ["oi", "ola", "bom dia", "boa tarde", "boa noite", "hey", "hello", "salve", "ei"],
        "weight": 1.0,
    },
    {
        "name": "horario",
        "keywords": ["horario", "horas", "abre", "fecha", "funcionamento", "quando", "aberto", "funciona", "expediente"],
        "weight": 1.2,
    },
    {
        "name": "exposicao",
        "keywords": ["exposicao", "exposicoes", "obra", "obras", "arte", "galeria", "artista", "ver", "visitando", "mostra"],
        "weight": 1.1,
    },
    {
        "name": "evento",
        "keywords": ["evento", "eventos", "programacao", "agenda", "show", "concerto", "sarau", "cinema", "apresentacao", "atividade"],
        "weight": 1.1,
    },
    {
        "name": "acessibilidade",
        "keywords": ["acessibilidade", "cadeirante", "cadeira de rodas", "deficiencia", "libras", "braille", "audio", "visual", "auditivo", "rampa", "adaptado"],
        "weight": 1.3,
    },
    {
        "name": "localizacao",
        "keywords": ["onde", "banheiro", "restaurante", "cafe", "loja", "estacionamento", "wifi", "internet", "como chegar", "fica"],
        "weight": 1.0,
    },
    {
        "name": "ingresso",
        "keywords": ["ingresso", "entrada", "preco", "gratis", "gratuito", "pagar", "ticket", "bilhete", "reserva", "agendar"],
        "weight": 1.1,
    },
    {
        "name": "despedida",
        "keywords": ["tchau", "ate logo", "ate mais", "obrigado", "obrigada", "valeu", "brigado", "bye", "adeus", "encerrar"],
        "weight": 1.0,
    },
    {
        "name": "ajuda",
        "keywords": ["ajuda", "help", "como", "pode", "consegue", "me diga", "informacao", "informacoes", "sabe", "duvida", "pergunta"],
        "weight": 0.8,
    },
    {
        "name": "acervo",
        "keywords": ["acervo", "colecao", "catalogo", "buscar", "busca", "pesquisa", "encontrar", "obra especifica", "artista"],
        "weight": 1.0,
    },
]

# ============================================================
# Templates de resposta
# ============================================================

RESPONSES: Dict[str, List[str]] = {
    "saudacao": [
        "Olá! 👋 Bem-vindo ao Tótem Cultural Inclusivo! Sou seu assistente virtual. Posso te ajudar com informações sobre exposições, eventos, horários, acessibilidade e muito mais. O que você gostaria de saber?",
        "Oi! 😊 Seja bem-vindo! Estou aqui para tornar sua visita mais agradável. Posso informar sobre programação, acessibilidade, localização de espaços e eventos. Como posso ajudar?",
        "Bom dia/tarde/noite! ✨ Seja bem-vindo ao nosso espaço cultural! Estou aqui para ajudar. Você pode me perguntar sobre exposições, eventos, horários ou qualquer dúvida sobre o espaço.",
    ],
    "horario_museu": [
        f"🕐 {KNOWLEDGE_BASE['horarios']['museu']}",
    ],
    "horario_biblioteca": [
        f"📚 {KNOWLEDGE_BASE['horarios']['biblioteca']}",
    ],
    "horario_centro": [
        f"🏛️ {KNOWLEDGE_BASE['horarios']['centro_cultural']}",
    ],
    "horario_default": [
        f"🕐 {KNOWLEDGE_BASE['horarios']['default']} Posso buscar o horário de um espaço específico — qual você quer saber?",
    ],
    "exposicao": [],  # gerado dinamicamente
    "evento": [],     # gerado dinamicamente
    "acessibilidade": [],  # gerado dinamicamente
    "localizacao_banheiro": [
        f"🚻 {KNOWLEDGE_BASE['localizacao']['banheiros']}",
    ],
    "localizacao_restaurante": [
        f"☕ {KNOWLEDGE_BASE['localizacao']['restaurante']}",
    ],
    "localizacao_estacionamento": [
        f"🅿️ {KNOWLEDGE_BASE['localizacao']['estacionamento']}",
    ],
    "localizacao_wifi": [
        f"📶 {KNOWLEDGE_BASE['localizacao']['wifi']}",
    ],
    "localizacao_loja": [
        f"🛍️ {KNOWLEDGE_BASE['localizacao']['loja']}",
    ],
    "ingresso": [
        f"🎟️ {KNOWLEDGE_BASE['ingressos']['preco']} {KNOWLEDGE_BASE['ingressos']['reserva']}",
        f"🎟️ {KNOWLEDGE_BASE['ingressos']['preco']} {KNOWLEDGE_BASE['ingressos']['educacional']}",
    ],
    "despedida": [
        "Até logo! 👋 Foi um prazer ajudar. Aproveite sua visita e volte sempre!",
        "Tchau! 😊 Espero que aproveite muito o espaço. Tenha uma ótima visita!",
        "Até mais! ✨ Se precisar de qualquer informação, estarei aqui. Boa visita!",
    ],
    "ajuda": [
        "Posso te ajudar com:\n• 🎨 Exposições em cartaz\n• 📅 Agenda de eventos\n• 🕐 Horários de funcionamento\n• ♿ Recursos de acessibilidade\n• 📍 Localização (banheiros, café, loja)\n• 🎟️ Ingressos e reservas\n\nO que você gostaria de saber?",
    ],
    "acervo": [
        "🔍 Nosso acervo conta com obras de arte brasileira e internacional. Posso te mostrar as exposições em cartaz:\n\n" + "\n".join(KNOWLEDGE_BASE["exposicoes"]) + "\n\nQuer saber mais sobre alguma delas?",
    ],
    "fallback": [
        "Desculpe, não entendi completamente. 🤔 Posso ajudar com informações sobre exposições, eventos, horários, acessibilidade e localização. Pode reformular a pergunta?",
        "Hmm, não tenho certeza do que você precisa. 💭 Tente perguntar sobre: exposições, eventos, horários, acessibilidade, café/restaurante, banheiros, Wi-Fi ou ingressos.",
        "Não consegui entender bem. 🙏 Estou aqui para ajudar com informações sobre o espaço cultural. Qual é a sua dúvida?",
    ],
}


def _get_exposicao_response() -> str:
    exps = "\n".join(KNOWLEDGE_BASE["exposicoes"])
    return f"🎨 Temos {len(KNOWLEDGE_BASE['exposicoes'])} exposições em cartaz:\n\n{exps}\n\nGostaria de saber mais sobre alguma delas ou precisa de informações de acessibilidade para as salas?"


def _get_evento_response() -> str:
    evts = "\n".join(KNOWLEDGE_BASE["eventos"])
    return f"📅 Confira nossa programação de eventos:\n\n{evts}\n\nTodos os eventos são gratuitos! Deseja mais informações sobre algum deles?"


def _get_acessibilidade_response() -> str:
    recursos = "\n".join(KNOWLEDGE_BASE["acessibilidade"]["recursos"])
    contato = KNOWLEDGE_BASE["acessibilidade"]["contato"]
    return f"♿ Recursos de acessibilidade disponíveis:\n\n{recursos}\n\n{contato}"


# ============================================================
# Detector de intenção
# ============================================================

@dataclass
class IntentResult:
    intent: str
    confidence: float
    matched_keywords: List[str]
    sub_intent: Optional[str] = None


def detect_intent(text: str) -> IntentResult:
    """
    Detecta intenção via contagem de keywords ponderada.
    Retorna IntentResult com intent, confiança e sub-intenção.
    """
    tokens = set(tokenize(text))
    text_norm = normalize(text)

    scores: Dict[str, float] = {}
    matches: Dict[str, List[str]] = {}

    for intent_def in INTENTS:
        name = intent_def["name"]
        weight = intent_def["weight"]
        kws = intent_def["keywords"]

        score = 0.0
        matched = []

        for kw in kws:
            kw_norm = normalize(kw)
            if kw_norm in text_norm:
                score += weight
                matched.append(kw)

        if score > 0:
            scores[name] = score
            matches[name] = matched

    if not scores:
        return IntentResult(intent="fallback", confidence=0.0, matched_keywords=[])

    best_intent = max(scores, key=lambda k: scores[k])
    max_possible = max(len(i["keywords"]) * i["weight"] for i in INTENTS if i["name"] == best_intent)
    confidence = min(scores[best_intent] / max_possible, 1.0)

    # Sub-intenção para horario e localizacao
    sub_intent = None
    if best_intent == "horario":
        if any(w in text_norm for w in ["museu", "mac", "arte"]):
            sub_intent = "museu"
        elif any(w in text_norm for w in ["biblioteca", "livro"]):
            sub_intent = "biblioteca"
        elif any(w in text_norm for w in ["centro", "cultural", "cc"]):
            sub_intent = "centro"

    if best_intent == "localizacao":
        if any(w in text_norm for w in ["banheiro", "wc", "sanitario", "toalete"]):
            sub_intent = "banheiro"
        elif any(w in text_norm for w in ["restaurante", "cafe", "comer", "lanche", "comida", "almoco"]):
            sub_intent = "restaurante"
        elif any(w in text_norm for w in ["estacionamento", "carro", "vaga", "parking"]):
            sub_intent = "estacionamento"
        elif any(w in text_norm for w in ["wifi", "internet", "rede", "senha"]):
            sub_intent = "wifi"
        elif any(w in text_norm for w in ["loja", "souvenir", "presente", "comprar"]):
            sub_intent = "loja"

    return IntentResult(
        intent=best_intent,
        confidence=round(confidence, 3),
        matched_keywords=matches.get(best_intent, []),
        sub_intent=sub_intent,
    )


# ============================================================
# Gerador de resposta
# ============================================================

def generate_response(intent_result: IntentResult) -> str:
    intent = intent_result.intent
    sub = intent_result.sub_intent

    # Exposição e eventos: gera dinamicamente
    if intent == "exposicao" or intent == "acervo":
        return _get_exposicao_response()

    if intent == "evento":
        return _get_evento_response()

    if intent == "acessibilidade":
        return _get_acessibilidade_response()

    # Horário com sub-intenção
    if intent == "horario":
        if sub == "museu":
            key = "horario_museu"
        elif sub == "biblioteca":
            key = "horario_biblioteca"
        elif sub == "centro":
            key = "horario_centro"
        else:
            key = "horario_default"
        options = RESPONSES.get(key, RESPONSES["fallback"])
        return random.choice(options)

    # Localização com sub-intenção
    if intent == "localizacao":
        if sub == "banheiro":
            key = "localizacao_banheiro"
        elif sub == "restaurante":
            key = "localizacao_restaurante"
        elif sub == "estacionamento":
            key = "localizacao_estacionamento"
        elif sub == "wifi":
            key = "localizacao_wifi"
        elif sub == "loja":
            key = "localizacao_loja"
        else:
            return (
                "📍 Posso te ajudar a localizar:\n"
                "• 🚻 Banheiros\n"
                "• ☕ Café/Restaurante\n"
                "• 🅿️ Estacionamento\n"
                "• 📶 Wi-Fi\n"
                "• 🛍️ Loja de souvenirs\n\n"
                "Qual desses você precisa encontrar?"
            )
        options = RESPONSES.get(key, RESPONSES["fallback"])
        return random.choice(options)

    # Outros intents diretos
    if intent in RESPONSES and RESPONSES[intent]:
        return random.choice(RESPONSES[intent])

    # Fallback
    return random.choice(RESPONSES["fallback"])


# ============================================================
# Gerenciador de sessão e persistência
# ============================================================

def _get_conn() -> sqlite3.Connection:
    from database.db import get_conn, init_db
    conn = get_conn(DB_PATH)
    init_db(conn)
    return conn


def create_session(device_id: str = "totem-01", language: str = "pt-BR", accessibility_mode: Optional[str] = None) -> str:
    """Cria nova sessão de chat e retorna session_id."""
    session_id = str(uuid.uuid4())
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO chat_sessions (session_id, device_id, language, accessibility_mode) VALUES (?, ?, ?, ?)",
            (session_id, device_id, language, accessibility_mode),
        )
        conn.commit()
    finally:
        conn.close()
    return session_id


def end_session(session_id: str) -> None:
    """Marca sessão como encerrada."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE chat_sessions SET ended_at = ? WHERE session_id = ?",
            (now, session_id),
        )
        conn.commit()
    finally:
        conn.close()


def save_message(
    session_id: str,
    role: str,
    content: str,
    intent: Optional[str] = None,
    confidence: Optional[float] = None,
    input_mode: str = "text",
) -> int:
    """Salva mensagem no banco e atualiza contador da sessão. Retorna id da mensagem."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, intent, confidence, input_mode) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, role, content, intent, confidence, input_mode),
        )
        conn.execute(
            "UPDATE chat_sessions SET total_messages = total_messages + 1 WHERE session_id = ?",
            (session_id,),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def get_session_history(session_id: str) -> List[Dict[str, Any]]:
    """Retorna histórico de mensagens de uma sessão."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT role, content, intent, created_at FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ============================================================
# Interface principal
# ============================================================

@dataclass
class ChatResponse:
    session_id: str
    user_message: str
    bot_response: str
    intent: str
    confidence: float
    input_mode: str


def chat(
    user_message: str,
    session_id: Optional[str] = None,
    device_id: str = "totem-01",
    input_mode: str = "text",
) -> ChatResponse:
    """
    Processa mensagem do usuário e retorna resposta do bot.
    Cria sessão automaticamente se não fornecida.
    Persiste tudo no banco.
    """
    if not session_id:
        session_id = create_session(device_id=device_id)

    # Detecta intenção
    intent_result = detect_intent(user_message)

    # Gera resposta
    bot_response = generate_response(intent_result)

    # Persiste mensagens
    save_message(
        session_id=session_id,
        role="user",
        content=user_message,
        intent=intent_result.intent,
        confidence=intent_result.confidence,
        input_mode=input_mode,
    )
    save_message(
        session_id=session_id,
        role="assistant",
        content=bot_response,
        intent=intent_result.intent,
        confidence=intent_result.confidence,
        input_mode=input_mode,
    )

    return ChatResponse(
        session_id=session_id,
        user_message=user_message,
        bot_response=bot_response,
        intent=intent_result.intent,
        confidence=intent_result.confidence,
        input_mode=input_mode,
    )
