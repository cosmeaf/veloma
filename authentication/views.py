import redis
from django.http import JsonResponse
from django.conf import settings
from .tasks import sample_task
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from authentication.serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
)

UserModel = get_user_model()

def ping_redis(request):
    try:
        r = redis.Redis(host='127.0.0.1', port=6379, db=1)
        response = r.ping()
        if response:
            return JsonResponse({'status': 'success', 'response': 'PONG'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Redis did not respond with PONG'}, status=500)
    except redis.ConnectionError as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to connect to Redis: {str(e)}'}, status=500)

def trigger_task(request):
    task = sample_task.delay()
    return JsonResponse({'status': 'success', 'task_id': task.id})


class UserRegisterViewSet(viewsets.ModelViewSet):
    """
    POST /api/auth/register/
    Registra usuário (username=email), adiciona grupo 'user',
    e retorna {access, refresh, user, last_login}.
    """
    serializer_class = UserRegisterSerializer
    queryset = UserModel.objects.all()
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.save() 
        return Response(data, status=status.HTTP_201_CREATED)


class UserLoginViewSet(viewsets.ViewSet):
    """
    POST /api/auth/login/
    Payload: { "username": "seu_username_ou_email", "password": "..." }
    Retorna {access, refresh, user}; last_login é atualizado no serializer.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = UserLoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
