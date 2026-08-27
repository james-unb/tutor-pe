from django.db import models
import uuid

from .Question import Question
from .Item import Item

class Solution(models.Model):
    id = models.CharField(primary_key=True, max_length=20) # e.g., 'l1q01' or 'l1q01ia'
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='solutions')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='solutions', null=True, blank=True)
    text = models.TextField()
