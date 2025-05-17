from django.urls import path
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

    # Creación y detalle
    path('relatos/crear/', api_crear_relato,name='relatos-crear'),
    path('relatos/<int:relato_id>/',api_obtener_relato,name='relatos-detalle'),
    path('relatos/publicados/<int:relato_id>/',api_ver_relato_publicado,name='relatos-detalle-publico'),

    # Edición y borrado
    path('relatos/<int:relato_id>/editar/',api_editar_relato,name='relatos-editar'),
    path('relatos/<int:relato_id>/eliminar/',api_eliminar_relato,name='relatos-eliminar'),

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

    #VOTOS----------------------------------------------------------------------------------------
    path('relatos/<int:relato_id>/votar/', api_votar_relato, name='votar-relato'),
    path('relatos/<int:relato_id>/mi-voto/', api_mi_voto_relato, name='mi-voto-relato'),

    #ESTADISTICAS----------------------------------------------------------------------------------------
    path('estadisticas/relatos/<int:relato_id>/', api_estadisticas_relato, name='estadisticas-relato'),
    path('estadisticas/', api_listar_estadisticas, name='listar-estadisticas'),
    path('ranking-usuarios/', ranking_usuarios, name='ranking-usuarios'),

]