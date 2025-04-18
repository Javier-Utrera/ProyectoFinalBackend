from django.urls import include, path
from . import views
from .views import *

from rest_framework import permissions



urlpatterns = [
    path('', views.home),

    path('registro/', RegistrarUsuarioAPIView.as_view(), name='registro_usuario'),
    path('login/', login_usuario, name='login_usuario'),
    path('logout/', logout_usuario, name='logout_usuario'),
    path('token/usuario/<str:token>/', obtener_usuario_por_token, name='usuario_por_token'),
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
]