# BookRoomAPI/middleware.py

from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from oauth2_provider.models import AccessToken
from django.utils import timezone
from channels.db import database_sync_to_async

class TokenAuthMiddleware:
    """
    Middleware Channels que extrae ?token=<access_token> de la URL
    y asigna scope['user'] al usuario correspondiente.
    Debe aceptar los tres parámetros (scope, receive, send).
    """
    def __init__(self, inner):
        # `inner` es el siguiente ASGI app
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # 1) Leer la query string
        query_string = scope.get('query_string', b'').decode()
        qs = parse_qs(query_string)
        token_list = qs.get('token')

        # 2) Inicialmente marcamos como AnonymousUser
        scope['user'] = AnonymousUser()

        # 3) Si hay un token, intentamos cargar el usuario
        if token_list:
            token = token_list[0]
            user = await self.get_user(token)
            if user:
                scope['user'] = user

        # 4) Llamamos al siguiente componente en la cadena ASGI
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        """
        Busca el AccessToken en la base de datos y devuelve el usuario
        sólo si el token existe y no está expirado.
        """
        try:
            at = AccessToken.objects.select_related('user').get(token=token)
            if at.expires > timezone.now():
                return at.user
        except AccessToken.DoesNotExist:
            pass
        return None
