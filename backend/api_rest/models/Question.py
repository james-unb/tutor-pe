from django.db import models
import uuid

from .Assignments import Assignments

class Question(models.Model):
    id = models.CharField(primary_key=True, max_length=20)  # e.g., 'l1q01'
    assignment = models.ForeignKey(Assignments, on_delete=models.CASCADE, related_name='questoes')
    number = models.IntegerField()
    enunciado = models.TextField()