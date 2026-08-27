from django.contrib import admin
from django.urls import path

from .views import ChatViews, AuthViews, SimuladoViews

urlpatterns = [
    path('chat/', ChatViews.handle_prompt),
    path('chat/history/', ChatViews.get_user_chats),
    path('chat/<str:session_id>/', ChatViews.get_chat_messages),
    path('login/google/', AuthViews.handle_login_with_google),
    
    # Simulados
    path('simulados/', SimuladoViews.list_or_create),
    path('simulados/<uuid:id>/', SimuladoViews.get_simulado),
    path('simulados/<uuid:id>/questoes/', SimuladoViews.get_questoes),
    path('simulados/<uuid:simulado_id>/questoes/<str:question_id>/chat/', SimuladoViews.simulado_question_chat),
    path('simulados/<uuid:id>/submeter/', SimuladoViews.submit_resposta),
    path('simulados/<uuid:id>/finalizar/', SimuladoViews.finalizar_simulado),
]