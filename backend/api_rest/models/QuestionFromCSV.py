from django.db import models

class QuestionFromCSV(models.Model):
    id = models.CharField(primary_key=True, max_length=255)  # ID do CSV
    prova = models.IntegerField()
    conteudo = models.IntegerField()  # p
    modelo = models.IntegerField()  # m
    versao = models.IntegerField()  # v
    dificuldade = models.FloatField()
    materia = models.CharField(max_length=255)
    enunciado = models.TextField()
    alternativas = models.JSONField(default=list, blank=True)  # list of 5 strings (A–E)
    solucao = models.TextField()
    gabarito = models.CharField(max_length=1, null=True, blank=True)


    def __str__(self):
        return f"Questão {self.id} (P{self.prova}, p{self.conteudo})"
