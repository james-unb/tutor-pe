import logging
from django.http import JsonResponse
import traceback

logger = logging.getLogger(__name__)

class GlobalExceptionHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        logger.error(f"Erro não tratado na URL {request.path}: {exception}", exc_info=True)
        traceback.print_exc()
        return JsonResponse({
            "status": "error",
            "message": "Ocorreu um erro interno enquanto respondiamos sua requisição. Tente novamente mais tarde.",
        }, status=500)