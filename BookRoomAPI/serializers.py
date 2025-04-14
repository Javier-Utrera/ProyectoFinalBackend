from rest_framework import serializers
from .models import Usuario
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