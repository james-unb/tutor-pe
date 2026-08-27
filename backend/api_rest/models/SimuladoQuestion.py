from django.db import models
import uuid
from .Simulado import Simulado

class SimuladoQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulado = models.ForeignKey(Simulado, related_name='questions', on_delete=models.CASCADE)
    question_id = models.CharField(max_length=255)  # ID da questão no CSV
    conteudo = models.IntegerField()  # p (1-10)
    dificuldade = models.FloatField()
    order = models.IntegerField()  # 1-10
    resposta_usuario = models.CharField(max_length=1, null=True, blank=True)

    def __str__(self):
        return f"Questão {self.question_id} do Simulado {self.simulado.id}"
