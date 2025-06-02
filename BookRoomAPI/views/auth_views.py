from rest_framework import status,generics, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token

from datetime import timedelta
from django.utils import timezone

from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Usuario,Mensaje,Relato
from ..serializers import (
    UsuarioSerializerRegistro, UsuarioSerializer,
    UsuarioLoginResponseSerializer, LoginSerializer,MensajeSerializer
)
from django.shortcuts import get_object_or_404

#============================================================================================
# AUTENTICACION Y REGISTRO
#============================================================================================

# 1) REGISTRAR USUARIO
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    operation_summary="Registro de usuario",
    operation_description="Registra un nuevo usuario con rol CLIENTE y devuelve un token OAuth2.",
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
    serializer = UsuarioSerializerRegistro(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Datos inválidos", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = Usuario.objects.create_user(
        username=serializer.validated_data["username"],
        email=serializer.validated_data.get("email", ""),
        password=serializer.validated_data["password1"],
        rol=Usuario.CLIENTE
    )

    # Application uOAuth2 (404 si no existe)
    app = get_object_or_404(Application, name="BookRoomAPI")

    token = AccessToken.objects.create(
        user=user,
        token=generate_token(),
        application=app,
        expires=timezone.now() + timedelta(hours=10),
        scope='read write'
    )

    return Response(
        {
            "access_token": token.token,
            "user": UsuarioSerializer(user).data
        },
        status=status.HTTP_201_CREATED
    )


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
        401: openapi.Response(description="Token no válido o expirado"),
        404: openapi.Response(description="Usuario no encontrado")
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_usuario_por_token(request, token):
    # 1) Buscar el AccessToken y verificar que no esté expirado
    access_token = AccessToken.objects.filter(token=token).first()
    if not access_token or access_token.expires <= timezone.now():
        return Response(
            {"error": "Token no válido o expirado."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # 2) Recuperar usuario asociado
    usuario = get_object_or_404(Usuario, id=access_token.user_id)

    # 3) Serializar y devolver
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
        401: "Credenciales inválidas",
        404: "Aplicación OAuth2 no encontrada"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    # 1) Validar datos de entrada
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    # 2) Autenticar con Django
    user = authenticate(username=username, password=password)
    if user is None:
        return Response({"error": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

    # 3) Recuperar la aplicación OAuth2 o 404
    app = get_object_or_404(Application, name="BookRoomAPI")

    # 4) Recuperar o crear token vigente
    token = AccessToken.objects.filter(
        user=user,
        application=app,
        expires__gt=timezone.now()
    ).first()
    if not token:
        token = AccessToken.objects.create(
            user=user,
            token=generate_token(),
            application=app,
            expires=timezone.now() + timedelta(hours=10),
            scope='read write'
        )

    # 5) Devolver token y datos del usuario
    return Response({
        "access_token": token.token,
        "user": UsuarioLoginResponseSerializer(user).data
    }, status=status.HTTP_200_OK)


# 4) LOGOUT DE USUARIO
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    operation_summary="Logout de usuario",
    operation_description="Elimina el token OAuth2 actual y cierra la sesión.",
    responses={
        200: openapi.Response(description="Sesión cerrada correctamente"),
        401: openapi.Response(description="Token inválido o expirado")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_usuario(request):
    # Si no viene autenticación por token, devolvemos 401
    if not getattr(request, 'auth', None):
        return Response({"error": "Token no válido o expirado."},
                        status=status.HTTP_401_UNAUTHORIZED)

    # Borrar el token OAuth2
    request.auth.delete()
    return Response({"mensaje": "Sesión cerrada correctamente."},
                    status=status.HTTP_200_OK)

class MensajesRelatoList(generics.ListAPIView):
    """
    Lista paginada de mensajes de un relato concreto.
    Sólo usuarios autenticados pueden ver el historial.
    """
    serializer_class = MensajeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        relato_id = self.kwargs['relato_id']
        # 1) Obtener el relato o 404
        relato = get_object_or_404(Relato, id=relato_id)

        # 2) Validar que el usuario es uno de los autores (colaboradores)
        if not relato.autores.filter(id=self.request.user.id).exists():
            raise PermissionDenied("No tienes permiso para ver los mensajes de este relato.")

        # 3) Devolver los mensajes ordenados por fecha
        return Mensaje.objects.filter(relato=relato).order_by('fecha_envio')