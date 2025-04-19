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

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.db.models import Count, F, Q
from .models import *
from .serializers import *
from .utils import *
from .permissions import EsCliente

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


#============================================================================================
#PERFIL-----------------------------------------------------------------------------------------
#============================================================================================

@swagger_auto_schema(
    methods=['get', 'patch'],
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

    if request.method == 'GET':
        serializer = UsuarioSerializer(user)
        return Response(serializer.data)

    if request.method == 'PATCH':
        serializer = UsuarioUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'mensaje': 'Perfil actualizado correctamente'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#============================================================================================    
#RELATOS----------------------------------------------------------------------------------------
#============================================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_listar_relatos_publicados(request):
    relatos = Relato.objects.filter(estado='PUBLICADO').order_by('-fecha_creacion')
    serializer = RelatoSerializer(relatos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listar_relatos(request):
    relatos = Relato.objects.filter(autores=request.user).order_by('-fecha_creacion')
    serializer = RelatoSerializer(relatos, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_obtener_relato(request, relato_id):
    relato = obtener_relato_de_usuario(relato_id, request.user)
    if not relato:
        return Response({"error": "No tienes acceso a este relato."}, status=status.HTTP_404_NOT_FOUND)
    serializer = RelatoSerializer(relato)
    return Response(serializer.data)

@api_view(['GET'])
def api_ver_relato_publicado(request, relato_id):
    try:
        relato = Relato.objects.get(id=relato_id, estado='PUBLICADO')
        serializer = RelatoSerializer(relato)
        return Response(serializer.data)
    except Relato.DoesNotExist:
        return Response({"error": "Este relato no está publicado o no existe."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_crear_relato(request):
    serializer = RelatoCreateSerializer(data=request.data)
    if serializer.is_valid():
        relato = serializer.save()

        # Añadir creador como primer participante
        ParticipacionRelato.objects.create(usuario=request.user, relato=relato)

        # Verificar si se puede pasar a EN_PROCESO
        relato.comprobar_estado_y_actualizar()

        return Response({"mensaje": "Relato creado correctamente."}, status=status.HTTP_201_CREATED)
    return api_errores(serializer)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_marcar_relato_listo(request, relato_id):
    try:
        relato = Relato.objects.get(id=relato_id, autores=request.user)
    except Relato.DoesNotExist:
        return Response({"error": "No tienes acceso a este relato."}, status=status.HTTP_403_FORBIDDEN)

    try:
        participacion = ParticipacionRelato.objects.get(usuario=request.user, relato=relato)
    except ParticipacionRelato.DoesNotExist:
        return Response({"error": "No estás registrado como colaborador de este relato."}, status=status.HTTP_404_NOT_FOUND)

    if participacion.listo_para_publicar:
        return Response({"mensaje": "Ya habías marcado este relato como listo."}, status=status.HTTP_200_OK)

    participacion.listo_para_publicar = True
    participacion.save()

    relato.comprobar_si_publicar()

    return Response({"mensaje": "Has marcado el relato como listo para publicar."})
    
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_editar_relato(request, relato_id):
    relato = obtener_relato_de_usuario(relato_id, request.user)
    if not relato:
        return Response({"error": "No tienes permisos para editar este relato."}, status=status.HTTP_403_FORBIDDEN)
    serializer = RelatoUpdateSerializer(instance=relato, data=request.data, partial=True)
    return api_errores(serializer, "Relato editado correctamente", status_success=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_relato(request, relato_id):
    relato = obtener_relato_de_usuario(relato_id, request.user)
    if not relato:
        return Response({"error": "No tienes permisos para eliminar este relato."}, status=status.HTTP_403_FORBIDDEN)
    if relato.autores.count() > 1:
        return Response({"error": "No puedes eliminar un relato con múltiples colaboradores."}, status=status.HTTP_403_FORBIDDEN)
    relato.delete()
    return Response({"mensaje": "Relato eliminado correctamente."}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_relatos_abiertos(request):
    # 'annotate' agrega una columna virtual llamada 'total_autores' usando COUNT sobre la relación autores
    relatos = Relato.objects.annotate(
        total_autores=Count('autores')
    ).filter(
        estado='CREACION', 
        total_autores__lt=F('num_escritores')  # 'F' permite comparar un atributo del modelo con otro atributo del modelo
    )

    # Serializamos los relatos filtrados
    serializer = RelatoSerializer(relatos, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_unirse_a_relato(request, relato_id):
    try:
        relato = Relato.objects.get(id=relato_id)
    except Relato.DoesNotExist:
        return Response({'error': 'Relato no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if relato.estado != 'CREACION':
        return Response({'error': 'Este relato ya no acepta más escritores.'}, status=status.HTTP_400_BAD_REQUEST)

    if relato.autores.filter(id=request.user.id).exists():
        return Response({'mensaje': 'Ya estás participando en este relato.'}, status=status.HTTP_200_OK)

    if relato.autores.count() >= relato.num_escritores:
        return Response({'error': 'El relato ya ha alcanzado el número máximo de escritores.'}, status=status.HTTP_400_BAD_REQUEST)

    ParticipacionRelato.objects.create(usuario=request.user, relato=relato)
    relato.comprobar_estado_y_actualizar()

    return Response({'mensaje': 'Te has unido correctamente al relato.'}, status=status.HTTP_201_CREATED)

#============================================================================================
#PETICIONES AMISTAD----------------------------------------------------------------------------------------
#============================================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_enviar_solicitud_amistad(request):
    receptor_id = request.data.get("a_usuario")

    if not receptor_id:
        return Response({"error": "Debes indicar el ID del usuario destinatario."}, status=400)

    if receptor_id == request.user.id:
        return Response({"error": "No puedes enviarte una solicitud a ti mismo."}, status=400)

    try:
        receptor = Usuario.objects.get(id=receptor_id)
    except Usuario.DoesNotExist:
        return Response({"error": "El usuario destinatario no existe."}, status=404)

    # Verifico si ya existe alguna relacion entre el que envia y el que recibe
    ya_existe = PeticionAmistad.objects.filter(
        de_usuario=request.user, a_usuario=receptor
    ).exists() or PeticionAmistad.objects.filter(
        de_usuario=receptor, a_usuario=request.user
    ).exists()

    if ya_existe:
        return Response({"error": "Ya existe una solicitud entre estos usuarios."}, status=400)

    # Creo la solicitud de amistad
    PeticionAmistad.objects.create(de_usuario=request.user, a_usuario=receptor)
    return Response({"mensaje": "Solicitud de amistad enviada."}, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_solicitudes_recibidas(request):
    solicitudes = request.user.amistades_por_responder().select_related('de_usuario')
    serializer = PeticionAmistadSerializer(solicitudes, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_aceptar_solicitud_amistad(request, solicitud_id):
    try:
        solicitud = PeticionAmistad.objects.get(id=solicitud_id)
    except PeticionAmistad.DoesNotExist:
        return Response({"error": "Solicitud no encontrada."}, status=404)

    # Solo el destinatario puede aceptarla
    if solicitud.a_usuario != request.user:
        return Response({"error": "No tienes permisos para aceptar esta solicitud."}, status=403)

    if solicitud.estado != 'PENDIENTE':
        return Response({"error": f"La solicitud ya fue {solicitud.estado.lower()}."}, status=400)

    solicitud.estado = 'ACEPTADA'
    solicitud.fecha_aceptacion = timezone.now()
    solicitud.save()

    return Response({"mensaje": "Solicitud de amistad aceptada correctamente."})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listar_amigos(request):
    amigos = request.user.amigos()
    serializer = UsuarioAmigoSerializer(amigos, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_solicitudes_enviadas(request):
    solicitudes = request.user.amistades_pendientes().select_related('a_usuario')
    serializer = PeticionAmistadSerializer(solicitudes, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_bloquear_solicitud_amistad(request, solicitud_id):
    try:
        solicitud = PeticionAmistad.objects.get(id=solicitud_id)
    except PeticionAmistad.DoesNotExist:
        return Response({"error": "Solicitud no encontrada."}, status=404)

    # Solo a quien se le envió la solicitud puede bloquearla
    if solicitud.a_usuario != request.user:
        return Response({"error": "No tienes permisos para bloquear esta solicitud."}, status=403)

    bloqueador = request.user
    bloqueado = solicitud.de_usuario

    # Elimino la solicitud de amistad porque se quedado guardado en la base de datos que la solicitud fue enviada
    # y cuando la bloqueo, reza de que la ha bloqueado el que la ha enviado, no el que la ha recibido
    solicitud.delete()

    # Verifico si ya existe un bloqueo
    ya_bloqueado = PeticionAmistad.objects.filter(
        de_usuario=bloqueador,
        a_usuario=bloqueado,
        estado='BLOQUEADA'
    ).exists()

    if ya_bloqueado:
        return Response({"mensaje": "Este usuario ya estaba bloqueado."}, status=200)

    # Creo el nuevo registro en la base de datos pero esta vez en estado BLOQUEADA directamente
    PeticionAmistad.objects.create(
        de_usuario=bloqueador,
        a_usuario=bloqueado,
        estado='BLOQUEADA'
    )

    return Response({"mensaje": "Has bloqueado al usuario correctamente."}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listar_bloqueados(request):
    solicitudes_bloqueadas = PeticionAmistad.objects.filter(
        de_usuario=request.user,
        estado='BLOQUEADA'
    ).select_related('a_usuario')

    usuarios_bloqueados = [solicitud.a_usuario for solicitud in solicitudes_bloqueadas]
    serializer = UsuarioAmigoSerializer(usuarios_bloqueados, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_desbloquear_usuario(request, usuario_id):
    try:
        solicitud = PeticionAmistad.objects.get(
            de_usuario=request.user,
            a_usuario__id=usuario_id,
            estado='BLOQUEADA'
        )
    except PeticionAmistad.DoesNotExist:
        return Response({"error": "No has bloqueado a este usuario."}, status=404)

    solicitud.delete()
    return Response({"mensaje": "Usuario desbloqueado correctamente."})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_amigo(request, usuario_id):
    try:
        solicitud = PeticionAmistad.objects.get(
            (
                Q(de_usuario=request.user, a_usuario__id=usuario_id) |
                Q(de_usuario__id=usuario_id, a_usuario=request.user)
            ),
            estado='ACEPTADA'
        )
    except PeticionAmistad.DoesNotExist:
        return Response({"error": "No tienes una amistad con ese usuario."}, status=404)

    solicitud.delete()
    return Response({"mensaje": "Amistad eliminada correctamente."})

#============================================================================================
#BUSCADOR USUARIOS----------------------------------------------------------------------------------------
#============================================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_buscar_usuarios(request):
    query = request.query_params.get('q', '').strip()

    if not query or len(query) < 3:
        return Response([])

    usuarios = Usuario.objects.filter(
        username__icontains=query
    ).exclude(id=request.user.id)

    serializer = UsuarioAmigoSerializer(usuarios, many=True)
    return Response(serializer.data)