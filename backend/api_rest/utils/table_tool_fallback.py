"""
Fallback: quando o modelo escreve a chamada da tool gerar_tabela_html como texto
em vez de invocá-la, detectamos o padrão e geramos o HTML equivalentemente.
Documentado como contingência; a prioridade é o modelo invocar a tool corretamente.
"""
import ast
import logging
import re
from typing import List, Optional, Tuple

from api_rest.PydanticAi import ContentItem, ContentType
from api_rest.PydanticAi.tools.create_table_html import build_table_html

logger = logging.getLogger(__name__)

TOOL_CALL_PATTERN = re.compile(
    r'(?:default_api\.)?gerar_tabela_html\s*\(',
    re.IGNORECASE,
)


def _find_matching_bracket(s: str, start: int, open_char: str, close_char: str) -> Optional[int]:
    """Retorna o índice do close_char que equilibra open_char a partir de start."""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == open_char:
            depth += 1
        elif s[i] == close_char:
            depth -= 1
            if depth == 0:
                return i
    return None


def _parse_quoted_string(s: str, start: int) -> Optional[Tuple[str, int]]:
    """Lê uma string entre aspas simples ou duplas a partir de start. Retorna (valor, índice após a aspas de fechamento)."""
    if start >= len(s):
        return None
    quote = s[start]
    if quote not in ("'", '"'):
        return None
    end = start + 1
    result = []
    while end < len(s):
        if s[end] == '\\':
            end += 1
            if end < len(s):
                result.append(s[end])
            end += 1
            continue
        if s[end] == quote:
            return (''.join(result), end + 1)
        result.append(s[end])
        end += 1
    return None


def _try_parse_gerar_tabela_html_args(content: str) -> Optional[Tuple[List[str], List[List[str]], Optional[str]]]:
    """
    Tenta extrair (headers, rows, caption) de uma string que parece uma chamada
    gerar_tabela_html(...). Retorna None se não reconhecer ou falhar o parse.
    """
    match = TOOL_CALL_PATTERN.search(content)
    if not match:
        return None
    paren_start = match.end() - 1  # índice do '('
    close = _find_matching_bracket(content, paren_start, '(', ')')
    if close is None:
        return None
    args_str = content[paren_start + 1:close].strip()

    headers: Optional[List[str]] = None
    rows: Optional[List[List[str]]] = None
    caption: Optional[str] = None

    # headers=[...]
    headers_match = re.search(r'headers\s*=\s*\[', args_str, re.IGNORECASE)
    if headers_match:
        bracket_start = args_str.index('[', headers_match.start())
        bracket_end = _find_matching_bracket(args_str, bracket_start, '[', ']')
        if bracket_end is not None:
            try:
                headers = ast.literal_eval(args_str[bracket_start:bracket_end + 1])
            except (ValueError, SyntaxError):
                pass

    # rows=[...]
    rows_match = re.search(r'rows\s*=\s*\[', args_str, re.IGNORECASE)
    if rows_match:
        bracket_start = args_str.index('[', rows_match.start())
        bracket_end = _find_matching_bracket(args_str, bracket_start, '[', ']')
        if bracket_end is not None:
            try:
                rows = ast.literal_eval(args_str[bracket_start:bracket_end + 1])
            except (ValueError, SyntaxError):
                pass

    # caption='...' ou caption="..."
    caption_match = re.search(r'caption\s*=\s*', args_str, re.IGNORECASE)
    if caption_match:
        value_start = caption_match.end()
        if value_start < len(args_str) and args_str[value_start] in ("'", '"'):
            parsed = _parse_quoted_string(args_str, value_start)
            if parsed:
                caption = parsed[0]

    if headers is not None and rows is not None:
        return (headers, rows, caption)
    return None


def fix_table_tool_text_in_response(response_data) -> None:
    """
    Modifica response_data.items in place: para qualquer item cujo content
    contenha uma chamada em texto a gerar_tabela_html(...), tenta extrair
    argumentos, gerar o HTML e substituir o content pelo HTML e o type por 'table'.
    """
    for i, item in enumerate(response_data.items):
        if not getattr(item, 'content', None):
            continue
        content = item.content
        if not TOOL_CALL_PATTERN.search(content):
            continue
        parsed = _try_parse_gerar_tabela_html_args(content)
        if parsed is None:
            continue
        headers, rows, caption = parsed
        try:
            html = build_table_html(headers=headers, rows=rows, caption=caption)
        except Exception as e:
            logger.warning("table_tool_fallback: build_table_html failed: %s", e)
            continue
        response_data.items[i] = item.model_copy(
            update={"type": ContentType.TABLE, "content": html}
        )
        logger.info("table_tool_fallback: replaced tool-call-as-text with table HTML for item %s", i)
