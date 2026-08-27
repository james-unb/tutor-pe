from django.http import JsonResponse
from rest_framework.decorators import api_view
from api_rest.models import (
    Simulado,
    SimuladoQuestion,
    QuestionFromCSV,
    SimuladoChatSession,
    SimuladoChatMessage,
)
from api_rest.utils.simulado_generator import generate_simulado
from api_rest.utils.latex_utils import clean_latex
from api_rest.utils.question_etl import process_question_text
from api_rest.utils.table_tool_fallback import fix_table_tool_text_in_response
from api_rest.PydanticAi import chat_with_agent_simulado
import json

@api_view(["POST", "GET"])
def list_or_create(request):
    if request.method == "POST":
        try:
            data = request.data
            prova = data.get("prova")
            target_dificuldade = data.get("target_dificuldade")
            
            if prova is None:
                return JsonResponse({"error": "O campo 'prova' é obrigatório."}, status=400)
            
            simulado = generate_simulado(prova, request.intern_user, target_dificuldade)
            
            # Formatar a resposta com as questões simplificadas
            questions_data = []
            for sq in simulado.questions.all().order_by('order'):
                questions_data.append({
                    "id": sq.question_id,
                    "conteudo": sq.conteudo,
                    "dificuldade": sq.dificuldade,
                    "order": sq.order
                })
            
            return JsonResponse({
                "status": "success",
                "id": str(simulado.id),
                "prova": simulado.prova,
                "dificuldade_media": simulado.dificuldade_media,
                "concluido": simulado.concluido,
                "nota": simulado.nota,
                "tempo_segundos": simulado.tempo_segundos,
                "created_at": simulado.created_at,
                "questions": questions_data
            }, status=201)
            
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Erro interno: {str(e)}"}, status=500)
            
    elif request.method == "GET":
        prova = request.query_params.get("prova")
        simulados = Simulado.objects.filter(user=request.intern_user).order_by('-created_at')
        
        if prova:
            simulados = simulados.filter(prova=prova)
            
        data = [
            {
                "id": str(s.id),
                "prova": s.prova,
                "dificuldade_media": s.dificuldade_media,
                "concluido": s.concluido,
                "nota": s.nota,
                "tempo_segundos": s.tempo_segundos,
                "created_at": s.created_at
            } for s in simulados
        ]
        return JsonResponse(data, safe=False)

@api_view(["GET"])
def get_simulado(request, id):
    try:
        simulado = Simulado.objects.get(id=id, user=request.intern_user)
        questions_data = []
        for sq in simulado.questions.all().order_by('order'):
            questions_data.append({
                "id": sq.question_id,
                "conteudo": sq.conteudo,
                "dificuldade": sq.dificuldade,
                "order": sq.order,
                "resposta_usuario": sq.resposta_usuario
            })
            
        return JsonResponse({
            "id": str(simulado.id),
            "prova": simulado.prova,
            "dificuldade_media": simulado.dificuldade_media,
            "concluido": simulado.concluido,
            "nota": simulado.nota,
            "tempo_segundos": simulado.tempo_segundos,
            "created_at": simulado.created_at,
            "questions": questions_data
        })
    except Simulado.DoesNotExist:
        return JsonResponse({"error": "Simulado não encontrado."}, status=404)

@api_view(["GET"])
def get_questoes(request, id):
    try:
        simulado = Simulado.objects.get(id=id, user=request.intern_user)
        sqs = simulado.questions.all().order_by('order')
        q_ids = [sq.question_id for sq in sqs]
        
        questions_map = {q.id: q for q in QuestionFromCSV.objects.filter(id__in=q_ids)}
        
        data = []
        for sq in sqs:
            q = questions_map.get(sq.question_id)
            if q:
                question_data = {
                    "id": q.id,
                    "order": sq.order,
                    "conteudo": q.conteudo,
                    "materia": q.materia,
                    "enunciado": process_question_text(q.enunciado or ""),
                    "dificuldade": q.dificuldade,
                    "resposta_usuario": sq.resposta_usuario
                }
                alternativas = getattr(q, "alternativas", None)
                if alternativas and len(alternativas) == 5:
                    question_data["alternativas"] = [process_question_text(a or "") for a in alternativas]
                if simulado.concluido:
                    question_data["solucao"] = process_question_text(q.solucao or "")
                    gabarito = _gabarito_ou_extrair_da_solucao(q)
                    if gabarito:
                        question_data["gabarito"] = gabarito
                data.append(question_data)
                
        return JsonResponse(data, safe=False)
    except Simulado.DoesNotExist:
        return JsonResponse({"error": "Simulado não encontrado."}, status=404)

@api_view(["POST"])
def submit_resposta(request, id):
    try:
        simulado = Simulado.objects.get(id=id, user=request.intern_user)
        if simulado.concluido:
            return JsonResponse({"error": "Este simulado já foi finalizado."}, status=400)
            
        data = request.data
        question_id = data.get("question_id")
        resposta = data.get("resposta") # Ex: 'A', 'B', etc.
        
        if not question_id or not resposta:
            return JsonResponse({"error": "Campos 'question_id' e 'resposta' são obrigatórios."}, status=400)
            
        try:
            sq = SimuladoQuestion.objects.get(simulado=simulado, question_id=question_id)
            sq.resposta_usuario = resposta.upper()
            sq.save()
            return JsonResponse({"status": "success", "message": "Resposta salva."})
        except SimuladoQuestion.DoesNotExist:
            return JsonResponse({"error": "Questão não pertence a este simulado."}, status=404)
            
    except Simulado.DoesNotExist:
        return JsonResponse({"error": "Simulado não encontrado."}, status=404)

@api_view(["POST"])
def finalizar_simulado(request, id):
    try:
        simulado = Simulado.objects.get(id=id, user=request.intern_user)
        if simulado.concluido:
            return JsonResponse({"error": "Este simulado já foi finalizado anteriormente."}, status=400)
            
        data = request.data
        tempo_segundos = data.get("tempo_segundos")
        
        sqs = simulado.questions.all()
        q_ids = [sq.question_id for sq in sqs]
        questions_map = {q.id: q for q in QuestionFromCSV.objects.filter(id__in=q_ids)}
        
        acertos = 0
        total = sqs.count()
        
        for sq in sqs:
            q = questions_map.get(sq.question_id)
            if q:
                gabarito = _gabarito_ou_extrair_da_solucao(q)
                if gabarito and sq.resposta_usuario and sq.resposta_usuario.upper() == gabarito:
                    acertos += 1
        
        nota = (acertos / total) * 10 if total > 0 else 0
        
        simulado.concluido = True
        simulado.nota = nota
        if tempo_segundos is not None:
            simulado.tempo_segundos = tempo_segundos
        simulado.save()
        
        return JsonResponse({
            "status": "success",
            "nota": nota,
            "acertos": acertos,
            "total": total,
            "tempo_segundos": simulado.tempo_segundos
        })
        
    except Simulado.DoesNotExist:
        return JsonResponse({"error": "Simulado não encontrado."}, status=404)


def _gabarito_ou_extrair_da_solucao(q):
    """Retorna o gabarito da questão: coluna gabarito ou extração da solução (fallback)."""
    if getattr(q, "gabarito", None):
        return (q.gabarito or "").strip().upper() or None
    solucao = q.solucao or ""
    if ")}" not in solucao:
        return None
    partes = solucao.split(")}")[-1].strip().split()
    for idx, word in enumerate(partes):
        if "Verdadeiro" in word:
            return chr(65 + idx)
    return None


def _build_question_context(q):
    """Monta string de contexto (enunciado, alternativas, gabarito, correção) para o agente."""
    parts = [
        f"Enunciado: {process_question_text(q.enunciado or '')}",
    ]
    alternativas = getattr(q, "alternativas", None)
    if alternativas and len(alternativas) == 5:
        labels = ["A", "B", "C", "D", "E"]
        alt_text = " ".join(f"{labels[i]}) {process_question_text(alternativas[i] or '')}" for i in range(5))
        parts.append(f"Alternativas: {alt_text}")
    gabarito = _gabarito_ou_extrair_da_solucao(q)
    if gabarito:
        parts.append(f"Alternativa correta (gabarito): {gabarito}")
    parts.append(
        "A correção abaixo é a explicação oficial da alternativa correta (gabarito)."
    )
    parts.append(f"Correção (solução): {process_question_text(q.solucao or '')}")
    return "\n\n".join(parts)


def _format_response_items(response_data):
    """Converte ChatResponse em final_response (items) e formatted_content, como em ChatViews."""
    final_response = [
        {"type": item.type, "content": item.content}
        for item in response_data.items
    ]
    formatted_content = ""
    for item in response_data.items:
        if item.type == "title":
            formatted_content += f"**{item.content}**\n\n"
        elif item.type == "subtitle":
            formatted_content += f"<h3>{item.content}</h3>\n\n"
        elif item.type == "formula":
            content = item.content.strip()
            if "<table" in content:
                formatted_content += content
            elif content.startswith("$$") or content.startswith("\\["):
                formatted_content += content
            else:
                formatted_content += f"$${content}$$\n\n"
        elif item.type == "list_item":
            formatted_content += f"- {item.content}\n"
        elif item.type == "table":
            formatted_content += item.content
        else:
            formatted_content += f"{item.content}\n\n"
    return final_response, clean_latex(formatted_content.strip())


@api_view(["GET", "POST"])
def simulado_question_chat(request, simulado_id, question_id):
    """
    GET: lista mensagens do chat da questão do simulado.
    POST: envia mensagem e recebe resposta do agente (questão + correção como contexto).
    """
    user = request.intern_user

    try:
        simulado = Simulado.objects.get(id=simulado_id, user=user)
    except Simulado.DoesNotExist:
        return JsonResponse({"error": "Simulado não encontrado."}, status=404)

    if not simulado.concluido:
        return JsonResponse(
            {"error": "O simulado precisa estar finalizado para acessar o chat da correção."},
            status=400,
        )

    try:
        sq = SimuladoQuestion.objects.get(simulado=simulado, question_id=question_id)
    except SimuladoQuestion.DoesNotExist:
        return JsonResponse({"error": "Questão não pertence a este simulado."}, status=404)

    if request.method == "GET":
        try:
            session = SimuladoChatSession.objects.get(user=user, simulado_question=sq)
        except SimuladoChatSession.DoesNotExist:
            return JsonResponse([], safe=False)
        messages = session.messages.all().order_by("timestamp")
        data = [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.strftime("%H:%M"),
            }
            for m in messages
        ]
        return JsonResponse(data, safe=False)

    # POST
    prompt = request.data.get("message", "")
    if not prompt:
        return JsonResponse({"error": "Message is required"}, status=400)

    session, _ = SimuladoChatSession.objects.get_or_create(
        user=user,
        simulado_question=sq,
    )

    SimuladoChatMessage.objects.create(session=session, role="user", content=prompt)

    history_messages = (
        SimuladoChatMessage.objects.filter(session=session)
        .order_by("-timestamp")[:20]
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(list(history_messages))
    ]

    try:
        q = QuestionFromCSV.objects.get(id=question_id)
    except QuestionFromCSV.DoesNotExist:
        return JsonResponse({"error": "Questão não encontrada."}, status=404)

    question_context = _build_question_context(q)
    response_data, _ = chat_with_agent_simulado(prompt, history, question_context)

    fix_table_tool_text_in_response(response_data)
    final_response, formatted_content = _format_response_items(response_data)
    msg_content = formatted_content

    SimuladoChatMessage.objects.create(
        session=session,
        role="assistant",
        content=msg_content,
    )

    return JsonResponse({
        "status": "success",
        "session_id": str(session.id),
        "data": {
            "items": final_response,
            "formatted_content": msg_content,
        },
    }, safe=False)
