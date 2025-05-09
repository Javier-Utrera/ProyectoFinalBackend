from rest_framework.response import Response
from rest_framework import status
import traceback
from django.db.models import Avg
from .models import Voto

from .models import Relato

def api_errores(serializer, mensaje="Operación realizada con éxito", status_success=status.HTTP_201_CREATED):
    if serializer.is_valid():
        try:
            serializer.save()
            return Response({"mensaje": mensaje}, status=status_success)
        except Exception as error:
            print("ERROR 500 en la API:", repr(error))
            traceback.print_exc()
            return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        print("ERRORES DEL SERIALIZADOR:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
def obtener_relato_de_usuario(relato_id, usuario):
    try:
        return Relato.objects.get(id=relato_id, autores=usuario)
    except Relato.DoesNotExist:
        return None
    
def actualizar_estadisticas(relato):
    estad = relato.estadisticas
    estad.num_colaboradores = relato.autores.count()
    estad.num_comentarios   = relato.comentarios.count()
    texto = relato.contenido or ""
    estad.total_palabras     = len(texto.split())
    estad.promedio_votos     = (
        Voto.objects
            .filter(relato=relato)
            .aggregate(avg=Avg('puntuacion'))['avg']
        or 0
    )
    estad.save()