from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Registra um usuário e retorna tokens JWT + dados do usuário.
    - username = email (compatível com seu legado)
    - validações case-insensitive
    - retorna last_login (normalmente None após registro)
    """
    first_name = serializers.CharField(required=True)
    last_name  = serializers.CharField(required=True)
    email      = serializers.EmailField(required=True)
    password   = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    password2  = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model  = User
        fields = ['id', 'first_name', 'last_name', 'email', 'password', 'password2']

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este e-mail já está em uso.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        email    = validated_data['email']

        # username = email
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=password,
        )

        # Grupo padrão
        default_group, _ = Group.objects.get_or_create(name='user')
        user.groups.add(default_group)

        # Tokens
        refresh = RefreshToken.for_user(user)
        groups  = list(user.groups.values_list('name', flat=True))

        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": groups[0] if groups else "user",
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserLoginSerializer(serializers.Serializer):
    """
    Login com apenas dois campos no payload: username, password.
    - No Browsable API, o 'username' aparece com rótulo "Email"
    - Se digitarem um email no 'username', mapeia para o username real antes de autenticar
    - Atualiza e retorna last_login
    """
    username = serializers.CharField(label="Email")
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        username_input = (data.get("username") or "").strip()
        password       = data.get("password")

        if not username_input or not password:
            raise serializers.ValidationError("Informe username e password.")

        # Se digitarem um email aqui, tenta mapear para o username real
        if '@' in username_input:
            try:
                u = User.objects.get(email__iexact=username_input)
                username_field = getattr(User, 'USERNAME_FIELD', 'username')
                username_input = getattr(u, username_field, getattr(u, 'username', username_input))
            except User.DoesNotExist:
                # não achou email -> tenta autenticar como username mesmo
                pass

        # Autentica (passando request do contexto, se existir)
        user = authenticate(self.context.get('request'), username=username_input, password=password)
        if not user or not getattr(user, 'is_active', True):
            # 401
            raise AuthenticationFailed("Credenciais inválidas.")

        # Atualiza last_login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Tokens
        refresh = RefreshToken.for_user(user)
        groups  = list(user.groups.values_list('name', flat=True))

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": groups[0] if groups else "user",
                "last_login": user.last_login.isoformat(),
            },
        }
