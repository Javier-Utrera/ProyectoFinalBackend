from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q

from BookRoomAPI.models import *
from BookRoomAPI.serializers import *
from BookRoomAPI.utils import *

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