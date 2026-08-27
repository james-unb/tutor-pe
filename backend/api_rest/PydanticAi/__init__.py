from enum import Enum
import logging
from typing import List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv
import os
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google import GoogleProvider
from .tools.create_table_html import create_table_html_tool
from .tools.get_question_by_number import get_question_by_number_tool
from .system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_KEY:
    raise ValueError("GEMINI_KEY not found in environment variables")
    

class ContentType(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    PARAGRAPH = "paragraph"
    FORMULA = "formula"
    LIST_ITEM = "list_item"
    TABLE = "table"

class ContentItem(BaseModel):           
    type: ContentType
    content: str = Field(..., description="The actual text content or formula")

class ChatResponse(BaseModel):
    items: List[ContentItem]

def chat_with_agent(prompt: str, history: List[dict] = None) -> tuple[ChatResponse, str | None]:
    history_context = ""
    if history:
        history_context = "<historico_da_conversa>\n"
        for msg in history:
            role = "Aluno" if msg['role'] == 'user' else "Professor"
            history_context += f"{role}: {msg['content']}\n"
        history_context += "</historico_da_conversa>\n"

    try:
        provider = GoogleProvider(api_key=GEMINI_KEY)
        model = GoogleModel(GEMINI_MODEL, provider=provider)
        model_settings = GoogleModelSettings(temperature=0.7)
        logger.info("==========================")
        logger.info("New message")

        agent = Agent(
            model,
            output_type=ChatResponse,
            model_settings=model_settings,
            deps_type=dict, 
            tools=[create_table_html_tool, get_question_by_number_tool],
            system_prompt=SYSTEM_PROMPT + history_context
        )
        captured_data = {}
        response = agent.run_sync(prompt, deps=captured_data)
        logger.debug("Captured data: %s", captured_data)
        logger.debug("Response: %s", response.output)
        logger.info("==========================")
        return response.output, captured_data.get('question_id')
    except Exception as e:
        logger.exception("Error in chat_with_agent: %s", e)
        return ChatResponse(items=[
            ContentItem(type=ContentType.PARAGRAPH, content="Ops! Parece que tive um pequeno tropeço aqui enquanto tentava te ajudar. 😅 Por favor, tente enviar sua mensagem novamente em alguns instantes para continuarmos nosso aprendizado!")
        ]), None


def chat_with_agent_simulado(
    prompt: str,
    history: List[dict] = None,
    question_context: str = "",
) -> tuple[ChatResponse, None]:
    """
    Chat com o agente no contexto de correção de uma questão de simulado.
    O question_context deve conter enunciado, alternativas e solução (correção).
    Não usa a tool get_question_by_number (a questão já está no contexto).
    """
    history_context = ""
    if history:
        history_context = "<historico_da_conversa>\n"
        for msg in history:
            role = "Aluno" if msg["role"] == "user" else "Professor"
            history_context += f"{role}: {msg['content']}\n"
        history_context += "</historico_da_conversa>\n"

    contexto_questao = (
        "\n\n<contexto_questao_simulado>\n"
        "Você está ajudando o aluno na correção desta questão de simulado. "
        "A explicação (correção/solução) fornecida abaixo é a explicação oficial e correta do gabarito. "
        "Use o enunciado, o gabarito (quando indicado) e essa correção como referência para responder.\n\n"
        f"{question_context}\n"
        "</contexto_questao_simulado>\n"
    )

    system_prompt = SYSTEM_PROMPT + contexto_questao + history_context

    try:
        provider = GoogleProvider(api_key=GEMINI_KEY)
        model = GoogleModel(GEMINI_MODEL, provider=provider)
        model_settings = GoogleModelSettings(temperature=0.7)
        logger.info("==========================")
        logger.info("New message (simulado correction)")

        agent = Agent(
            model,
            output_type=ChatResponse,
            model_settings=model_settings,
            deps_type=dict,
            tools=[create_table_html_tool],
            system_prompt=system_prompt,
        )
        response = agent.run_sync(prompt, deps={})
        logger.debug("Response: %s", response.output)
        logger.info("==========================")
        return response.output, None
    except Exception as e:
        logger.exception("Error in chat_with_agent_simulado: %s", e)
        return ChatResponse(items=[
            ContentItem(
                type=ContentType.PARAGRAPH,
                content="Ops! Parece que tive um pequeno tropeço aqui enquanto tentava te ajudar. 😅 Por favor, tente enviar sua mensagem novamente em alguns instantes para continuarmos nosso aprendizado!",
            )
        ]), None
