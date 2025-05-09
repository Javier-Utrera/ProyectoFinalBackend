from rest_framework import  status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema

from BookRoomAPI.models import *
from BookRoomAPI.serializers import *
from BookRoomAPI.utils import *

#============================================================================================
#VOTOS--------------------------------------------------------------------------------------
#============================================================================================

@swagger_auto_schema(
    method='post',
    tags=["Votos"],
    operation_summary="Votar un relato",
    request_body=VotoSerializer,
    responses={
        201: "Voto registrado",
        400: "Errores de validación o ya votado"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_votar_relato(request, relato_id):
    # 1) Recuperar relato publicado
    try:
        relato = Relato.objects.get(id=relato_id, estado='PUBLICADO')
    except Relato.DoesNotExist:
        return Response(
            {"error": "El relato no está publicado o no existe."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Validar entrada
    serializer = VotoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    puntuacion = serializer.validated_data['puntuacion']

    # 3) Crear o actualizar el voto
    voto, created = Voto.objects.update_or_create(
        usuario=request.user,
        relato=relato,
        defaults={'puntuacion': puntuacion}
    )
    # 4) Actualizar estadísticas del relato
    actualizar_estadisticas(relato)

    # 5) Responder con el voto (200 si se modificó, 201 si es nuevo)
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(VotoSerializer(voto).data, status=status_code)


@swagger_auto_schema(
    method='get',
    tags=["Votos"],
    operation_summary="Ver mi voto en un relato",
    responses={
        200: VotoSerializer,
        404: "No has votado este relato"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_mi_voto_relato(request, relato_id):
    try:
        voto = Voto.objects.get(relato_id=relato_id, usuario=request.user)
    except Voto.DoesNotExist:
        return Response({"error": "No has votado este relato."}, status=404)

    serializer = VotoSerializer(voto)
    return Response(serializer.data)