from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from rest_framework.permissions import IsAuthenticated
from .permissions import EsCliente
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Usuario, PerfilCliente
from .serializers import *

# Create your views here.
def home(request):
    return HttpResponse("¡Bienvenido a The Book Room API!")

##REGISTRO----------------------------------------------------------------------------------------
class RegistrarUsuarioAPIView(generics.CreateAPIView):
    serializer_class = UsuarioSerializerRegistro
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = Usuario.objects.create_user(
            username=serializer.validated_data["username"],
            email=serializer.validated_data.get("email", ""),
            password=serializer.validated_data["password1"],
            rol=Usuario.CLIENTE
        )

        PerfilCliente.objects.create(usuario=user)

        try:
            grupo = Group.objects.get(name="Clientes")
            grupo.user_set.add(user)
        except Group.DoesNotExist:
            pass

        # Crear token OAuth2
        try:
            app = Application.objects.get(name="Angular App")
        except Application.DoesNotExist:
            return Response({"error": "Aplicación OAuth2 no encontrada."}, status=500)

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
        }, status=201)
    
#obtener_usuario_por_token-----------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='get',
    operation_summary="Obtener usuario por token",
    operation_description="Devuelve la información del usuario asociado a un token OAuth2 específico.",
    responses={
        200: openapi.Response(description="Usuario encontrado y serializado correctamente"),
        404: openapi.Response(description="Token o usuario no encontrado")
    }
)
@api_view(['GET'])
def obtener_usuario_por_token(request, token):
    try:
        access_token = AccessToken.objects.get(token=token)
        usuario = Usuario.objects.get(id=access_token.user_id)
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)
    except AccessToken.DoesNotExist:
        return Response({"error": "Token no válido."}, status=404)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado."}, status=404)
    
#login_usuario-----------------------------------------------------------------------------------------    
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['username', 'password'],
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description="Nombre de usuario"),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description="Contraseña"),
        },
    ),
    operation_summary="Login de usuario",
    operation_description="Autentica a un usuario con username y password y devuelve un token OAuth2",
    responses={
        200: openapi.Response(description="Token generado correctamente"),
        400: openapi.Response(description="Credenciales inválidas"),
        500: openapi.Response(description="Error del servidor")
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({"error": "Credenciales inválidas."}, status=400)

    try:
        app = Application.objects.get(name="Angular App")
    except Application.DoesNotExist:
        return Response({"error": "Aplicación OAuth2 no encontrada."}, status=500)

    # Buscar token existente que no haya expirado
    token = AccessToken.objects.filter(
        user=user,
        application=app,
        expires__gt=timezone.now()
    ).first()

    #Si no existe token valido, generarlo
    if not token:
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
    })

#logout_usuario-----------------------------------------------------------------------------------------   
@swagger_auto_schema(
    method='post',
    operation_summary="Logout de usuario",
    operation_description="Cierra la sesión del usuario autenticado eliminando el token actual.",
    responses={
        200: openapi.Response(description="Sesión cerrada correctamente"),
        401: openapi.Response(description="No autenticado o token inválido")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_usuario(request):
    if request.auth:
        request.auth.delete() 
    return Response({"mensaje": "Sesión cerrada correctamente."})


#SESION----------------------------------------------------------------------------------------
##PERFIL-----------------------------------------------------------------------------------------   
@swagger_auto_schema(
    method='get',
    operation_summary="Obtener perfil del usuario autenticado",
    operation_description="Devuelve los datos del usuario actualmente autenticado, incluyendo su perfil cliente.",
    responses={
        200: openapi.Response(description="Perfil cargado correctamente"),
        401: openapi.Response(description="Token no enviado o inválido")
    }
)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def obtener_perfil(request):
    user = request.user

    try:
        perfil = user.perfil
    except PerfilCliente.DoesNotExist:
        return Response({'error': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UsuarioConPerfilSerializer(user)
        return Response(serializer.data)

    if request.method == 'PATCH':
        serializer = PerfilClienteUpdateSerializer(perfil, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'mensaje': 'Perfil actualizado correctamente'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)