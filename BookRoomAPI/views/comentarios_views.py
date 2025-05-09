from rest_framework import  status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from BookRoomAPI.models import *
from BookRoomAPI.serializers import *
from BookRoomAPI.utils import *
#============================================================================================
# COMENTARIOS
#============================================================================================

@swagger_auto_schema(
    method='get',
    tags=["Comentarios"],
    operation_summary="Listar comentarios de un relato",
    responses={200: ComentarioSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_listar_comentarios_relato(request, relato_id):
    # 1) Comprobar que el relato existe y está publicado
    try:
        relato = Relato.objects.get(id=relato_id, estado='PUBLICADO')
    except Relato.DoesNotExist:
        return Response(
            {"error": "El relato no está publicado o no existe."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Recuperar y ordenar los comentarios
    comentarios = Comentario.objects.filter(relato=relato).order_by('-fecha')
    # 3) Serializar y devolver la lista
    serializer = ComentarioSerializer(comentarios, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    tags=["Comentarios"],
    operation_summary="Añadir comentario a un relato",
    request_body=ComentarioSerializer,
    responses={201: ComentarioSerializer, 400: "Errores de validación"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_crear_comentario_relato(request, relato_id):
    # 1) Comprobar que el relato existe y está publicado
    try:
        relato = Relato.objects.get(id=relato_id, estado='PUBLICADO')
    except Relato.DoesNotExist:
        return Response(
            {"error": "El relato no está publicado o no existe."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Verificar que el usuario aún no ha comentado
    if Comentario.objects.filter(relato=relato, usuario=request.user).exists():
        return Response(
            {"error": "Ya has comentado este relato. Edita o elimina tu comentario."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3) Validar y guardar el nuevo comentario
    serializer = ComentarioSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(usuario=request.user, relato=relato)

    # 4) Actualizar las estadísticas del relato
    actualizar_estadisticas(relato)

    # 5) Devolver el comentario creado
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    methods=['patch'],
    tags=["Comentarios"],
    operation_summary="Editar mi comentario en un relato",
    request_body=ComentarioSerializer,
    responses={200: ComentarioSerializer, 400: "Validación", 403: "Sin permiso", 404: "No encontrado"}
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def api_editar_comentario_relato(request, relato_id, comentario_id):
    # 1) Comprobar relato publicado
    try:
        Relato.objects.get(id=relato_id, estado='PUBLICADO')
    except Relato.DoesNotExist:
        return Response(
            {"error": "El relato no está publicado o no existe."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Recuperar el comentario
    try:
        comentario = Comentario.objects.get(id=comentario_id, relato_id=relato_id)
    except Comentario.DoesNotExist:
        return Response(
            {"error": "Comentario no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 3) Comprobar que es del usuario
    if comentario.usuario != request.user:
        return Response(
            {"error": "No tienes permiso para editar este comentario."},
            status=status.HTTP_403_FORBIDDEN
        )

    # 4) Validar y actualizar el comentario
    serializer = ComentarioSerializer(comentario, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # 5) Actualizar estadísticas y devolver el comentario
    actualizar_estadisticas(comentario.relato)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    tags=["Comentarios"],
    operation_summary="Eliminar mi comentario en un relato",
    responses={200: "Comentario eliminado", 403: "Sin permiso", 404: "No encontrado"}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_borrar_comentario_relato(request, relato_id, comentario_id):
    # 1) Comprobar relato publicado
    try:
        Relato.objects.get(id=relato_id, estado='PUBLICADO')
    except Relato.DoesNotExist:
        return Response(
            {"error": "El relato no está publicado o no existe."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Recuperar el comentario
    try:
        comentario = Comentario.objects.get(id=comentario_id, relato_id=relato_id)
    except Comentario.DoesNotExist:
        return Response(
            {"error": "Comentario no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 3) Comprobar que es del usuario
    if comentario.usuario != request.user:
        return Response(
            {"error": "No tienes permiso para eliminar este comentario."},
            status=status.HTTP_403_FORBIDDEN
        )

    # 4) Eliminar comentario y actualizar estadísticas
    relato = comentario.relato
    comentario.delete()
    actualizar_estadisticas(relato)

    # 5) Devolver confirmación
    return Response(
        {"mensaje": "Comentario eliminado correctamente."},
        status=status.HTTP_200_OK
    )
