from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, F
from django.shortcuts import get_object_or_404

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from BookRoomAPI.filtros import RelatoFilter
from BookRoomAPI.models import Relato, ParticipacionRelato, Estadistica
from BookRoomAPI.serializers import (
    RelatoSerializer,
    RelatoCreateSerializer,
    RelatoUpdateSerializer,
    MiFragmentoSerializer
)
from BookRoomAPI.utils import api_errores, actualizar_estadisticas
from BookRoomAPI.permissions import EsPropietarioOModerador, EsModeradorAdmin


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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RelatoFilter
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_creacion', 'num_escritores', 'titulo']
    ordering = ['-fecha_creacion']

    @swagger_auto_schema(
        operation_summary="Listar relatos publicados",
        operation_description=(
            "Listado paginado de relatos PUBLICADOS.\n"
            "Parámetros opcionales: search, filtros, ordering."
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RelatoFilter
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_creacion', 'num_escritores', 'titulo']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        return Relato.objects.filter(autores=self.request.user).order_by('-fecha_creacion')

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
    operation_description="Devuelve los datos de un relato específico en el que el usuario participa. Si no tiene acceso, devuelve 404.",
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    responses={200: RelatoSerializer, 404: "Error de acceso"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_obtener_relato(request, relato_id):
    relato = get_object_or_404(Relato, pk=relato_id)
    permiso = EsPropietarioOModerador()
    if not permiso.has_object_permission(request, None, relato):
        return Response({"error": "No tienes acceso a este relato."}, status=status.HTTP_404_NOT_FOUND)
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
    relato = get_object_or_404(Relato, pk=relato_id, estado='PUBLICADO')
    serializer = RelatoSerializer(relato)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Crear nuevo relato",
    operation_description="Crea un relato, añade al creador como participante, inicializa estadísticas y actualiza estado/estadísticas.",
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
        relato = serializer.save()
        Estadistica.objects.create(relato=relato)
        ParticipacionRelato.objects.create(usuario=request.user, relato=relato, orden=1, contenido_fragmento='')
        relato.comprobar_estado_y_actualizar()
        actualizar_estadisticas(relato)
    return Response({"mensaje": "Relato creado correctamente."}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Marcar relato como listo para publicar",
    operation_description="Marca la participación del usuario como lista y publica si todos están listos.",
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    responses={200: "Marcado correctamente", 403: "Sin permisos", 404: "No colaborador"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_marcar_relato_listo(request, relato_id):
    relato = get_object_or_404(Relato, pk=relato_id)
    permiso = EsPropietarioOModerador()
    if not permiso.has_object_permission(request, None, relato):
        return Response({"error": "No tienes permisos para marcar este relato."}, status=status.HTTP_403_FORBIDDEN)
    participacion = get_object_or_404(ParticipacionRelato, usuario=request.user, relato=relato)
    if participacion.listo_para_publicar:
        return Response({"mensaje": "Ya marcado como listo."}, status=status.HTTP_200_OK)
    participacion.listo_para_publicar = True
    participacion.save()
    relato.comprobar_si_publicar()
    return Response({"mensaje": "Has marcado el relato como listo."})


@swagger_auto_schema(
    methods=['put', 'patch'],
    tags=["Relatos"],
    operation_summary="Editar un relato existente",
    operation_description="Permite modificar solo si eres colaborador, moderador o admin.",
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    request_body=RelatoUpdateSerializer,
    responses={200: "Editado correctamente", 400: "Errores", 403: "Sin permisos"}
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_editar_relato(request, relato_id):
    print("Estoy en api_editar_relato")
    relato = get_object_or_404(Relato, pk=relato_id)
    permiso = EsPropietarioOModerador()
    if not permiso.has_object_permission(request, None, relato):
        print(permiso)
        return Response({"error": "Sin permisos para editar este relato."}, status=status.HTTP_403_FORBIDDEN)
    serializer = RelatoUpdateSerializer(instance=relato, data=request.data, partial=True)
    return api_errores(serializer, "Relato editado correctamente", status_success=status.HTTP_200_OK)


@swagger_auto_schema(
    methods=['put', 'patch'],
    tags=["Relatos"],
    operation_summary="Editar contenido FINAL de un relato",
    operation_description="Permite a moderadores o administradores modificar el contenido final de un relato publicado, una vez que todos los fragmentos han sido unidos.",
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    request_body=RelatoUpdateSerializer,
    responses={200: "Relato final editado correctamente", 400: "Errores de validación", 403: "Sin permisos", 404: "Relato no encontrado"}
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, EsModeradorAdmin])
def api_editar_relato_final(request, relato_id):
    relato = get_object_or_404(Relato, pk=relato_id)
    serializer = RelatoUpdateSerializer(instance=relato, data=request.data, partial=True)
    return api_errores(serializer, "Relato final editado correctamente", status_success=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    tags=["Relatos"],
    operation_summary="Eliminar un relato",
    operation_description="Permite eliminar un relato si eres colaborador único, moderador o admin.",
    manual_parameters=[openapi.Parameter('relato_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)],
    responses={200: "Eliminado correctamente", 403: "Sin permisos", 404: "Relato no encontrado"}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_relato(request, relato_id):
    relato = get_object_or_404(Relato, pk=relato_id)
    permiso = EsPropietarioOModerador()
    if not permiso.has_object_permission(request, None, relato):
        return Response({"error": "Sin permisos para eliminar este relato."}, status=status.HTTP_403_FORBIDDEN)
    relato.delete()
    return Response({"mensaje": "Relato eliminado correctamente."})


class RelatosDisponiblesList(generics.ListAPIView):
    """
    Listar relatos en CREACION con plazas libres. Requiere autenticación.
    """
    serializer_class = RelatoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RelatoFilter
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_creacion', 'num_escritores', 'titulo']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        return (
            Relato.objects
                  .annotate(total_autores=Count('autores'))
                  .filter(estado='CREACION', total_autores__lt=F('num_escritores'))
                  .order_by('-fecha_creacion')
        )

    @swagger_auto_schema(
        operation_summary="Listar relatos disponibles",
        operation_description="Devuelve listado de relatos en creación con plazas libres.",
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
    relato = get_object_or_404(Relato, pk=relato_id)
    if relato.estado != 'CREACION':
        return Response({"error": "No acepta más escritores."}, status=status.HTTP_400_BAD_REQUEST)
    if relato.autores.filter(pk=request.user.pk).exists():
        return Response({"mensaje": "Ya participas en este relato."}, status=status.HTTP_200_OK)
    if relato.autores.count() >= relato.num_escritores:
        return Response({"error": "Máximo de escritores alcanzado."}, status=status.HTTP_400_BAD_REQUEST)
    orden = relato.autores.count() + 1
    ParticipacionRelato.objects.create(usuario=request.user, relato=relato, orden=orden)
    relato.comprobar_estado_y_actualizar()
    actualizar_estadisticas(relato)
    return Response({"mensaje": "Te has unido correctamente al relato."}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='get',
    tags=["Relatos"],
    operation_summary="Obtener mi fragmento de un relato",
    operation_description="Devuelve el fragmento que te corresponde.",
    responses={200: MiFragmentoSerializer(), 404: "No encontrado"}
)
@swagger_auto_schema(
    method='put',
    tags=["Relatos"],
    operation_summary="Actualizar mi fragmento de un relato",
    operation_description="Actualiza solo el contenido del fragmento.",
    request_body=MiFragmentoSerializer,
    responses={200: MiFragmentoSerializer(), 404: "No encontrado", 400: "Errores de validación"}
)
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def api_mi_fragmento(request, relato_id):
    try:
        relato = Relato.objects.get(pk=relato_id, autores=request.user)
        participacion = get_object_or_404(ParticipacionRelato, relato=relato, usuario=request.user)
    except Relato.DoesNotExist:
        return Response({"error": "No tienes acceso a este relato."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(MiFragmentoSerializer(participacion).data)

    # PUT
    serializer = MiFragmentoSerializer(participacion, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    tags=["Relatos"],
    operation_summary="Marcar fragmento como listo",
    operation_description="Marca como listo tu fragmento y publica el relato si todos están listos.",
    responses={200: "Fragmento marcado como listo", 404: "No participas en este relato"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_marcar_fragmento_listo(request, relato_id):
    participacion = get_object_or_404(ParticipacionRelato, relato_id=relato_id, usuario=request.user)
    if not participacion.listo_para_publicar:
        texto = participacion.contenido_fragmento or ""
        palabras = len(texto.split())
        request.user.total_palabras_escritas = F('total_palabras_escritas') + palabras
        request.user.save(update_fields=['total_palabras_escritas'])
        participacion.listo_para_publicar = True
        participacion.save()
    relato = participacion.relato
    if not ParticipacionRelato.objects.filter(relato=relato, listo_para_publicar=False).exists():
        inicial = relato.contenido or ""
        fragments = ParticipacionRelato.objects.filter(relato=relato).order_by('orden')
        relato.contenido = inicial + "".join(p.contenido_fragmento or "" for p in fragments)
        relato.estado = 'PUBLICADO'
        relato.save()
        actualizar_estadisticas(relato)
        for autor in relato.autores.all():
            autor.total_relatos_publicados = F('total_relatos_publicados') + 1
            autor.save(update_fields=['total_relatos_publicados'])
    return Response({"mensaje": "Fragmento marcado como listo."})


@api_view(['GET'])
@permission_classes([AllowAny])
def opciones_relato(request):
    return Response({
        'idiomas': Relato.IDIOMAS,
        'generos': Relato.GENERO
    })
