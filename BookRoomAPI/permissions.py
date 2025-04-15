from rest_framework.permissions import BasePermission
from .models import Usuario

class EsAdministrador(BasePermission):
    """
    Permite el acceso solo a usuarios con rol de Administrador.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == Usuario.ADMINISTRADOR

class EsCliente(BasePermission):
    """
    Permite el acceso solo a usuarios con rol de Cliente.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == Usuario.CLIENTE