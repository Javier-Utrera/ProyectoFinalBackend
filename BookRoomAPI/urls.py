from django.urls import include, path
from . import views
from .views import *

from rest_framework import permissions



urlpatterns = [
    path('', views.home, name='home'),

    path('registro/', registrar_usuario, name='registrar_usuario'),
    path('login/', login_usuario, name='login_usuario'),
    path('logout/', logout_usuario, name='logout_usuario'),
    path('token/usuario/<str:token>/', obtener_usuario_por_token),

    #PERFIL----------------------------------------------------------------------------------------
    path('perfil/', obtener_perfil, name='obtener_perfil'),

    #RELATOS----------------------------------------------------------------------------------------
    path('relatos/publicados/', api_listar_relatos_publicados),
    path('relatos/', api_listar_relatos),
    path('relatos/crear/', api_crear_relato),
    path('relatos/<int:relato_id>/', api_obtener_relato),
    path('relatos/publicados/<int:relato_id>/', api_ver_relato_publicado),
    path('relatos/<int:relato_id>/editar/', api_editar_relato),
    path('relatos/<int:relato_id>/eliminar/', api_eliminar_relato),
    path('relatos/<int:relato_id>/marcar-listo/', api_marcar_relato_listo),
    path('relatos/abiertos/', api_relatos_abiertos),
    path('relatos/<int:relato_id>/unirse/', api_unirse_a_relato),
    path('relatos/<int:relato_id>/mi-fragmento/', api_mi_fragmento),
    path('relatos/<int:relato_id>/mi-fragmento/ready/', api_marcar_fragmento_listo),

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
    path('relatos/<int:relato_id>/comentarios/',views.api_listar_comentarios_relato,name='listar-comentarios-relato'),
    path('relatos/<int:relato_id>/comentarios/crear/',views.api_crear_comentario_relato,name='crear-comentario-relato'),
    path('relatos/<int:relato_id>/comentarios/<int:comentario_id>/editar/',api_editar_comentario_relato,name='editar-comentario'),
    path('relatos/<int:relato_id>/comentarios/<int:comentario_id>/borrar/',api_borrar_comentario_relato,name='borrar-comentario'),

    #VOTOS----------------------------------------------------------------------------------------
    path('relatos/<int:relato_id>/votar/', views.api_votar_relato, name='votar-relato'),
    path('relatos/<int:relato_id>/mi-voto/', views.api_mi_voto_relato, name='mi-voto-relato'),

    #ESTADISTICAS----------------------------------------------------------------------------------------
    path('estadisticas/relatos/<int:relato_id>/', api_estadisticas_relato, name='estadisticas-relato'),
    path('estadisticas/', api_listar_estadisticas, name='listar-estadisticas'),

]