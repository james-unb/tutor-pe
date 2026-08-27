import logging

from django.http import JsonResponse
from rest_framework.decorators import api_view
from api_rest.PydanticAi import chat_with_agent
from asgiref.sync import async_to_sync
from google.oauth2 import id_token
from google.auth.transport import requests
from api_rest.models import User
import json
from jose import jwt
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 
if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID not found in environment variables")

JWT_SECRET = os.getenv("JWT_SECRET") 
if not JWT_SECRET:
    raise ValueError("JWT_SECRET not found in environment variables")

@api_view(["POST"])
def handle_login_with_google(request):
    try:
        body = json.loads(request.body)
        token = body.get("credential")
        
        id_info = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        email = id_info['email']
        name = id_info.get('name', '')
        google_id = id_info['sub']
        photo_url = id_info.get('picture', '')

        user, created = User.objects.update_or_create(
            email=email,
            defaults={
                'name': name,
                'google_id': google_id,
                'photo_url': photo_url
            }
        )

        payload_data = {
            "id": str(user.id),
            "exp": datetime.utcnow() + timedelta(days=1)
        }

        jwt_token = jwt.encode(
            claims=payload_data,
            key=JWT_SECRET,
            algorithm="HS256"            
        )

        return JsonResponse({
            "status": "success",
            "user": {
                "email": user.email,
                "name": user.name,
                "photo_url": user.photo_url
            },
            "token": jwt_token
        })

    except ValueError as e:
        logger.warning("Invalid token in login: %s", e)
        return JsonResponse({
            "status": "error",
            "message": f"Invalid token: {str(e)}"
        }, status=400)
