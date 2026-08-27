from dotenv import load_dotenv
import os
from django.http import JsonResponse
from jose import jwt, JWTError, ExpiredSignatureError

from api_rest.models import User

load_dotenv()
JWT_SECRET = os.getenv('JWT_SECRET')
ALGORITHM = "HS256"

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        

    def __call__(self, request):

        if request.path in ["/api/login/google/"] or request.path.startswith("/admin"):
            return self.get_response(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"status": "error", "message": "Invalid token"},
                status=401,
            )
        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            user_id = payload.get("id")
            if not user_id:
                raise JWTError("") 
            userOnDb = User.objects.get(pk=user_id)
            if not userOnDb:
                raise JWTError("")
            request.intern_user = userOnDb
        except ExpiredSignatureError:
            return JsonResponse({"status": "error", "message": "Expired token"}, status=401 )
        except JWTError:
            return JsonResponse({"status": "error", "message": "Invalid token"}, status=401 )
        except Exception as error:
            return JsonResponse({"status": "error", "message": "Invalid token"}, status=401)

        response = self.get_response(request)
        return response
