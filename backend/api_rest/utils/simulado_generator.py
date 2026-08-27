import random

from django.db import transaction
from django.db.models import Avg
from api_rest.models import QuestionFromCSV, Simulado, SimuladoQuestion
import numpy as np

def generate_simulado(prova: int, user, target_dificuldade: float = None):
    """
    Gera um simulado com 10 questões, uma de cada conteúdo (p=1 a 10),
    com dificuldades próximas à target_dificuldade.
    """
    
    # 1. Buscar todas as questões da prova especificada
    questions_qs = QuestionFromCSV.objects.filter(prova=prova)
    
    if not questions_qs.exists():
        raise ValueError(f"Não foram encontradas questões para a prova {prova}.")

    # 2. Se target_dificuldade não for fornecido, calcular a média geral
    if target_dificuldade is None:
        target_dificuldade = questions_qs.aggregate(Avg('dificuldade'))['dificuldade__avg'] or 0.5
    
    # 3. Identificar os conteúdos disponíveis para esta prova
    available_contents = sorted(list(questions_qs.values_list('conteudo', flat=True).distinct()))
    
    # Pegar os primeiros 10 conteúdos (ou todos se houver menos de 10) e embaralhar a ordem
    contents_to_pick = list(available_contents[:10])
    random.shuffle(contents_to_pick)

    # 4. Pegar IDs de questões que o usuário já resolveu
    seen_questions = set(SimuladoQuestion.objects.filter(simulado__user=user).values_list('question_id', flat=True))

    # Modelos já vistos por conteúdo (para priorizar variações diferentes)
    seen_models_by_content = {}
    if seen_questions:
        for conteudo, modelo in QuestionFromCSV.objects.filter(id__in=seen_questions).values_list('conteudo', 'modelo'):
            seen_models_by_content.setdefault(conteudo, set()).add(modelo)

    selected_questions = []

    # 5. Para cada conteúdo identificado (ordem já embaralhada)
    for p in contents_to_pick:
        content_questions = list(questions_qs.filter(conteudo=p))
        
        if not content_questions:
            continue

        # Tentar priorizar questões que o usuário ainda não viu
        unseen_questions = [q for q in content_questions if q.id not in seen_questions]
        
        # Se houver questões inéditas, usamos apenas elas. Caso contrário, usamos todas (repetição necessária)
        candidates = unseen_questions if unseen_questions else content_questions

        # Encontrar a diferença mínima para este pool de candidatas
        min_diff = min(abs(q.dificuldade - target_dificuldade) for q in candidates)
        
        # Identificar todas as questões que empatam com essa diferença mínima no pool escolhido
        best_candidates = [q for q in candidates if abs(q.dificuldade - target_dificuldade) == min_diff]

        # Preferir modelos (variações) que o usuário ainda não viu para este conteúdo
        seen_models = seen_models_by_content.get(p, set())
        unseen_model_candidates = [q for q in best_candidates if q.modelo not in seen_models]
        pool = unseen_model_candidates if unseen_model_candidates else best_candidates

        selected_questions.append(random.choice(pool))
    
    if not selected_questions:
        raise ValueError(f"Não foi possível selecionar questões para a prova {prova}.")
    
    # 4. Calcular a dificuldade média real das selecionadas
    avg_diff = sum(q.dificuldade for q in selected_questions) / len(selected_questions)
    
    # 5. Criar objetos no banco de dados em uma transação
    with transaction.atomic():
        simulado = Simulado.objects.create(
            user=user,
            prova=prova,
            dificuldade_media=avg_diff
        )
        
        for idx, q in enumerate(selected_questions, start=1):
            SimuladoQuestion.objects.create(
                simulado=simulado,
                question_id=q.id,
                conteudo=q.conteudo,
                dificuldade=q.dificuldade,
                order=idx
            )
            
    return simulado
