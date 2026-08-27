from django.db import models
import uuid

class User(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    google_id = models.CharField(max_length=255, unique=True)
    photo_url = models.URLField(blank=True, null=True)
