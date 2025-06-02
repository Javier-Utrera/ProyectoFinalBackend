from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdminPersonalizado(UserAdmin):
    model = Usuario
    list_display = ['username', 'email', 'rol', 'is_staff', 'is_superuser']
    list_filter  = ['rol', 'is_staff', 'is_superuser', 'is_active']

    fieldsets = UserAdmin.fieldsets + (
        ('Perfil adicional', {
            'fields': (
                'rol',
                'biografia',
                'avatar',
                'fecha_nacimiento',
                'pais',
                'ciudad',
                'generos_favoritos',
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Perfil adicional', {
            'classes': ('wide',),
            'fields': (
                'rol',
                'biografia',
                'avatar',
                'fecha_nacimiento',
                'pais',
                'ciudad',
                'generos_favoritos',
            )
        }),
    )


admin.site.register(Usuario, UsuarioAdminPersonalizado)
