from datetime import date
from rest_framework import serializers
from .models import *
import re

class UsuarioSerializerRegistro(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        errores = {}

        # Validación de username
        if not data.get("username", "").strip():
            errores["username"] = "El nombre de usuario es obligatorio."
        elif Usuario.objects.filter(username=data["username"]).exists():
            errores["username"] = "El nombre de usuario ya está en uso."
        elif len(data["username"]) < 3:
            errores["username"] = "El nombre de usuario debe tener al menos 3 caracteres."

        # Validación de email
        if not data.get("email", "").strip():
            errores["email"] = "El correo electrónico es obligatorio."
        if Usuario.objects.filter(email=data["email"]).exists():
            errores["email"] = "El correo electrónico ya está registrado."

        # Validación de contraseñas
        password1 = data.get("password1", "")
        password2 = data.get("password2", "")

        if password1 != password2:
            errores["password"] = "Las contraseñas no coinciden."
        # else:
        #     if len(password1) < 8:
        #         errores["password"] = "La contraseña debe tener al menos 8 caracteres."
        #     elif not re.search(r"[A-Z]", password1):
        #         errores["password"] = "La contraseña debe contener al menos una letra mayúscula."
        #     elif not re.search(r"[a-z]", password1):
        #         errores["password"] = "La contraseña debe contener al menos una letra minúscula."
        #     elif not re.search(r"[0-9]", password1):
        #         errores["password"] = "La contraseña debe contener al menos un número."

        if errores:
            raise serializers.ValidationError(errores)

        return data


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'rol']

#PERFIL----------------------------------------------------------------------------------------
class PerfilClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilCliente
        exclude = ['usuario']

class UsuarioConPerfilSerializer(serializers.ModelSerializer):
    perfil = PerfilClienteSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'rol', 'perfil']

class PerfilClienteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilCliente
        fields = ['biografia', 'fecha_nacimiento', 'pais', 'ciudad', 'generos_favoritos']

    def validate_biografia(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("La biografía no puede superar los 500 caracteres.")
        return value

    def validate_fecha_nacimiento(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return value

    def validar_campo_texto(self, valor, nombre_campo):
        if valor and not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]+$', valor):
            raise serializers.ValidationError(f"El campo {nombre_campo} contiene caracteres inválidos.")
        return valor

    def validate_pais(self, value):
        return self.validar_campo_texto(value, "país")

    def validate_ciudad(self, value):
        return self.validar_campo_texto(value, "ciudad")

    def validate_generos_favoritos(self, value):
        if value:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ,]+$', value):
                raise serializers.ValidationError("Los géneros favoritos deben contener solo letras y comas.")
            # Validar que hay al menos un género separado por comas
            generos = [g.strip() for g in value.split(',')]
            if any(not g for g in generos):
                raise serializers.ValidationError("Los géneros deben estar separados por comas correctamente.")
        return value