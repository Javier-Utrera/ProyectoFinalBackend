from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from django.conf import settings

def get_paypal_client():
    """
    Inicializa y devuelve un cliente de PayPal configurado
    con el CLIENT_ID y CLIENT_SECRET de settings.
    Usa sandbox o live según PAYPAL_MODE.
    """
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET
    mode = settings.PAYPAL_MODE  # debe ser 'sandbox' o 'live'

    if mode == 'live':
        env = LiveEnvironment(client_id=client_id, client_secret=client_secret)
    else:
        env = SandboxEnvironment(client_id=client_id, client_secret=client_secret)

    return PayPalHttpClient(env)


def create_order(amount: str, currency: str = "EUR"):
    """
    Crea una orden de PayPal por el importe indicado (amount).
    Retorna la respuesta con el order ID y links.
    """
    client = get_paypal_client()
    request = OrdersCreateRequest()
    request.prefer('return=representation')
    request.request_body({
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": currency,
                    "value": amount
                }
            }
        ]
    })

    response = client.execute(request)
    return response


def capture_order(order_id: str):
    """
    Captura el pago de una orden ya aprobada en PayPal.
    Retorna la respuesta de PayPal con detalles de la captura.
    """
    client = get_paypal_client()
    request = OrdersCaptureRequest(order_id)
    request.prefer('return=representation')
    response = client.execute(request)
    return response
