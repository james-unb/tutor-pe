import logging

from pydantic_ai import RunContext, Tool
from api_rest.models import Question
from api_rest.utils.latex_utils import clean_latex

logger = logging.getLogger(__name__)


def get_question_by_number(ctx: RunContext[dict], numero_lista: int, numero_questao: int) -> str:
    """
    Busca o enunciado, itens e soluções de uma questão específica no banco de dados.
    Utilize esta ferramenta APENAS UMA VEZ por questão solicitada. Ela retorna todas as informações necessárias (enunciado, itens e soluções).
    
    Se o aluno não informar o número da lista ou da questão, solicite gentilmente a informação faltante antes de usar a ferramenta.
    
    exemplo de uso:
        buscar_questao_por_numero(numero_lista=1, numero_questao=1)
    """
    try:
        logger.info("Tool get_question_by_number executada: %s - %s", numero_lista, numero_questao)
        questionInDb = Question.objects.filter(assignment__number=numero_lista, number=numero_questao).first()
        logger.debug("Questão encontrada: %s", questionInDb)
        if not questionInDb:
            return f"Não encontrei a Questão {numero_questao} da Lista {numero_lista}. Informe ao usuário que as informações dadas são invalidas."
        
        if ctx.deps is not None:
            ctx.deps['question_id'] = questionInDb.id

        toolResponse = f"Questão {questionInDb.number} (Lista {questionInDb.assignment.number})\n\n"
        toolResponse += f"{clean_latex(questionInDb.enunciado)}\n\n"
        
        for item in questionInDb.itens.all():
            toolResponse += f"Item {item.codigo}) {clean_latex(item.enunciado)}\n"
        
        toolResponse += "\nSoluções:\n"
        for sol in questionInDb.solutions.filter(item__isnull=True):
            toolResponse += f"{clean_latex(sol.text)}\n"
        
        for item in questionInDb.itens.all():
            for sol in item.solutions.all():
                toolResponse += f"Solução Item {item.codigo}: {clean_latex(sol.text)}\n"
        
        logger.info("Tool get_question_by_number finalizada")
        return toolResponse
    except Exception as e:
        logger.exception("Error in tool: %s", e)
        return f"Erro ao buscar dados: {str(e)}"

    
get_question_by_number_tool = Tool(
    get_question_by_number,
    name="buscar_questao_por_numero",
    description="Busca o enunciado, itens e soluções de uma questão específica no banco de dados."
)