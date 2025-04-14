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


from .models import Usuario, PerfilCliente
from .serializers import UsuarioSerializerRegistro, UsuarioSerializer
# Create your views here.
def home(request):
    return HttpResponse("¡Bienvenido a The Book Room API!")


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

        # Crear token OAuth2 automáticamente
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

    #Si no existe token válido, generarlo
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_usuario(request):
    if request.auth:
        request.auth.delete() 
    return Response({"mensaje": "Sesión cerrada correctamente."})