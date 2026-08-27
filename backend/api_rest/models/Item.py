from django.db import models
import uuid

from .Question import Question

class Item(models.Model):
    id = models.CharField(primary_key=True, max_length=20)  # e.g., 'l1q01ia'
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='itens')
    codigo = models.CharField(max_length=5)  # e.g., 'a'
    enunciado = models.TextField()
