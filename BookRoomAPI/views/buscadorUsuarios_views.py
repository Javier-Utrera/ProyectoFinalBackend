from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from BookRoomAPI.models import *
from BookRoomAPI.serializers import *
from BookRoomAPI.utils import *
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