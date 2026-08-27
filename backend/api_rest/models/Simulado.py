from django.db import models
import uuid
from .User import User

class Simulado(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simulados')
    prova = models.IntegerField()  # 1, 2 ou 3
    dificuldade_media = models.FloatField()
    concluido = models.BooleanField(default=False)
    nota = models.FloatField(null=True, blank=True)
    tempo_segundos = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Simulado {self.id} (Prova {self.prova})"
