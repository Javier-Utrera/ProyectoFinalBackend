from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Count, F
from django.db import transaction
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from BookRoomAPI.filtros import RelatoFilter
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

class RelatosPublicadosList(generics.ListAPIView):
    """
    Listar relatos en estado PUBLICADO. Público.
    """
    queryset = Relato.objects.filter(estado='PUBLICADO')
    serializer_class = RelatoSerializer
    permission_classes = [AllowAny]

    filter_backends = [
        DjangoFilterBackend,  
        SearchFilter,         # Para ?search
        OrderingFilter,       # Para ?ordering
    ]
    filterset_class = RelatoFilter
    search_fields   = ['titulo', 'descripcion']
    ordering_fields = ['fecha_creacion', 'num_escritores', 'titulo']
    ordering        = ['-fecha_creacion']

    @swagger_auto_schema(
        operation_summary="Listar relatos publicados",
        operation_description=(
            "Listado paginado de relatos PUBLICADOS. "
            "Parámetros opcionales:\n"
            "- `search`: búsqueda global en título o descripción.\n"
            "- `titulo__icontains`, `descripcion__icontains`: búsquedas específicas.\n"
            "- `idioma`, `num_escritores`, `num_escritores__gte`, `num_escritores__lte`.\n"
            "- `fecha_desde`, `fecha_hasta`.\n"
            "- `ordering`: campos `fecha_creacion`, `num_escritores`, `titulo`.\n"
            "- `page`: número de página."
        ),
        responses={200: openapi.Response(
            description="Listado de relatos publicados",
            schema=RelatoSerializer(many=True)
        )}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MisRelatosList(generics.ListAPIView):
    """
    Listar relatos en los que participa el usuario autenticado.
    """
    serializer_class = RelatoSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]
    filterset_class = RelatoFilter
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_creacion', 'num_escritores', 'titulo']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        return Relato.objects.filter(autores=self.request.user)\
                           .order_by('-fecha_creacion')

    @swagger_auto_schema(
        operation_summary="Listar mis relatos",
        operation_description="Devuelve listado de relatos donde el usuario es autor o colaborador.",
        responses={200: openapi.Response(
            description="Listado de mis relatos",
            schema=RelatoSerializer(many=True)
        )}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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
    serializer = RelatoCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return api_errores(serializer)

    with transaction.atomic():
        # 1) Creamos el relato, guardando su contenido inicial (puede venir vacío)
        relato = serializer.save()

        # 2) Creamos las estadísticas nuevas
        Estadistica.objects.create(relato=relato)

        # 3) Creamos la participación del creador (fragmento pendiente)
        ParticipacionRelato.objects.create(
            usuario=request.user,
            relato=relato,
            orden=1,
            contenido_fragmento=''  # arrancamos vacío
        )

        # 4) Si ya basta con un solo autor, pasamos a EN_PROCESO
        relato.comprobar_estado_y_actualizar()

        # 5) Llenamos estadísticas reales
        actualizar_estadisticas(relato)

    return Response(
        {"mensaje": "Relato creado correctamente."},
        status=status.HTTP_201_CREATED
    )


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


class RelatosDisponiblesList(generics.ListAPIView):
    """
    Listar relatos en CREACION con plazas libres. Requiere autenticación.
    """
    queryset = Relato.objects.annotate(
        total_autores=Count('autores')
    ).filter(
        estado='CREACION',
        total_autores__lt=F('num_escritores')
    ).order_by('-fecha_creacion')
    serializer_class = RelatoSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]
    filterset_class = RelatoFilter
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_creacion', 'num_escritores', 'titulo']
    ordering = ['-fecha_creacion']

    @swagger_auto_schema(
        operation_summary="Listar relatos disponibles",
        operation_description="Devuelve listado de relatos en creación con plazas libres para el usuario autenticado.",
        responses={200: openapi.Response(
            description="Listado de relatos disponibles",
            schema=RelatoSerializer(many=True)
        )}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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
    # 1) Recuperar la participación del usuario
    try:
        participacion = ParticipacionRelato.objects.get(
            relato_id=relato_id,
            usuario=request.user
        )
    except ParticipacionRelato.DoesNotExist:
        return Response(
            {"error": "No estás participando en este relato."},
            status=status.HTTP_404_NOT_FOUND
        )


   # 2) Si aún no estaba listo, contamos y sumamos palabras escritas
    if not participacion.listo_para_publicar:
        texto = participacion.contenido_fragmento or ""
        palabras = len(texto.split())
        # Sumamos de golpe esas palabras al total del usuario
        request.user.total_palabras_escritas = F('total_palabras_escritas') + palabras
        request.user.save(update_fields=['total_palabras_escritas'])
        # ahora sí marcamos como listo
        participacion.listo_para_publicar = True
        participacion.save()

    # 3) Si TODOS los autores han marcado su fragmento, publicamos
    relato = participacion.relato
    pendientes = ParticipacionRelato.objects.filter(
        relato=relato,
        listo_para_publicar=False
    )
    if not pendientes.exists():
        # 3.1) Tomamos el contenido inicial (campo relato.contenido)…
        inicial = relato.contenido or ""
        # 3.2) …y concatenamos todos los fragmentos por orden
        fragments = ParticipacionRelato.objects.filter(relato=relato).order_by('orden')
        relato.contenido = inicial + "".join(p.contenido_fragmento or "" for p in fragments)
        relato.estado = 'PUBLICADO'
        relato.save()

        # 3.3) Actualizar las estadísticas del relato
        actualizar_estadisticas(relato)

        # 3.4) Incrementar el contador de “relatos publicados” de cada autor
        for autor in relato.autores.all():
            autor.total_relatos_publicados = F('total_relatos_publicados') + 1
            autor.save(update_fields=['total_relatos_publicados'])

    # 4) Responder al cliente
    return Response({"mensaje": "Fragmento marcado como listo."})
