from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from BookRoomAPI.paypal_utils import create_order, capture_order
from BookRoomAPI.models import Suscripcion, Factura
from BookRoomAPI.utils import generar_factura_pdf


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_orden_paypal(request):
    """
    Crea una orden de PayPal por el importe de la suscripción PREMIUM (fijo).
    Solo responde con el orderID y los links.
    """
    IMPORTE_SUSCRIPCION = "3.99"
    try:
        respuesta = create_order(IMPORTE_SUSCRIPCION, currency="EUR")
    except Exception as e:
        return Response(
            {"error": "Error al comunicarse con PayPal", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    order_id = respuesta.result.id
    order_status = respuesta.result.status
    links = []
    for link in respuesta.result.links:
        links.append({
            "rel": link.rel,
            "href": link.href,
            "method": link.method
        })
    return Response({
        "orderID": order_id,
        "status": order_status,
        "links": links
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def capturar_y_crear_suscripcion(request):
    """
    1) Recibe {"orderID": "<id_de_paypal>"}.
    2) Captura la orden en PayPal sandbox.
    3) Si se completa correctamente, crea una Suscripcion y una Factura,
       genera el PDF de la factura y lo sube a Cloudinary.
    4) Devuelve JSON con status, captureID, datos de suscripción y URL del PDF.
    """
    user = request.user
    order_id = request.data.get('orderID')
    if not order_id:
        return Response(
            {"error": "Debes enviar 'orderID' en el body."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 1) Llamar a PayPal para capturar la orden
    try:
        captura = capture_order(order_id)
    except Exception as e:
        return Response(
            {"error": "Error al capturar la orden en PayPal", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # 2) Verificar que la captura se completó
    if captura.result.status != "COMPLETED":
        return Response(
            {"error": "La captura no se completó correctamente", "status": captura.result.status},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3) Crear la Suscripcion en la base de datos
    ahora = timezone.now()
    fecha_fin = ahora + timedelta(days=30)  # Suscripción de 30 días
    sus_anterior = Suscripcion.objects.filter(usuario=user, activa=True).order_by('-fecha_inicio').first()
    if sus_anterior:
        sus_anterior.activa = False
        sus_anterior.save(update_fields=['activa'])

    suscripcion = Suscripcion.objects.create(
        usuario=user,
        tipo='PREMIUM',
        activa=True,
        fecha_inicio=ahora,
        fecha_fin=fecha_fin
    )

    # 4) Crear la Factura asociada
    factura = Factura.objects.create(
        suscripcion=suscripcion,
        total=3.99
    )

    # 5) Generar PDF de la factura y subir a Cloudinary
    pdf_url = generar_factura_pdf(factura)

    # 6) Devolver la respuesta con los datos
    return Response({
        "status": captura.result.status,
        "captureID": captura.result.purchase_units[0].payments.captures[0].id,
        "suscripcion": {
            "tipo": suscripcion.tipo,
            "fecha_inicio": suscripcion.fecha_inicio,
            "fecha_fin": suscripcion.fecha_fin,
            "activa": suscripcion.activa,
        },
        "factura": {
            "id": factura.id,
            "total": str(factura.total),
            "fecha": factura.fecha,
            "pdf_url": pdf_url
        }
    }, status=status.HTTP_200_OK)
