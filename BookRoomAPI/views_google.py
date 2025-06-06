import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from oauth2_provider.models import AccessToken, Application
from oauthlib.common import generate_token
from django.utils import timezone
from datetime import timedelta

from .models import Suscripcion, Usuario
from .serializers import UsuarioSerializer


class GoogleLoginAPIView(APIView):
    permission_classes = []  # Público

    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({'detail': 'No se envió id_token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verifica el ID token contra Google usando tu CLIENT_ID
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                os.getenv('GOOGLE_CLIENT_ID')
            )
        except ValueError:
            return Response({'detail': 'ID token inválido o expirado'}, status=status.HTTP_401_UNAUTHORIZED)

        email = idinfo.get('email')
        nombre = idinfo.get('name') or ''

        if not email:
            return Response({'detail': 'ID token no contiene email'}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Creamos (o recuperamos) el Usuario
        user, created = Usuario.objects.get_or_create(
            email=email,
            defaults={'username': email, 'first_name': nombre}
        )

        # 2) Si se acaba de crear el usuario, le añadimos la suscripción FREE
        if created:
            Suscripcion.objects.create(
                usuario=user,
                tipo='FREE',
                activa=True,
                fecha_inicio=timezone.now(),
                fecha_fin=None
            )
        else:
            # 3) Si ya existía, comprobamos si no tiene ninguna suscripción activa
            if not user.suscripciones.filter(activa=True).exists():
                Suscripcion.objects.create(
                    usuario=user,
                    tipo='FREE',
                    activa=True,
                    fecha_inicio=timezone.now(),
                    fecha_fin=None
                )

        # 4) Generamos o reutilizamos el token OAuth2
        app = get_object_or_404(Application, name="BookRoomAPI")
        token_obj = AccessToken.objects.filter(
            user=user,
            application=app,
            expires__gt=timezone.now()
        ).first()

        if not token_obj:
            token_obj = AccessToken.objects.create(
                user=user,
                token=generate_token(),
                application=app,
                expires=timezone.now() + timedelta(hours=10),
                scope='read write'
            )

        return Response({
            'access_token': token_obj.token,
            'user': UsuarioSerializer(user).data
        }, status=status.HTTP_200_OK)
