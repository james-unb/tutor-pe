from django.db import models
import uuid

from .ChatSession import ChatSession

class ChatMessage(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=50) # 'user' or 'assistant'
    content = models.TextField()
    related_question = models.ForeignKey('Question', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_messages')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']