from django.urls import path

from BookRoomAPI.views_google import GoogleLoginAPIView
from BookRoomAPI.views_paypal import capturar_y_crear_suscripcion, crear_orden_paypal
from . import views
from .views import *



urlpatterns = [
    path('', views.home, name='home'),

    path('registro/', registrar_usuario, name='registrar_usuario'),
    path('login/', login_usuario, name='login_usuario'),
    path('logout/', logout_usuario, name='logout_usuario'),
    path('token/usuario/<str:token>/', obtener_usuario_por_token),

    #PERFIL----------------------------------------------------------------------------------------
    path('perfil/', obtener_perfil, name='obtener_perfil'),
    path('perfil/<int:usuario_id>/', obtener_perfil_usuario, name='perfil-usuario'),

    #RELATOS----------------------------------------------------------------------------------------

    # Listados con CBV
    path('relatos/publicados/',RelatosPublicadosList.as_view(),name='relatos-publicados'),
    path('relatos/disponibles/',RelatosDisponiblesList.as_view(),name='relatos-disponibles'),
    path('relatos/mis-relatos/',MisRelatosList.as_view(),name='relatos-mis-relatos'),

    # Expongo los choices idiomas y generos
    path('opciones-relato/', opciones_relato, name='opciones_relato'),

    # Creación y detalle
    path('relatos/crear/', api_crear_relato,name='relatos-crear'),
    path('relatos/<int:relato_id>/',api_obtener_relato,name='relatos-detalle'),
    path('relatos/publicados/<int:relato_id>/',api_ver_relato_publicado,name='relatos-detalle-publico'),

    # Edición y borrado
    path('relatos/<int:relato_id>/editar/',api_editar_relato,name='relatos-editar'),
    path('relatos/<int:relato_id>/eliminar/',api_eliminar_relato,name='relatos-eliminar'),

    #Edicion y borrado relato MODERADOR
    path('moderador/relatos/<int:relato_id>/editar-final/',api_editar_relato_final,name='moderador-editar-relato-final'),

    # Marcado listo y participación
    path('relatos/<int:relato_id>/marcar-listo/',api_marcar_relato_listo,name='relatos-marcar-listo'),
    path('relatos/<int:relato_id>/unirse/',api_unirse_a_relato,name='relatos-unirse'),

    # Fragmentos
    path('relatos/<int:relato_id>/mi-fragmento/',api_mi_fragmento,name='relatos-mi-fragmento'),
    path('relatos/<int:relato_id>/mi-fragmento/ready/',api_marcar_fragmento_listo,name='relatos-fragmento-ready'),

    #BUSCADOR USUARIOS----------------------------------------------------------------------------------------
    path('usuarios/buscar/', api_buscar_usuarios),

    #PETICIONES AMISTAD----------------------------------------------------------------------------------------
    path('amigos/enviar/', api_enviar_solicitud_amistad),
    path('amigos/recibidas/', api_solicitudes_recibidas),
    path('amigos/aceptar/<int:solicitud_id>/', api_aceptar_solicitud_amistad),
    path('amigos/', api_listar_amigos),
    path('amigos/enviadas/', api_solicitudes_enviadas),
    path('amigos/bloquear/<int:solicitud_id>/', api_bloquear_solicitud_amistad),
    path('amigos/bloqueados/', api_listar_bloqueados),
    path('amigos/desbloquear/<int:usuario_id>/', api_desbloquear_usuario),
    path('amigos/eliminar/<int:usuario_id>/', api_eliminar_amigo),

    #COMENTARIOS----------------------------------------------------------------------------------------
    path('relatos/<int:relato_id>/comentarios/',api_listar_comentarios_relato,name='listar-comentarios-relato'),
    path('relatos/<int:relato_id>/comentarios/crear/',api_crear_comentario_relato,name='crear-comentario-relato'),
    path('relatos/<int:relato_id>/comentarios/<int:comentario_id>/editar/',api_editar_comentario_relato,name='editar-comentario'),
    path('relatos/<int:relato_id>/comentarios/<int:comentario_id>/borrar/',api_borrar_comentario_relato,name='borrar-comentario'),
    path('relatos/<int:relato_id>/comentarios/<int:comentario_id>/votar/', api_votar_comentario, name='votar-comentario'),
    path('relatos/<int:relato_id>/comentarios/<int:comentario_id>/quitar-voto/',api_quitar_voto_comentario,name='quitar-voto-comentario'),
    path('relatos/<int:relato_id>/comentarios/<int:comentario_id>/voto/',api_eliminar_voto_comentario,name='eliminar-voto-comentario'),

        #Mesanjes en la pagina de escribir el relato
    path('relatos/<int:relato_id>/mensajes/', MensajesRelatoList.as_view(), name='mensajes-relato'),
    #VOTOS----------------------------------------------------------------------------------------
    path('relatos/<int:relato_id>/votar/', api_votar_relato, name='votar-relato'),
    path('relatos/<int:relato_id>/mi-voto/', api_mi_voto_relato, name='mi-voto-relato'),

    #ESTADISTICAS----------------------------------------------------------------------------------------
    path('estadisticas/relatos/<int:relato_id>/', api_estadisticas_relato, name='estadisticas-relato'),
    path('estadisticas/', api_listar_estadisticas, name='listar-estadisticas'),
    path('ranking-usuarios/', ranking_usuarios, name='ranking-usuarios'),

    path('auth/google-login/', GoogleLoginAPIView.as_view(), name='google-login'),

    path('paypal/crear-orden/', crear_orden_paypal, name='crear-orden-paypal'),
    path('paypal/capturar-y-suscribirse/', capturar_y_crear_suscripcion, name='capturar_y_crear_suscripcion'),

    #Dashboard de administrador
    path('admin/dashboard/', DashboardStatsView.as_view(), name='admin-dashboard'),
    # Listados generales
    path('admin/usuarios/', AdministradorUsuariosList.as_view(), name='admin-usuarios'),
    path('admin/relatos/', AdministradorRelatosList.as_view(), name='admin-relatos'),
    path('admin/participaciones/', AdministradorParticipacionesList.as_view(), name='admin-participaciones'),
    path('admin/comentarios/', AdministradorComentariosList.as_view(), name='admin-comentarios'),
    path('admin/votos/', AdministradorVotosList.as_view(), name='admin-votos'),
    path('admin/suscripciones/', AdministradorSuscripcionesList.as_view(), name='admin-suscripciones'),
    path('admin/facturas/', AdministradorFacturasList.as_view(), name='admin-facturas'),
    path('admin/mensajes/', AdministradorMensajesList.as_view(), name='admin-mensajes'),
    path('admin/estadisticas/', AdministradorEstadisticasList.as_view(), name='admin-estadisticas'),
    path('admin/peticiones-amistad/', AdministradorPeticionesAmistadList.as_view(), name='admin-peticiones-amistad'),
]