import logging

from django.http import JsonResponse
from rest_framework.decorators import api_view
from api_rest.PydanticAi import chat_with_agent
from ..models import ChatSession, ChatMessage
import os
import re
from api_rest.utils.latex_utils import clean_latex
from api_rest.utils.table_tool_fallback import fix_table_tool_text_in_response

logger = logging.getLogger(__name__)
JWT_SECRET = os.getenv("JWT_SECRET")

@api_view(["POST"])
def handle_prompt(request):
    user=request.intern_user
    prompt = request.data.get("message", "")
    session_id = request.data.get("session_id")

    if not prompt:
        return JsonResponse({"error": "Message is required"}, status=400)

    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return JsonResponse({"error": "Session not found"}, status=404)
    else:
        session = ChatSession.objects.create(user=user)

    ChatMessage.objects.create(session=session, role='user', content=prompt)
    
    history_messages = ChatMessage.objects.filter(session=session)\
        .select_related('related_question', 'related_question__assignment')\
        .prefetch_related('related_question__itens')\
        .order_by('-timestamp')[:20]
    
    history = []
    for msg in reversed(history_messages):
        content = msg.content
        if msg.related_question:
            q = msg.related_question
            q_text = f"\n\n[System Context] Questão Vinculada:\nEnunciado: {q.enunciado}\n"
            for item in q.itens.all():
                q_text += f"{item.codigo}) {item.enunciado}\n"
            content = f"{content}{q_text}"
        
        history.append({"role": msg.role, "content": content})

    response_data, question_id = chat_with_agent(prompt, history)

    # Fallback: se o modelo escreveu a chamada da tool como texto, converter em HTML
    fix_table_tool_text_in_response(response_data)

    final_response = [
        {
            "type": item.type,
            "content": item.content
        } for item in response_data.items
    ]
    
    formatted_content = ""
    for item in response_data.items:
        if item.type == 'title':
            formatted_content += f"**{item.content}**\n\n"
        elif item.type == 'subtitle':
            formatted_content += f"<h3>{item.content}</h3>\n\n"
        elif item.type == 'formula':
            content = item.content.strip()
            # If it's HTML (table), don't wrap in $$
            if '<table' in content:
                formatted_content += f"{content}"
            # If it already has delimiters, use it as is
            elif content.startswith('$$') or content.startswith('\\['):
                formatted_content += f"{content}"
            # Otherwise, wrap in $$
            else:
                formatted_content += f"$${content}$$\n\n"
        elif item.type == 'list_item':
            formatted_content += f"- {item.content}\n"
        elif item.type == 'table':
            formatted_content += f"{item.content}"
        else:
            formatted_content += f"{item.content}\n\n"
    
    msg_content = clean_latex(formatted_content.strip())
    msg = ChatMessage.objects.create(session=session, role='assistant', content=msg_content)
    
    question_data = None
    if question_id:
        msg.related_question_id = question_id
        msg.save()
        try:
            q = msg.related_question
            if q:
                question_data = {
                    "id": q.id,
                    "number": q.number,
                    "assignment": q.assignment.number,
                    "enunciado": clean_latex(q.enunciado or ""),
                    "itens": [
                        {"codigo": i.codigo, "enunciado": clean_latex(i.enunciado or "")}
                        for i in q.itens.all()
                    ]
                }
        except Exception as e:
            logger.exception("Error fetching question data: %s", e)

    if not session.title:
        session.title = prompt[:30] + "..." if len(prompt) > 30 else prompt
        session.save()
    
    return JsonResponse({
        "status": "success",
        "session_id": str(session.id),
        "title": session.title,
        "data": {
            "items": final_response,
            "formatted_content": msg_content,
            "question_data": question_data
        }
    }, safe=False)

@api_view(["GET"])
def get_user_chats(request):
    user = request.intern_user
    
    sessions = ChatSession.objects.filter(user=user).order_by('-updated_at')
    data = [
        {
            "id": str(s.id),
            "title": s.title,
            "timestamp": s.updated_at.strftime("%d/%m/%Y %H:%M")
        } for s in sessions
    ]
    return JsonResponse(data, safe=False)

@api_view(["GET"])
def get_chat_messages(request, session_id):
    user = request.intern_user
    
    try:
        session = ChatSession.objects.get(id=session_id, user=user)
        messages = session.messages.all()\
            .select_related('related_question', 'related_question__assignment')\
            .prefetch_related('related_question__itens')
        
        data = []
        for m in messages:
            msg_data = {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.strftime("%H:%M")
            }
            if m.related_question:
                q = m.related_question
                msg_data["question_data"] = {
                    "id": q.id,
                    "number": q.number,
                    "assignment": q.assignment.number,
                    "enunciado": clean_latex(q.enunciado or ""),
                    "itens": [
                        {"codigo": i.codigo, "enunciado": clean_latex(i.enunciado or "")}
                        for i in q.itens.all()
                    ]
                }
            data.append(msg_data)
            
        return JsonResponse(data, safe=False)
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)
