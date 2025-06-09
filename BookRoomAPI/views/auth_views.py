# views/auth.py

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token

from datetime import timedelta
from django.utils import timezone

from django.contrib.auth import authenticate

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Suscripcion, Usuario, Mensaje, Relato
from ..serializers import (
    UsuarioSerializerRegistro, UsuarioSerializer,
    UsuarioLoginResponseSerializer, LoginSerializer, MensajeSerializer
)

# 1) REGISTRAR USUARIO
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    request_body=UsuarioSerializerRegistro,
    responses={
        201: openapi.Response(
            description="Usuario registrado correctamente",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'mensaje': openapi.Schema(type=openapi.TYPE_STRING),
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'tipo': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
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

    Suscripcion.objects.create(
        usuario=user,
        tipo='FREE',
        activa=True,
        fecha_inicio=timezone.now(),
        fecha_fin=None
    )

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
            "mensaje": "Usuario registrado correctamente. Bienvenido/a " + f"{user.username}",
            "access_token": token.token,
            "user": UsuarioSerializer(user).data,
            "tipo": "success"
        },
        status=status.HTTP_201_CREATED
    )


# 2) OBTENER USUARIO POR TOKEN
@swagger_auto_schema(
    method='get',
    tags=["Registro y login"],
    manual_parameters=[openapi.Parameter('token', openapi.IN_PATH, type=openapi.TYPE_STRING)],
    responses={
        200: openapi.Response(description="Usuario encontrado", schema=UsuarioSerializer()),
        401: "Token no válido o expirado",
        404: "Usuario no encontrado"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_usuario_por_token(request, token):
    access_token = AccessToken.objects.filter(token=token).first()
    if not access_token or access_token.expires <= timezone.now():
        return Response(
            {"error": "Token no válido o expirado."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    usuario = get_object_or_404(Usuario, id=access_token.user_id)
    return Response(UsuarioSerializer(usuario).data, status=status.HTTP_200_OK)


# 3) LOGIN DE USUARIO
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    request_body=LoginSerializer,
    responses={
        200: openapi.Response(
            description="Login correcto",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'mensaje': openapi.Schema(type=openapi.TYPE_STRING),
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'tipo': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        401: "Credenciales inválidas",
        404: "Aplicación OAuth2 no encontrada"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({"error": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

    app = get_object_or_404(Application, name="BookRoomAPI")
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

    return Response({
        "mensaje": "Login correcto. Bienvenido/a." + f" {user.username}",
        "access_token": token.token,
        "user": UsuarioLoginResponseSerializer(user).data,
        "tipo": "success"
    }, status=status.HTTP_200_OK)


# 4) LOGOUT DE USUARIO
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    responses={
        200: openapi.Response(
            description="Sesión cerrada correctamente",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'mensaje': openapi.Schema(type=openapi.TYPE_STRING),
                    'tipo': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        401: "Token inválido o expirado"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_usuario(request):
    if not getattr(request, 'auth', None):
        return Response({"error": "Token no válido o expirado."},
                        status=status.HTTP_401_UNAUTHORIZED)
    request.auth.delete()
    return Response({"mensaje": "Sesión cerrada correctamente.", "tipo": "success"},
                    status=status.HTTP_200_OK)


# 5) Mensajes de un relato (no devuelve pop-ups)
class MensajesRelatoList(generics.ListAPIView):
    serializer_class    = MensajeSerializer
    permission_classes  = [permissions.IsAuthenticated]
    pagination_class    = None

    def get_queryset(self):
        relato_id = self.kwargs['relato_id']
        relato = get_object_or_404(Relato, id=relato_id)
        if not relato.autores.filter(id=self.request.user.id).exists():
            raise PermissionDenied("No tienes permiso para ver los mensajes de este relato.")
        return Mensaje.objects.filter(relato=relato).order_by('fecha_envio')
