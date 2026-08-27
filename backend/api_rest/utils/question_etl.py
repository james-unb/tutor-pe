"""
ETL de exibição para questões (simulados e listas).
Independente do sistema que processa LaTeX dos chats (clean_latex).
Normaliza quebras de linha para texto fluir e usar toda a largura disponível.
"""
import re

from api_rest.utils.latex_utils import clean_latex


def process_question_display(text: str) -> str:
    """
    Normaliza quebras de linha em texto já processado por clean_latex.
    Colapsa sequências de <br>, \\n e espaços em um espaço, preservando
    um <br> apenas para separação de parágrafo (dupla quebra).
    Não altera blocos de matemática nem tabelas HTML.
    """
    if not text or not text.strip():
        return text

    # 1. Proteger blocos que não devem ser alterados
    blocks = []
    placeholder_fmt = "____QUESTION_BLOCK_{}____"

    def _protect(match):
        idx = len(blocks)
        blocks.append(match.group(0))
        return placeholder_fmt.format(idx)

    # Tabelas HTML (podem conter \n e espaços)
    text = re.sub(r'<table[\s\S]*?</table>', _protect, text, flags=re.IGNORECASE)
    # Blocos de matemática: $$ ... $$ e \( ... \)
    text = re.sub(r'\$\$[\s\S]*?\$\$', _protect, text)
    text = re.sub(r'\\\([\s\S]*?\\\)', _protect, text)

    # 2. Marcar quebras de parágrafo (dupla ou mais) antes de colapsar
    para_placeholder = "____PARA_BR____"
    text = re.sub(r'(?:<br\s*/?\s*>|\r?\n)\s*(?:<br\s*/?\s*>|\r?\n)+', para_placeholder, text, flags=re.IGNORECASE)

    # 3. Colapsar qualquer sequência de <br>, \n, \r e espaços em um único espaço
    text = re.sub(r'(?:<br\s*/?\s*>|\r?\n|\s)+', ' ', text, flags=re.IGNORECASE)
    text = text.strip()

    # 4. Restaurar quebra de parágrafo
    text = text.replace(para_placeholder, '<br>')

    # 5. Restaurar blocos protegidos
    for i, content in enumerate(blocks):
        text = text.replace(placeholder_fmt.format(i), content)

    return text.strip()


def process_question_text(raw_or_cleaned: str) -> str:
    """
    Pipeline completo para texto de questão: clean_latex + normalização de exibição.
    Use apenas para enunciado/alternativas/solução de simulados e listas.
    """
    if not raw_or_cleaned:
        return raw_or_cleaned or ""
    cleaned = clean_latex(raw_or_cleaned)
    return process_question_display(cleaned)
