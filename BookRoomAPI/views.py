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
from .serializerSwagger import *
from .utils import *
from .permissions import EsCliente

# Create your views here.
def home(request):
    return HttpResponse("¡Bienvenido a The Book Room API!")

#============================================================================================
#AUTENTICACION Y REGISTRO--------------------------------------------------------------------
#============================================================================================

#REGISTRAR USUARIO----------------------------------------------------------
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
    serializer = UsuarioSerializerRegistro(data=request.data)
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
    
#DEVOLVER TOKEN--------------------------------------------------------------
@swagger_auto_schema(
    method='get',
    tags=["Registro y login"],
    operation_summary="Obtener usuario por token",
    operation_description="Devuelve la información del usuario asociado a un token OAuth2 proporcionado en la URL.",
    manual_parameters=[
        openapi.Parameter(
            'token',
            openapi.IN_PATH,
            description="Token OAuth2 del usuario",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(description="Usuario encontrado y serializado correctamente"),
        404: openapi.Response(description="Token o usuario no encontrado"),
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
    
#LOGIN USUARIO--------------------------------------------------------------- 
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    request_body=LoginSerializer,
    operation_summary="Login de usuario",
    operation_description="Autentica a un usuario y devuelve un token OAuth2 si las credenciales son correctas.",
    responses={
        200: "Logeo correcto, token generado y datos del usuario recibido",
        400: "Credenciales inválidas",
        500: "Error del servidor"
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
        "access_token": token.token,
        "user": UsuarioLoginResponseSerializer(user).data
    })

#LOGOUT USUARIO---------------------------------------------------------------
@swagger_auto_schema(
    method='post',
    tags=["Registro y login"],
    operation_summary="Logout de usuario",
    operation_description="Elimina el token OAuth2 actual del usuario, cerrando su sesión.",
    responses={
        200: "Sesión cerrada correctamente",
        401: "Token inválido o no enviado"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_usuario(request):
    if request.auth:
        request.auth.delete()
    return Response({"mensaje": "Sesión cerrada correctamente."})

#============================================================================================
#PERFIL--------------------------------------------------------------------------------------
#============================================================================================

@swagger_auto_schema(
    method='get',
    tags=["Perfil"],
    operation_summary="Obtener perfil del usuario",
    operation_description="Devuelve los datos del usuario actualmente autenticado.",
    responses={
        200: "Perfil cargado correctamente",
        401: "Token no enviado o inválido"
    }
)
@swagger_auto_schema(
    method='patch',
    tags=["Perfil"],
    operation_summary="Editar perfil del usuario",
    operation_description="""
        Permite modificar los campos del perfil del usuario autenticado:
        - Biografía (máx. 500 caracteres)
        - Fecha de nacimiento (no puede ser futura)
        - País, ciudad (solo letras y espacios)
        - Géneros favoritos (texto separado por comas)
    """,
    request_body=UsuarioUpdateSerializer,
    responses={
        200: "Perfil actualizado correctamente",
        400: "Errores de validación",
        401: "Token no enviado o inválido"
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
#RELATOS-------------------------------------------------------------------------------------
#============================================================================================

#Listar relatos publicados-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Listar relatos publicados",
    operation_description="Devuelve una lista de todos los relatos en estado 'PUBLICADO'. No requiere autenticación.",
    responses={
        200: "Lista de relatos publicados devuelta correctamente"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_listar_relatos_publicados(request):
    relatos = Relato.objects.filter(estado='PUBLICADO').order_by('-fecha_creacion')
    serializer = RelatoSerializer(relatos, many=True)
    return Response(serializer.data)

#Listar relatos en los que participa el usuario atenticado-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Listar relatos del usuario autenticado",
    operation_description="Devuelve todos los relatos en los que participa el usuario autenticado.",
    responses={
        200: "Lista de relatos devuelta correctamente",
        401: "Token inválido o no enviado"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listar_relatos(request):
    relatos = Relato.objects.filter(autores=request.user).order_by('-fecha_creacion')
    serializer = RelatoSerializer(relatos, many=True)
    return Response(serializer.data)

#Obtener relato del usuario autenticado-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Obtener un relato del usuario autenticado",
    operation_description="""
        Devuelve los datos de un relato específico en el que el usuario autenticado participa.
        El relato debe estar asociado al usuario, de lo contrario se devolverá un error.
    """,
    manual_parameters=[
        openapi.Parameter(
            'relato_id',
            openapi.IN_PATH,
            description="ID del relato",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: "Relato encontrado",
        404: "Relato no encontrado o no pertenece al usuario"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_obtener_relato(request, relato_id):
    relato = obtener_relato_de_usuario(relato_id, request.user)
    if not relato:
        return Response({"error": "No tienes acceso a este relato."}, status=status.HTTP_404_NOT_FOUND)
    serializer = RelatoSerializer(relato)
    return Response(serializer.data)

#Ver relato publicado-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Ver relato publicado (público)",
    operation_description="""
        Devuelve los datos de un relato publicado si existe.  
        Este endpoint es accesible sin autenticación.
    """,
    manual_parameters=[
        openapi.Parameter(
            'relato_id',
            openapi.IN_PATH,
            description="ID del relato",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: "Relato encontrado y publicado",
        404: "El relato no está publicado o no existe"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_ver_relato_publicado(request, relato_id):
    try:
        relato = Relato.objects.get(id=relato_id, estado='PUBLICADO')
        serializer = RelatoSerializer(relato)
        return Response(serializer.data)
    except Relato.DoesNotExist:
        return Response({"error": "Este relato no está publicado o no existe."}, status=status.HTTP_404_NOT_FOUND)

#Crear relato-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Crear nuevo relato",
    operation_description="""
        Crea un nuevo relato con los datos proporcionados.  
        El usuario autenticado se convierte automáticamente en el primer participante.  
        Si el relato cumple condiciones, cambia de estado automáticamente.
    """,
    request_body=RelatoCreateSerializer,
    responses={
        201: "Relato creado correctamente",
        400: "Errores de validación"
    }
)
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

#Marcar relato como listo para publicar-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Marcar relato como listo para publicar",
    operation_description="""
        Permite que un colaborador marque su participación como lista.  
        Si todos los participantes han marcado su relato como listo, se cambia el estado a PUBLICADO automáticamente.
    """,
    manual_parameters=[
        openapi.Parameter(
            name="relato_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID del relato a marcar como listo",
            required=True
        )
    ],
    responses={
        200: "Relato marcado como listo correctamente o ya estaba marcado",
        403: "No tienes acceso al relato",
        404: "No estás registrado como colaborador del relato"
    }
)
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

#Editar relato-------------------------------------------------------------------------------------
@swagger_auto_schema(
    methods=['put', 'patch'],
    tags=["Relatos"],
    operation_summary="Editar un relato existente",
    operation_description="""
        Permite a un colaborador modificar los datos del relato.  
        Solo puede hacerlo si forma parte del relato.
    """,
    manual_parameters=[
        openapi.Parameter(
            name="relato_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID del relato a editar",
            required=True
        )
    ],
    request_body=RelatoUpdateSerializer,
    responses={
        200: "Relato editado correctamente",
        400: "Errores de validación",
        403: "No tienes permisos para editar este relato"
    }
)    
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_editar_relato(request, relato_id):
    relato = obtener_relato_de_usuario(relato_id, request.user)
    if not relato:
        return Response({"error": "No tienes permisos para editar este relato."}, status=status.HTTP_403_FORBIDDEN)
    serializer = RelatoUpdateSerializer(instance=relato, data=request.data, partial=True)
    return api_errores(serializer, "Relato editado correctamente", status_success=status.HTTP_200_OK)

#Eliminar relato-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='delete',
    tags=["Relatos"],
    operation_summary="Eliminar un relato",
    operation_description="""
        Elimina un relato si el usuario es su único colaborador.  
        No es posible eliminar relatos con múltiples autores.
    """,
    manual_parameters=[
        openapi.Parameter(
            name="relato_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID del relato a eliminar",
            required=True
        )
    ],
    responses={
        200: "Relato eliminado correctamente",
        403: "No tienes permisos o hay múltiples colaboradores"
    }
)
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

#Listar relatos abiertos-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Listar relatos abiertos",
    operation_description="""
        Devuelve los relatos en estado **CREACION** que todavía no han alcanzado el número máximo de escritores.  
        Este endpoint es público y puede ser accedido sin autenticación.
    """,
    responses={
        200: "Listado de relatos abiertos para colaboración"
    }
)
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

#Unirse a relato-------------------------------------------------------------------------------------
@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Unirse a un relato",
    operation_description="""
        Permite que un usuario autenticado se una a un relato que aún se encuentra en estado **CREACION**  
        y no ha alcanzado el número máximo de escritores.
    """,
    responses={
        201: "Te has unido correctamente al relato",
        200: "Ya estás participando en este relato",
        400: "El relato ya no acepta más escritores o ya tiene el número máximo",
        404: "Relato no encontrado"
    }
)
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
@swagger_auto_schema(
    method='post',
    tags=["Amistades"],
    operation_summary="Enviar solicitud de amistad",
    operation_description="""
        Permite al usuario autenticado enviar una solicitud de amistad a otro usuario.
        - No se permite enviar una solicitud a uno mismo.
        - No se permite duplicar solicitudes existentes.
    """,
    request_body=SolicitudAmistadSerializer,
    responses={
        201: "Solicitud de amistad enviada",
        400: "ID no proporcionado, usuario no válido o ya existe una solicitud",
        404: "Usuario destinatario no encontrado"
    }
)
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

@swagger_auto_schema(
    method='get',
    tags=["Amistades"],
    operation_summary="Listar solicitudes de amistad recibidas",
    operation_description="""
        Devuelve una lista de solicitudes de amistad que ha recibido el usuario autenticado y que aún no ha respondido.
    """,
    responses={
        200: "Listado de solicitudes recibidas"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_solicitudes_recibidas(request):
    solicitudes = request.user.amistades_por_responder().select_related('de_usuario')
    serializer = PeticionAmistadSerializer(solicitudes, many=True)
    return Response(serializer.data)

@swagger_auto_schema(
    method='post',
    tags=["Amistades"],
    operation_summary="Aceptar solicitud de amistad",
    operation_description="""
        Permite al usuario autenticado aceptar una solicitud de amistad pendiente recibida.

        La solicitud debe estar en estado `PENDIENTE`, y solo el destinatario (a_usuario) puede aceptarla.
    """,
    responses={
        200: "Solicitud de amistad aceptada correctamente",
        400: "La solicitud ya fue respondida o no es válida",
        403: "No tienes permisos para aceptar esta solicitud",
        404: "Solicitud no encontrada"
    }
)
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

@swagger_auto_schema(
    method='get',
    tags=["Amistades"],
    operation_summary="Listar amigos del usuario",
    operation_description="""
        Devuelve una lista de todos los amigos del usuario autenticado.
        
        La relación de amistad debe estar en estado `ACEPTADA`.
    """,
    responses={
        200: "Lista de amigos cargada correctamente",
        401: "Token no enviado o inválido"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listar_amigos(request):
    amigos = request.user.amigos()
    serializer = UsuarioAmigoSerializer(amigos, many=True)
    return Response(serializer.data)

@swagger_auto_schema(
    method='get',
    tags=["Amistades"],
    operation_summary="Listar solicitudes de amistad enviadas",
    operation_description="""
        Devuelve todas las solicitudes de amistad que el usuario autenticado ha enviado y que aún están pendientes.
    """,
    responses={
        200: "Solicitudes de amistad enviadas listadas correctamente",
        401: "Token no enviado o inválido"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_solicitudes_enviadas(request):
    solicitudes = request.user.amistades_pendientes().select_related('a_usuario')
    serializer = PeticionAmistadSerializer(solicitudes, many=True)
    return Response(serializer.data)

@swagger_auto_schema(
    method='post',
    tags=["Amistades"],
    operation_summary="Bloquear usuario",
    operation_description="""
        Bloquea al usuario que envió la solicitud de amistad.  
        - Elimina la solicitud original.  
        - Crea una relación de tipo 'BLOQUEADA' en la base de datos.  
        - Si ya estaba bloqueado, devuelve un mensaje informativo.
    """,
    responses={
        200: "Usuario bloqueado correctamente o ya estaba bloqueado",
        403: "No tienes permisos para bloquear esta solicitud",
        404: "Solicitud no encontrada",
        401: "Token no enviado o inválido"
    }
)
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

@swagger_auto_schema(
    method='get',
    tags=["Amistades"],
    operation_summary="Listar usuarios bloqueados",
    operation_description="""
        Devuelve un listado de todos los usuarios que el usuario autenticado ha bloqueado.  
        Utiliza relaciones `PeticionAmistad` con estado **'BLOQUEADA'**.
    """,
    responses={
        200: "Lista de usuarios bloqueados devuelta correctamente",
        401: "Token no enviado o inválido"
    }
)
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

@swagger_auto_schema(
    method='delete',
    tags=["Amistades"],
    operation_summary="Desbloquear usuario",
    operation_description="""
        Elimina la relación de tipo 'BLOQUEADA' entre el usuario autenticado y el usuario con `usuario_id`.  
        Esto permite que puedan volver a enviarse solicitudes de amistad.
    """,
    responses={
        200: "Usuario desbloqueado correctamente",
        404: "No se ha encontrado un bloqueo hacia ese usuario"
    }
)
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

@swagger_auto_schema(
    method='delete',
    tags=["Amistades"],
    operation_summary="Eliminar amistad",
    operation_description="""
        Elimina la relación de amistad con el usuario indicado por `usuario_id`.  
        Esta acción es irreversible y elimina la solicitud aceptada entre ambos usuarios.
    """,
    responses={
        200: "Amistad eliminada correctamente",
        404: "No existe una relación de amistad con ese usuario"
    }
)
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
@swagger_auto_schema(
    method='get',
    tags=["Amistades"],
    operation_summary="Buscar usuarios",
    operation_description="""
        Busca usuarios por nombre de usuario `username` a partir del parámetro `q`.  
        - La búsqueda requiere al menos 3 caracteres.  
        - No devuelve al usuario autenticado.  
        - Devuelve información básica del usuario.
    """,
    manual_parameters=[
        openapi.Parameter(
            name='q',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            required=True,
            description='Texto a buscar (mínimo 3 caracteres)'
        )
    ],
    responses={
        200: "Listado de usuarios encontrados",
    }
)
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