from django.db import models
import uuid

class Assignments(models.Model):
    number = models.IntegerField(unique=True)