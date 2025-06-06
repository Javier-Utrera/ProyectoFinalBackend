import cloudinary
from rest_framework.response import Response
from rest_framework import status
import traceback
from django.db.models import Avg
from .models import Voto

from django.conf import settings


import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .models import Relato
from BookRoomAPI.models import Factura

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

def generar_factura_pdf(factura: Factura) -> str:
    """
    Genera un PDF de la factura usando ReportLab (sin plantillas HTML) y sube el PDF a Cloudinary.
    Devuelve la URL pública del PDF en Cloudinary.
    """
    print(f"[Factura PDF] Generando PDF para la factura #{factura.id}...")

    # 1) Creamos un buffer en memoria
    buffer = io.BytesIO()
    print("[Factura PDF] Buffer de memoria creado.")

    # 2) Configuramos el PDF con ReportLab
    ancho, alto = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    print("[Factura PDF] Canvas PDF creado.")

    # 3) Definimos márgenes, posiciones, estilos básicos
    margen_izq = 20 * mm
    margen_sup = alto - 20 * mm
    salto_linea = 8 * mm

    # 4) Título de la factura
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margen_izq, margen_sup, f"Factura #{factura.id}")

    # 5) Datos de la factura (usuario, fecha)
    pdf.setFont("Helvetica", 10)
    y = margen_sup - salto_linea * 1.5
    fecha_str = factura.fecha.strftime("%d/%m/%Y %H:%M")
    pdf.drawString(margen_izq, y, f"Fecha: {fecha_str}")
    y -= salto_linea
    usuario = factura.suscripcion.usuario.username
    pdf.drawString(margen_izq, y, f"Usuario: {usuario}")

    # 6) Línea divisoria
    y -= salto_linea
    pdf.line(margen_izq, y, ancho - margen_izq, y)

    # 7) Detalle de la suscripción
    y -= salto_linea * 1.5
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margen_izq, y, "Detalle de la Suscripción:")

    y -= salto_linea
    pdf.setFont("Helvetica", 10)
    tipo = factura.suscripcion.tipo
    inicio = factura.suscripcion.fecha_inicio.strftime("%d/%m/%Y")
    fin = factura.suscripcion.fecha_fin.strftime("%d/%m/%Y")
    total = f"{factura.total:.2f} €"

    pdf.drawString(margen_izq, y, f"- Tipo: {tipo}")
    y -= salto_linea
    pdf.drawString(margen_izq, y, f"- Período: {inicio} al {fin}")
    y -= salto_linea
    pdf.drawString(margen_izq, y, f"- Total: {total}")

    # 8) Nota de agradecimiento
    y -= salto_linea * 2
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(margen_izq, y, "¡Gracias por tu suscripción a BookRoomAPI Premium!")

    # 9) Finalizar y cerrar PDF
    pdf.showPage()
    pdf.save()
    print("[Factura PDF] PDF generado en memoria.")

    # 10) Obtener el contenido binario del buffer
    buffer.seek(0)
    contenido_pdf = buffer.read()
    print(f"[Factura PDF] Tamaño del PDF generado: {len(contenido_pdf)} bytes.")

    # 11) Subir a Cloudinary
    print("[Factura PDF] Subiendo PDF a Cloudinary...")
    resultado = cloudinary.uploader.upload(
        io.BytesIO(contenido_pdf),
        resource_type="raw", 
        public_id=f"factura_{factura.id}.pdf",
        folder="facturas",
        overwrite=True
    )
    print(f"[Factura PDF] Respuesta de Cloudinary: {resultado}")

    # 12) Extraer la URL pública que Cloudinary devuelve
    url_publica = resultado.get("secure_url")
    print(f"[Factura PDF] URL pública del PDF: {url_publica}")

    # 13) Retornar la URL
    return url_publica