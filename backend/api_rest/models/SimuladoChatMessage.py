from django.db import models
import uuid
from .SimuladoChatSession import SimuladoChatSession


class SimuladoChatMessage(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    session = models.ForeignKey(
        SimuladoChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=50)  # 'user' or 'assistant'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role} @ {self.timestamp}"
