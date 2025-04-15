from django.urls import include, path
from . import views
from .views import *

urlpatterns = [
    path('', views.home),
    path('registro/', RegistrarUsuarioAPIView.as_view(), name='registro_usuario'),
    path('login/', login_usuario, name='login_usuario'),
    path('logout/', logout_usuario, name='logout_usuario'),
    path('token/usuario/<str:token>/', obtener_usuario_por_token, name='usuario_por_token'),

    path('perfil/', obtener_perfil, name='obtener_perfil'),
]