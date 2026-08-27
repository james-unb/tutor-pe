from django.db import models
import uuid

from .User import User
from .ChatSession import ChatSession
from .ChatMessage import ChatMessage
from .Assignments import Assignments
from .Question import Question
from .Item import Item
from .Solution import Solution
from .Simulado import Simulado
from .SimuladoQuestion import SimuladoQuestion
from .SimuladoChatSession import SimuladoChatSession
from .SimuladoChatMessage import SimuladoChatMessage
from .QuestionFromCSV import QuestionFromCSV