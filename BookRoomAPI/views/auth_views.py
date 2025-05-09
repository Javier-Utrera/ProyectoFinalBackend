from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes


from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token

from datetime import timedelta
from django.utils import timezone

from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Usuario
from ..serializers import (
    UsuarioSerializerRegistro, UsuarioSerializer,
    UsuarioLoginResponseSerializer, LoginSerializer
)

#============================================================================================
# AUTENTICACION Y REGISTRO
#============================================================================================

# 1) REGISTRAR USUARIO
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    operation_summary="Registro de usuario",
    operation_description="""
        Registra un nuevo usuario con rol CLIENTE.
        - Crea el usuario
        - Le asigna el grupo "Clientes"
        - Devuelve un token OAuth2 válido por 10 horas
    """,
    request_body=UsuarioSerializerRegistro,
    responses={
        201: "Usuario registrado correctamente",
        400: "Errores de validación",
        500: "Error interno al generar el token"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_usuario(request):
    # 1.1) Validar entrada
    serializer = UsuarioSerializerRegistro(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 1.2) Crear usuario con rol CLIENTE
    user = Usuario.objects.create_user(
        username=serializer.validated_data["username"],
        email=serializer.validated_data.get("email", ""),
        password=serializer.validated_data["password1"],
        rol=Usuario.CLIENTE
    )

    # 1.3) Asignar al grupo "Clientes" si existe
    try:
        grupo = Group.objects.get(name="Clientes")
        grupo.user_set.add(user)
    except Group.DoesNotExist:
        pass

    # 1.4) Recuperar aplicación OAuth2
    try:
        app = Application.objects.get(name="Angular App")
    except Application.DoesNotExist:
        return Response({"error": "Aplicación OAuth2 no encontrada."}, status=500)

    # 1.5) Generar token y devolver respuesta
    token = AccessToken.objects.create(
        user=user,
        token=generate_token(),
        application=app,
        expires=timezone.now() + timedelta(hours=10),
        scope='read write'
    )
    return Response({
        "access_token": token.token,
        "user": UsuarioSerializer(user).data
    }, status=status.HTTP_201_CREATED)


# 2) OBTENER USUARIO POR TOKEN
@swagger_auto_schema(
    method='get',
    tags=["Registro y login"],
    operation_summary="Obtener usuario por token",
    operation_description="Devuelve la información del usuario asociado a un token OAuth2.",
    manual_parameters=[
        openapi.Parameter('token', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
    ],
    responses={
        200: openapi.Response(description="Usuario encontrado"),
        404: openapi.Response(description="Token o usuario no encontrado")
    }
)
@api_view(['GET'])
def obtener_usuario_por_token(request, token):
    # 2.1) Buscar AccessToken
    try:
        access_token = AccessToken.objects.get(token=token)
        usuario = Usuario.objects.get(id=access_token.user_id)
    except AccessToken.DoesNotExist:
        return Response({"error": "Token no válido."}, status=status.HTTP_404_NOT_FOUND)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    # 2.2) Serializar y devolver usuario
    return Response(UsuarioSerializer(usuario).data, status=status.HTTP_200_OK)


# 3) LOGIN DE USUARIO
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    request_body=LoginSerializer,
    operation_summary="Login de usuario",
    operation_description="Autentica credenciales y devuelve un token OAuth2.",
    responses={
        200: "Login correcto",
        400: "Credenciales inválidas",
        500: "Error del servidor"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    # 3.1) Autenticar con Django
    user = authenticate(
        username=request.data.get("username"),
        password=request.data.get("password")
    )
    if user is None:
        return Response({"error": "Credenciales inválidas."}, status=status.HTTP_400_BAD_REQUEST)

    # 3.2) Recuperar o crear token vigente
    try:
        app = Application.objects.get(name="Angular App")
    except Application.DoesNotExist:
        return Response({"error": "Aplicación OAuth2 no encontrada."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    token = AccessToken.objects.filter(user=user, application=app, expires__gt=timezone.now()).first()
    if not token:
        token = AccessToken.objects.create(
            user=user,
            token=generate_token(),
            application=app,
            expires=timezone.now() + timedelta(hours=10),
            scope='read write'
        )

    # 3.3) Devolver token y datos de usuario
    return Response({
        "access_token": token.token,
        "user": UsuarioLoginResponseSerializer(user).data
    }, status=status.HTTP_200_OK)


# 4) LOGOUT DE USUARIO
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    operation_summary="Logout de usuario",
    operation_description="Elimina el token actual, cerrando sesión.",
    responses={200: "Sesión cerrada correctamente", 401: "Token inválido"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_usuario(request):
    # 4.1) Borrar el token del usuario
    if request.auth:
        request.auth.delete()
    # 4.2) Confirmar cierre de sesión
    return Response({"mensaje": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)
