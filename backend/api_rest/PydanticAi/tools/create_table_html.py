from pydantic_ai import RunContext, Tool
from typing import List, Optional


def build_table_html(
    headers: List[str],
    rows: List[List[str]],
    caption: Optional[str] = None,
) -> str:
    """Gera o código HTML para uma tabela padronizada (lógica pura, sem contexto)."""
    html = '<table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">'
    if caption:
        html += f'<caption style="caption-side: top; font-weight: bold; padding: 8px;">{caption}</caption>'
    
    if headers:
        html += '<thead><tr>'
        for h in headers:
            html += f'<th style="padding: 8px; border: 1px solid #ddd; background-color: rgba(255,255,255,0.05);">{h}</th>'
        html += '</tr></thead>'
    
    html += '<tbody>'
    for row in rows:
        html += '<tr>'
        for cell in row:
            html += f'<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{cell}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html


def create_table_html(ctx: RunContext[dict], headers: List[str], rows: List[List[str]], caption: str = None) -> str:
    """
    Gera o código HTML para uma tabela padronizada.
    Utilize para apresentar distribuições de probabilidade, tabelas de frequências ou conjuntos de dados.
    Invoque esta ferramenta através do sistema de tools; não descreva nem escreva a chamada no texto da resposta.
    
    Args:
        headers: Lista de strings para o cabeçalho da tabela.
        rows: Lista de listas de strings para as linhas da tabela.
        caption: (Opcional) Legenda descritiva para a tabela.
    """
    return build_table_html(headers=headers, rows=rows, caption=caption)

create_table_html_tool = Tool(
    create_table_html,
    name="gerar_tabela_html",
    description="Gera o código HTML para uma tabela padronizada. Invoque esta ferramenta através do sistema de tools; não descreva nem escreva a chamada no texto da resposta."
)
