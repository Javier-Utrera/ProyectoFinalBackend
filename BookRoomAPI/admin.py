from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdminPersonalizado(UserAdmin):
    model = Usuario
    list_display = ['username', 'email', 'rol', 'is_staff', 'is_superuser']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Rol personalizado', {'fields': ('rol',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rol personalizado', {'fields': ('rol',)}),
    )


admin.site.register(Usuario, UsuarioAdminPersonalizado)
