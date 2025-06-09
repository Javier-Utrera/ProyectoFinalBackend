from django.utils import timezone
from django.db.models import Count
from rest_framework import generics, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Count, Sum

from BookRoomAPI.models import (
    ComentarioVoto, Usuario, Relato, ParticipacionRelato, Comentario, Voto,
    Suscripcion, Factura, Mensaje, Estadistica, PeticionAmistad
)
from BookRoomAPI.serializers import (
    UsuarioSerializer,
    RelatoSerializer,
    ParticipacionRelatoSerializer,
    ComentarioSerializer,
    VotoSerializer,
    SuscripcionSerializer,
    EstadisticaSerializer,
    MensajeSerializer,
    PeticionAmistadSerializer,
)
from BookRoomAPI.permissions import EsModeradorAdmin

# ——— Serializer Factura ———————————————————————————————

class FacturaAdminSerializer(serializers.ModelSerializer):
    usuario = serializers.ReadOnlyField(source='suscripcion.usuario.id')
    suscripcion = SuscripcionSerializer(read_only=True)

    class Meta:
        model = Factura
        fields = ['id', 'usuario', 'suscripcion', 'total', 'fecha', 'pdf_url']


# ——— Dashboard de métricas generales —————————————————————————

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(
        operation_summary="Obtener métricas generales",
        operation_description="Devuelve totales y estadísticas básicas para el panel de administración.",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_usuarios': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'usuarios_nuevos_ultima_semana': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_relatos': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'relatos_publicados': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_participaciones': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_comentarios': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_votos': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'suscripciones_activas': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'facturas_ultimo_mes': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_mensajes': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_estadisticas': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_peticiones_amistad': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )
        },
        tags=["Administrador"]
    )
    def get(self, request):
        now = timezone.now()
        semana = now - timezone.timedelta(days=7)
        mes = now - timezone.timedelta(days=30)

        # Usuarios
        total_usuarios = Usuario.objects.count()
        usuarios_nuevos_7d = Usuario.objects.filter(date_joined__gte=semana).count()
        usuarios_por_rol = dict(
            Usuario.objects
            .values('rol')
            .annotate(c=Count('id'))
            .order_by('rol')
            .values_list('rol', 'c')
        )

        # Relatos
        total_relatos = Relato.objects.count()
        relatos_por_estado = dict(
            Relato.objects
            .values('estado')
            .annotate(c=Count('id'))
            .values_list('estado', 'c')
        )

        # Participaciones
        total_participaciones = ParticipacionRelato.objects.count()

        # Comentarios y votos de comentarios
        total_comentarios = Comentario.objects.count()
        total_votos_comentarios = ComentarioVoto.objects.count()

        # Votos a relatos
        total_votos_relatos = Voto.objects.count()
        promedio_puntuacion = Voto.objects.aggregate(avg=Sum('puntuacion')/Count('id'))['avg'] or 0

        # Peticiones de amistad por estado
        pet_por_estado = dict(
            PeticionAmistad.objects
            .values('estado')
            .annotate(c=Count('id'))
            .values_list('estado', 'c')
        )

        # Suscripciones
        suscripciones_activas = Suscripcion.objects.filter(activa=True).count()
        suscripciones_por_tipo = dict(
            Suscripcion.objects
            .values('tipo')
            .annotate(c=Count('id'))
            .values_list('tipo', 'c')
        )

        # Facturas
        facturas_ult_mes = Factura.objects.filter(fecha__gte=mes).count()
        ingreso_ult_mes = Factura.objects.filter(fecha__gte=mes).aggregate(total=Sum('total'))['total'] or 0
        facturas_totales = Factura.objects.count()
        ingreso_total = Factura.objects.aggregate(total=Sum('total'))['total'] or 0

        # Mensajes y estadísticas
        total_mensajes = Mensaje.objects.count()
        total_estadisticas = Estadistica.objects.count()

        data = {
            'usuarios': {
                'total': total_usuarios,
                'nuevos_7d': usuarios_nuevos_7d,
                'por_rol': {
                    'administrador': usuarios_por_rol.get(Usuario.ADMINISTRADOR, 0),
                    'moderador':     usuarios_por_rol.get(Usuario.MODERADOR, 0),
                    'cliente':       usuarios_por_rol.get(Usuario.CLIENTE, 0),
                }
            },
            'relatos': {
                'total': total_relatos,
                'por_estado': relatos_por_estado
            },
            'participaciones': total_participaciones,
            'comentarios': {
                'total': total_comentarios,
                'votos_comentarios': total_votos_comentarios
            },
            'votos_relatos': {
                'total': total_votos_relatos,
                'promedio_puntuacion': round(promedio_puntuacion, 2)
            },
            'amistades': pet_por_estado,
            'suscripciones': {
                'activas': suscripciones_activas,
                'por_tipo': suscripciones_por_tipo
            },
            'facturas': {
                'ult_mes': {
                    'cantidad': facturas_ult_mes,
                    'ingreso': float(ingreso_ult_mes)
                },
                'total': {
                    'cantidad': facturas_totales,
                    'ingreso': float(ingreso_total)
                }
            },
            'mensajes': total_mensajes,
            'estadisticas': total_estadisticas,
        }
        return Response(data)


# ——— Vistas de listado ——————————————————————————————————————

class AdministradorUsuariosList(generics.ListAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar usuarios", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorRelatosList(generics.ListAPIView):
    queryset = Relato.objects.all().order_by('-fecha_creacion')
    serializer_class = RelatoSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar relatos", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorParticipacionesList(generics.ListAPIView):
    queryset = ParticipacionRelato.objects.select_related('usuario', 'relato').all().order_by('-fecha_ultima_aportacion')
    serializer_class = ParticipacionRelatoSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar participaciones", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorComentariosList(generics.ListAPIView):
    queryset = Comentario.objects.select_related('usuario', 'relato').all().order_by('-fecha')
    serializer_class = ComentarioSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar comentarios", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorVotosList(generics.ListAPIView):
    queryset = Voto.objects.select_related('usuario', 'relato').all().order_by('-fecha')
    serializer_class = VotoSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar votos", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorSuscripcionesList(generics.ListAPIView):
    queryset = Suscripcion.objects.select_related('usuario').all().order_by('-fecha_inicio')
    serializer_class = SuscripcionSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar suscripciones", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorFacturasList(generics.ListAPIView):
    queryset = Factura.objects.select_related('suscripcion__usuario').all().order_by('-fecha')
    serializer_class = FacturaAdminSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar facturas", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorMensajesList(generics.ListAPIView):
    queryset = Mensaje.objects.select_related('autor', 'relato').all().order_by('-fecha_envio')
    serializer_class = MensajeSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar mensajes", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorEstadisticasList(generics.ListAPIView):
    queryset = Estadistica.objects.select_related('relato').all().order_by('-promedio_votos')
    serializer_class = EstadisticaSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar estadísticas de relatos", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdministradorPeticionesAmistadList(generics.ListAPIView):
    queryset = PeticionAmistad.objects.select_related('de_usuario', 'a_usuario').all().order_by('-fecha_solicitud')
    serializer_class = PeticionAmistadSerializer
    permission_classes = [IsAuthenticated, EsModeradorAdmin]

    @swagger_auto_schema(operation_summary="Listar peticiones de amistad", tags=["Administrador"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
