from django.contrib import admin
# Register your models here.
from api_rest.models import *

admin.site.register(User)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(Assignments)
admin.site.register(Question)
admin.site.register(Item)
admin.site.register(Solution)
admin.site.register(Simulado)
admin.site.register(SimuladoQuestion)
admin.site.register(QuestionFromCSV)

