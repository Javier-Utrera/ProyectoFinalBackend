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

import unicodedata
import re


def limpiar_texto(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'\W+', '', texto)
    return texto.lower()

def generar_username_unico(nombre_base):
    username_base = limpiar_texto(nombre_base) or "usuario"
    username = username_base
    contador = 1
    while Usuario.objects.filter(username=username).exists():
        username = f"{username_base}{contador}"
        contador += 1
    return username


class GoogleLoginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({'detail': 'No se envió id_token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
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

        base_nombre = nombre if nombre else email.split('@')[0]
        username_generado = generar_username_unico(base_nombre)

        user, created = Usuario.objects.get_or_create(
            email=email,
            defaults={'username': username_generado, 'first_name': nombre}
        )

        if not created:
            # Actualizar nombre si ha cambiado
            if user.first_name != nombre:
                user.first_name = nombre
                user.save()

        # Gestión suscripción
        if created or not user.suscripciones.filter(activa=True).exists():
            Suscripcion.objects.create(
                usuario=user,
                tipo='FREE',
                activa=True,
                fecha_inicio=timezone.now(),
                fecha_fin=None
            )

        # Token OAuth2
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
