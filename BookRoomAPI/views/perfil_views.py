from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q
from drf_yasg import openapi
from BookRoomAPI.models import PeticionAmistad, Usuario
from ..serializers import UsuarioSerializer, UsuarioUpdateSerializer

#============================================================================================
# PERFIL
#============================================================================================

@swagger_auto_schema(
    method='get',
    tags=["Perfil"],
    operation_summary="Obtener perfil del usuario",
    operation_description="Devuelve los datos del usuario actualmente autenticado.",
    responses={200: UsuarioSerializer(), 401: "Token no válido"}
)
@swagger_auto_schema(
    method='patch',
    tags=["Perfil"],
    operation_summary="Editar perfil del usuario",
    operation_description="""
        Permite modificar:
        - Biografía (máx. 500 caracteres)
        - Fecha de nacimiento (no futura)
        - País, ciudad (solo letras y espacios)
        - Géneros favoritos (texto separado por comas)
    """,
    request_body=UsuarioUpdateSerializer,
    responses={200: "Perfil actualizado", 400: "Errores de validación", 401: "Token no válido"}
)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def obtener_perfil(request):
    # 1) Usuario autenticado
    user = request.user

    # 2) GET: serializar y devolver datos
    if request.method == 'GET':
        serializer = UsuarioSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 3) PATCH: validar y guardar cambios parciales
    serializer = UsuarioUpdateSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    # 4) Confirmar actualización
    return Response({'mensaje': 'Perfil actualizado correctamente'}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    tags=["Perfil"],
    operation_summary="Obtener perfil de un usuario",
    operation_description="""
      Devuelve los datos del usuario cuyo id pasas en la URL.
      Sólo tú (si pones tu propio id) o si sois amigos.
    """,
    manual_parameters=[ openapi.Parameter('usuario_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER) ],
    responses={200: UsuarioSerializer, 403: "Sin permiso", 404: "No existe"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_perfil_usuario(request, usuario_id):
    # 1) Objetivo existe?
    try:
        objetivo = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return Response(
          {"error": "Usuario no encontrado."},
          status=status.HTTP_404_NOT_FOUND
        )

    # 2) Si me pido a mi mismo, OK
    if objetivo.pk == request.user.pk:
        return Response(UsuarioSerializer(objetivo).data)

    # 3) Si no, compruebo amistad en dos queries sencillas
    es_amigo = PeticionAmistad.objects.filter(
        Q(de_usuario=request.user, a_usuario=objetivo, estado='ACEPTADA') |
        Q(de_usuario=objetivo, a_usuario=request.user, estado='ACEPTADA')
    ).exists()

    if not es_amigo:
        return Response(
          {"error": "Solo puedes ver el perfil de tus amigos."},
          status=status.HTTP_403_FORBIDDEN
        )

    # 4) Devuelvo el perfil del amigo
    return Response(UsuarioSerializer(objetivo).data)