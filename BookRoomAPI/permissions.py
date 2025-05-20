from rest_framework import permissions
from .models import Usuario

class EsPropietarioOModerador(permissions.BasePermission):
    """
    SAFE_METHODS siempre True.
    EDIT/DELETE permitido si:
      - request.user.rol es ADMINISTRADOR o MODERADOR.
      - o bien eres propietario del objeto:
          * Relato: estás en obj.autores (y para DELETE solo si eres único autor).
          * ParticipacionRelato/Comentario: obj.usuario == request.user.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # 1) Lecturas (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2) Rol ADMINISTRADOR o MODERADOR tiene vía libre
        if request.user.rol in (Usuario.ADMINISTRADOR, Usuario.MODERADOR):
            return True

        # 3) Propietario de Relato
        if hasattr(obj, 'autores') and obj.autores.filter(pk=request.user.pk).exists():
            # Para borrar solo si eres único autor
            if request.method == 'DELETE' and obj.autores.count() > 1:
                return False
            return True

        # 4) Propietario de ParticipacionRelato o Comentario
        if hasattr(obj, 'usuario') and obj.usuario_id == request.user.pk:
            return True

        # 5) Resto: denegado
        return False
    

class EsModeradorAdmin(permissions.BasePermission):
    """
    Acceso sólo a moderadores (rol=MODERADOR) o administradores.
    Utilízalo para endpoints que sólo ellos deban tocar.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in (Usuario.MODERADOR, Usuario.ADMINISTRADOR)
        )
