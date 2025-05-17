from rest_framework import  status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema

from BookRoomAPI.models import *
from BookRoomAPI.serializers import *
from BookRoomAPI.utils import *
#============================================================================================
#ESTADISTICAS--------------------------------------------------------------------------------------
#============================================================================================
@swagger_auto_schema(
    method='get',
    tags=["Estadisticas"],
    operation_summary="Obtener estadísticas de un relato",
    responses={200: EstadisticaSerializer()}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_estadisticas_relato(request, relato_id):
    # 1) Intentar recuperar el relato
    try:
        relato = Relato.objects.get(id=relato_id)
    except Relato.DoesNotExist:
        return Response(
            {"error": "Relato no existe."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Intentar acceder a sus estadísticas
    try:
        estadisticas = relato.estadisticas
    except Estadistica.DoesNotExist:
        return Response(
            {"error": "Sin estadísticas."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 3) Serializar y devolver
    serializer = EstadisticaSerializer(estadisticas)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    tags=["Estadisticas"],
    operation_summary="Listar estadísticas de todos los relatos",
    responses={200: EstadisticaSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_listar_estadisticas(request):
    # 1) Recuperar todas las estadísticas de los relatos publicados, ordenadas por promedio de votos y limitadas a 10
    estadisticas = (
    Estadistica.objects
    .select_related('relato')
    .filter(relato__estado='PUBLICADO')
    .order_by('-promedio_votos')
    )[:10]

    # 2) Serializar y devolver
    serializer = EstadisticaSerializer(estadisticas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def ranking_usuarios(request):
    filtro = request.GET.get('filtro', 'relatos')
    map_ord = {
        'relatos': '-total_relatos_publicados',
        'votos': '-total_votos_recibidos',
        'palabras': '-total_palabras_escritas',
    }
    ordering = map_ord.get(filtro, '-total_relatos_publicados')
    usuarios = Usuario.objects.order_by(ordering)[:10]
    serializer = UsuarioRankingSerializer(usuarios, many=True)
    return Response(serializer.data)
