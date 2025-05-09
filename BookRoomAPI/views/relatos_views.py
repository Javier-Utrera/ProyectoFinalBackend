from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Count, F
from django.db import transaction

from BookRoomAPI.models import Relato, ParticipacionRelato, Estadistica
from BookRoomAPI.serializers import (
    RelatoSerializer,
    RelatoCreateSerializer,
    RelatoUpdateSerializer,
    MiFragmentoSerializer
)
from BookRoomAPI.utils import api_errores, obtener_relato_de_usuario, actualizar_estadisticas


#============================================================================================
# RELATOS
#============================================================================================

@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Listar relatos publicados",
    operation_description="Devuelve una lista de todos los relatos en estado 'PUBLICADO'. No requiere autenticación.",
    responses={200: "Lista de relatos publicados devuelta correctamente"}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_listar_relatos_publicados(request):
    # 1) Obtener todos los relatos con estado 'PUBLICADO', ordenados por fecha de creación desc.
    relatos = Relato.objects.filter(estado='PUBLICADO').order_by('-fecha_creacion')
    # 2) Serializar la lista de relatos.
    serializer = RelatoSerializer(relatos, many=True)
    # 3) Devolver la respuesta con los datos serializados.
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Listar relatos del usuario autenticado",
    operation_description="Devuelve todos los relatos en los que participa el usuario autenticado.",
    responses={200: "Lista de relatos devuelta correctamente", 401: "Token inválido o no enviado"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listar_relatos(request):
    # 1) Filtrar relatos donde el usuario actual es autor, ordenados desc.
    relatos = Relato.objects.filter(autores=request.user).order_by('-fecha_creacion')
    # 2) Serializar la lista de relatos.
    serializer = RelatoSerializer(relatos, many=True)
    # 3) Devolver la respuesta.
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Obtener un relato del usuario autenticado",
    operation_description="""
        Devuelve los datos de un relato específico en el que el usuario participa.
        Si no tiene acceso, devuelve 404.
    """,
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    responses={200: RelatoSerializer, 404: "Error de acceso"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_obtener_relato(request, relato_id):
    # 1) Intentar recuperar el relato al que el usuario tiene acceso mediante helper.
    relato = obtener_relato_de_usuario(relato_id, request.user)
    # 2) Si no existe o no pertenece al usuario, devolver 404.
    if not relato:
        return Response({"error": "No tienes acceso a este relato."}, status=status.HTTP_404_NOT_FOUND)
    # 3) Serializar y devolver el relato.
    serializer = RelatoSerializer(relato)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Ver relato publicado (público)",
    operation_description="Devuelve un relato si está en estado PUBLICADO. Público.",
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    responses={200: RelatoSerializer, 404: "No publicado o no existe"}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_ver_relato_publicado(request, relato_id):
    try:
        # 1) Intentar recuperar el relato publicado.
        relato = Relato.objects.get(id=relato_id, estado='PUBLICADO')
    except Relato.DoesNotExist:
        # 2) Si no existe o no está publicado, devolver 404.
        return Response({"error": "Este relato no está publicado o no existe."}, status=status.HTTP_404_NOT_FOUND)
    # 3) Serializar y devolver.
    serializer = RelatoSerializer(relato)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Crear nuevo relato",
    operation_description="""
        Crea un relato, añade al creador como participante, inicializa estadísticas
        y actualiza estado/estadísticas.
    """,
    request_body=RelatoCreateSerializer,
    responses={201: "Relato creado correctamente", 400: "Errores de validación"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_crear_relato(request):
    # 1) Validar datos de entrada con el serializer.
    serializer = RelatoCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return api_errores(serializer)

    # 2) Ejecutar en transacción para mantener consistencia.
    with transaction.atomic():
        # 2.1) Crear el relato.
        relato = serializer.save()
        # 2.2) Inicializar sus estadísticas.
        Estadistica.objects.create(relato=relato)
        # 2.3) Añadir al usuario actual como primer colaborador.
        ParticipacionRelato.objects.create(usuario=request.user, relato=relato, orden=1)
        # 2.4) Verificar si el relato pasa a EN_PROCESO.
        relato.comprobar_estado_y_actualizar()
        # 2.5) Calcular valores reales en estadísticas.
        actualizar_estadisticas(relato)

    # 3) Devolver confirmación.
    return Response({"mensaje": "Relato creado correctamente."}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Marcar relato como listo para publicar",
    operation_description="""
        Marca la participación del usuario como lista y publica si todos están listos.
    """,
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    responses={200: "Marcado correctamente", 403: "Sin permisos", 404: "No colaborador"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_marcar_relato_listo(request, relato_id):
    # 1) Verificar que el usuario es colaborador del relato.
    try:
        relato = Relato.objects.get(id=relato_id, autores=request.user)
    except Relato.DoesNotExist:
        return Response({"error": "No tienes acceso a este relato."}, status=status.HTTP_403_FORBIDDEN)

    # 2) Recuperar su registro de participación.
    try:
        participacion = ParticipacionRelato.objects.get(usuario=request.user, relato=relato)
    except ParticipacionRelato.DoesNotExist:
        return Response({"error": "No estás registrado como colaborador."}, status=status.HTTP_404_NOT_FOUND)

    # 3) Si ya estaba marcado, devolver OK sin cambios.
    if participacion.listo_para_publicar:
        return Response({"mensaje": "Ya marcado como listo."}, status=status.HTTP_200_OK)

    # 4) Marcar como listo y guardar.
    participacion.listo_para_publicar = True
    participacion.save()

    # 5) Si todos los colaboradores están listos, publicar relato.
    relato.comprobar_si_publicar()

    # 6) Responder.
    return Response({"mensaje": "Has marcado el relato como listo."})


@swagger_auto_schema(
    methods=['put', 'patch'],
    tags=["Relatos"],
    operation_summary="Editar un relato existente",
    operation_description="Permite modificar solo si eres colaborador.",
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    request_body=RelatoUpdateSerializer,
    responses={200: "Editado correctamente", 400: "Errores", 403: "Sin permisos"}
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_editar_relato(request, relato_id):
    # 1) Recuperar relato solo si el usuario es colaborador.
    relato = obtener_relato_de_usuario(relato_id, request.user)
    if not relato:
        return Response({"error": "Sin permisos para editar."}, status=status.HTTP_403_FORBIDDEN)
    # 2) Aplicar cambios con el serializer.
    serializer = RelatoUpdateSerializer(instance=relato, data=request.data, partial=True)
    return api_errores(serializer, "Relato editado correctamente", status_success=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    tags=["Relatos"],
    operation_summary="Eliminar un relato",
    operation_description="Solo si eres único colaborador.",
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    responses={200: "Eliminado correctamente", 403: "Sin permisos"}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_relato(request, relato_id):
    # 1) Recuperar relato con helper.
    relato = obtener_relato_de_usuario(relato_id, request.user)
    # 2) Verificar que solo tiene un colaborador (el usuario).
    if not relato or relato.autores.count() > 1:
        return Response({"error": "No puedes eliminar este relato."}, status=status.HTTP_403_FORBIDDEN)
    # 3) Eliminar y responder.
    relato.delete()
    return Response({"mensaje": "Relato eliminado correctamente."})


@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Listar relatos abiertos",
    operation_description="Relatos en CREACION con plazas libres. Público.",
    responses={200: "Listado devuelto correctamente"}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_relatos_abiertos(request):
    # 1) Anotar conteo de autores y filtrar CREACION vs num_escritores.
    abiertos = Relato.objects.annotate(total_autores=Count('autores')) \
                             .filter(estado='CREACION', total_autores__lt=F('num_escritores'))
    # 2) Serializar y devolver.
    return Response(RelatoSerializer(abiertos, many=True).data)


@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Unirse a un relato",
    operation_description="Permite unirse si está en CREACION y quedan plazas.",
    responses={201: "Unido correctamente", 200: "Ya participas", 400: "No admite más", 404: "No existe"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_unirse_a_relato(request, relato_id):
    # 1) Recuperar relato.
    try:
        relato = Relato.objects.get(id=relato_id)
    except Relato.DoesNotExist:
        return Response({"error": "Relato no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    # 2) Verificar estado CREACION.
    if relato.estado != 'CREACION':
        return Response({"error": "No acepta más escritores."}, status=status.HTTP_400_BAD_REQUEST)

    # 3) Si ya participas, devolver mensaje.
    if relato.autores.filter(id=request.user.id).exists():
        return Response({"mensaje": "Ya participas en este relato."})

    # 4) Si no hay plazas, error.
    if relato.autores.count() >= relato.num_escritores:
        return Response({"error": "Máximo de escritores alcanzado."}, status=status.HTTP_400_BAD_REQUEST)

    # 5) Crear participación con el siguiente orden.
    orden = relato.autores.count() + 1
    ParticipacionRelato.objects.create(usuario=request.user, relato=relato, orden=orden)

    # 6) Actualizar estado y estadísticas.
    relato.comprobar_estado_y_actualizar()
    actualizar_estadisticas(relato)

    # 7) Devolver confirmación.
    return Response({"mensaje": "Te has unido correctamente al relato."}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    methods=['get', 'put'],
    tags=["Relatos"],
    operation_summary="Obtener o actualizar mi fragmento de un relato",
    operation_description="GET devuelve fragmento; PUT actualiza solo el contenido.",
    request_body=MiFragmentoSerializer,
    responses={200: MiFragmentoSerializer, 404: "No encontrado"}
)
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def api_mi_fragmento(request, relato_id):
    # 1) Verificar acceso al relato y participación.
    try:
        relato = Relato.objects.get(id=relato_id, autores=request.user)
        participacion = ParticipacionRelato.objects.get(relato=relato, usuario=request.user)
    except (Relato.DoesNotExist, ParticipacionRelato.DoesNotExist):
        return Response({"error": "No tienes acceso a este relato."}, status=status.HTTP_404_NOT_FOUND)

    # 2) Si es GET, serializar la participación.
    if request.method == 'GET':
        return Response(MiFragmentoSerializer(participacion).data)

    # 3) Si es PUT, validar y guardar solo el fragmento.
    serializer = MiFragmentoSerializer(participacion, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_marcar_fragmento_listo(request, relato_id):
    # 1) Recuperar la participaci ón
    participacion = ParticipacionRelato.objects.get(relato_id=relato_id, usuario=request.user)
    # 2) Marcar como listo y guardar
    participacion.listo_para_publicar = True
    participacion.save()

    # 3) Si TODOS los fragmentos están listos, concatenar y publicar relato
    relato = participacion.relato
    pendientes = ParticipacionRelato.objects.filter(relato=relato, listo_para_publicar=False)
    if not pendientes.exists():
        contenido = "".join(
            p.contenido_fragmento or ""
            for p in ParticipacionRelato.objects.filter(relato=relato).order_by('orden')
        )
        relato.contenido = contenido
        relato.estado = 'PUBLICADO'
        relato.save()
        actualizar_estadisticas(relato)

    # 4) Devolver confirmación
    return Response({"mensaje": "Fragmento marcado como listo."})
