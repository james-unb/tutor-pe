from django.db import models
import uuid
from .User import User
from .SimuladoQuestion import SimuladoQuestion


class SimuladoChatSession(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simulado_chat_sessions')
    simulado_question = models.ForeignKey(
        SimuladoQuestion,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'simulado_question'],
                name='unique_user_simulado_question_chat'
            )
        ]

    def __str__(self):
        return f"Chat simulado {self.id} ({self.user.email})"
