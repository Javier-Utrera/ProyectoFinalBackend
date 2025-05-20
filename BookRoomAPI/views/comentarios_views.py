from django.shortcuts import get_object_or_404
from rest_framework import  status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import F

from BookRoomAPI.models import *
from BookRoomAPI.permissions import EsPropietarioOModerador
from BookRoomAPI.serializers import *
from BookRoomAPI.utils import *
#============================================================================================
# COMENTARIOS
#============================================================================================

@swagger_auto_schema(
    method='get',
    tags=["Comentarios"],
    operation_summary="Listar comentarios de un relato",
    operation_description="Devuelve dos listas: `amigos` y `otros`.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amigos': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        ref='#/definitions/Comentario'
                    )
                ),
                'otros': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        ref='#/definitions/Comentario'
                    )
                ),
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_listar_comentarios_relato(request, relato_id):
    # 1) Comprobar relato publicado
    try:
        relato = Relato.objects.get(id=relato_id, estado='PUBLICADO')
    except Relato.DoesNotExist:
        return Response(
            {"error": "El relato no está publicado o no existe."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Base queryset
    todos = Comentario.objects.filter(relato=relato).order_by('-fecha')

    # 3) Separar amigos y otros
    if request.user.is_authenticated:
        ids_amigos = request.user.amigos().values_list('id', flat=True)
        qs_amigos = todos.filter(usuario__in=ids_amigos)
        qs_otros  = todos.exclude(usuario__in=ids_amigos)
    else:
        qs_amigos = Comentario.objects.none()
        qs_otros  = todos

    # 4) Serializar con contexto para `mi_voto`
    serializer_amigos = ComentarioSerializer(
        qs_amigos, many=True, context={'request': request}
    )
    serializer_otros = ComentarioSerializer(
        qs_otros, many=True, context={'request': request}
    )

    # 5) Devolver ambas listas
    return Response({
        "amigos": serializer_amigos.data,
        "otros":  serializer_otros.data
    }, status=status.HTTP_200_OK)


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
    serializer = ComentarioSerializer(data=request.data,context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save(usuario=request.user, relato=relato)

    # 4) Actualizar las estadísticas del relato
    actualizar_estadisticas(relato)

    # 5) Devolver el comentario creado
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    methods=['patch'],
    tags=["Comentarios"],
    operation_summary="Editar comentario (autor, moderador o admin)",
    request_body=ComentarioSerializer,
    responses={200: ComentarioSerializer, 400: "Validación", 403: "Sin permiso", 404: "No encontrado"}
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def api_editar_comentario_relato(request, relato_id, comentario_id):
    # 1) Comprobar relato publicado
    get_object_or_404(Relato, id=relato_id, estado='PUBLICADO')

    # 2) Recuperar el comentario o 404
    comentario = get_object_or_404(Comentario, id=comentario_id, relato_id=relato_id)

    # 3) Permisos: autor, moderador o admin
    permiso = EsPropietarioOModerador()
    if not permiso.has_object_permission(request, view=None, obj=comentario):
        return Response(
            {"error": "No tienes permiso para editar este comentario."},
            status=status.HTTP_403_FORBIDDEN
        )

    # 4) Validar y guardar
    serializer = ComentarioSerializer(comentario, data=request.data, partial=True, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # 5) Actualizar estadísticas y devolver
    actualizar_estadisticas(comentario.relato)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    tags=["Comentarios"],
    operation_summary="Eliminar comentario (autor, moderador o admin)",
    responses={200: "Comentario eliminado", 403: "Sin permiso", 404: "No encontrado"}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_borrar_comentario_relato(request, relato_id, comentario_id):
    # 1) Comprobar relato publicado
    get_object_or_404(Relato, id=relato_id, estado='PUBLICADO')

    # 2) Recuperar el comentario o 404
    comentario = get_object_or_404(Comentario, id=comentario_id, relato_id=relato_id)

    # 3) Permisos: autor, moderador o admin
    permiso = EsPropietarioOModerador()
    if not permiso.has_object_permission(request, view=None, obj=comentario):
        return Response(
            {"error": "No tienes permiso para eliminar este comentario."},
            status=status.HTTP_403_FORBIDDEN
        )

    # 4) Eliminar y actualizar estadísticas
    relato = comentario.relato
    comentario.delete()
    actualizar_estadisticas(relato)

    # 5) Confirmación
    return Response(
        {"mensaje": "Comentario eliminado correctamente."},
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method='post',
    tags=["Comentarios"],
    operation_summary="Up-vote a un comentario",
    operation_description="Marca o cambia tu voto a positivo (+1).",
    manual_parameters=[
        openapi.Parameter("relato_id",     in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER),
        openapi.Parameter("comentario_id", in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: ComentarioSerializer,
        400: "Ya has votado positivamente este comentario",
        404: "Comentario no encontrado"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_votar_comentario(request, relato_id, comentario_id):
    # 1) Recuperar el comentario validando relato
    try:
        comentario = Comentario.objects.get(pk=comentario_id, relato_id=relato_id)
    except Comentario.DoesNotExist:
        return Response(
            {"error": "Comentario no encontrado en este relato."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Intentar recuperar voto existente
    try:
        voto = ComentarioVoto.objects.get(usuario=request.user, comentario=comentario)
        if voto.valor == ComentarioVoto.VOTOARRIBA:
            return Response(
                {"error": "Ya has votado positivamente este comentario."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # cambiar de down a up => +2
        voto.valor = ComentarioVoto.VOTOARRIBA
        voto.save(update_fields=['valor'])
        comentario.votos = F('votos') + 2

    except ComentarioVoto.DoesNotExist:
        # primer up-vote => +1
        ComentarioVoto.objects.create(
            usuario=request.user,
            comentario=comentario,
            valor=ComentarioVoto.VOTOARRIBA
        )
        comentario.votos = F('votos') + 1

    comentario.save(update_fields=['votos'])
    comentario.refresh_from_db()
    serializer = ComentarioSerializer(
    comentario,
    context={'request': request}
    )
    return Response(serializer.data)

@swagger_auto_schema(
    method='post',
    tags=["Comentarios"],
    operation_summary="Down-vote a un comentario",
    operation_description="Marca o cambia tu voto a negativo (-1).",
    manual_parameters=[
        openapi.Parameter("relato_id",     in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER),
        openapi.Parameter("comentario_id", in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: ComentarioSerializer,
        400: "Ya has votado negativamente este comentario",
        404: "Comentario no encontrado"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_quitar_voto_comentario(request, relato_id, comentario_id):
    # 1) Recuperar el comentario validando relato
    try:
        comentario = Comentario.objects.get(pk=comentario_id, relato_id=relato_id)
    except Comentario.DoesNotExist:
        return Response(
            {"error": "Comentario no encontrado en este relato."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Intentar recuperar voto existente
    try:
        voto = ComentarioVoto.objects.get(usuario=request.user, comentario=comentario)
        if voto.valor == ComentarioVoto.VOTOABAJO:
            return Response(
                {"error": "Ya has votado negativamente este comentario."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # cambiar de up a down => -2
        voto.valor = ComentarioVoto.VOTOABAJO
        voto.save(update_fields=['valor'])
        comentario.votos = F('votos') - 2

    except ComentarioVoto.DoesNotExist:
        # primer down-vote => -1
        ComentarioVoto.objects.create(
            usuario=request.user,
            comentario=comentario,
            valor=ComentarioVoto.VOTOABAJO
        )
        comentario.votos = F('votos') - 1

    comentario.save(update_fields=['votos'])
    comentario.refresh_from_db()
    serializer = ComentarioSerializer(
    comentario,
    context={'request': request}
    )
    return Response(serializer.data)

@swagger_auto_schema(
    method='delete',
    tags=["Comentarios"],
    operation_summary="Eliminar mi voto de un comentario",
    operation_description="Quita el voto (positivo o negativo) que el usuario haya dado.",
    manual_parameters=[
        openapi.Parameter("relato_id",     in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER),
        openapi.Parameter("comentario_id", in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: ComentarioSerializer,
        404: "Comentario o voto no encontrado"
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_voto_comentario(request, relato_id, comentario_id):
    # 1) Recuperar comentario
    try:
        comentario = Comentario.objects.get(pk=comentario_id, relato_id=relato_id)
    except Comentario.DoesNotExist:
        return Response({"error": "Comentario no encontrado."},
                        status=status.HTTP_404_NOT_FOUND)

    # 2) Recuperar voto del usuario
    try:
        voto = ComentarioVoto.objects.get(usuario=request.user, comentario=comentario)
    except ComentarioVoto.DoesNotExist:
        return Response({"error": "No existía un voto tuyo en este comentario."},
                        status=status.HTTP_404_NOT_FOUND)

    # 3) Ajustar contador neto
    comentario.votos = F('votos') - voto.valor
    comentario.save(update_fields=['votos'])
    comentario.refresh_from_db()

    # 4) Borrar registro
    voto.delete()

    # 5) Responder con el comentario actualizado
    serializer = ComentarioSerializer(comentario, context={'request': request})
    return Response(serializer.data)
