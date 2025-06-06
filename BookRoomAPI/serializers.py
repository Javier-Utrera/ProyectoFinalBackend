from datetime import date
from rest_framework import serializers
from .models import *
import re

class SuscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suscripcion
        fields = [
            'tipo',         # 'FREE' o 'PREMIUM'
            'activa',       # True/False
            'fecha_inicio', # DateTime
            'fecha_fin',    # DateTime o null
        ]
        read_only_fields = fields

class UsuarioSerializerRegistro(serializers.Serializer):
    username = serializers.CharField(default="usuario123")
    email = serializers.EmailField(default="correo@gmail.com")
    password1 = serializers.CharField(default="contraseña",write_only=True)
    password2 = serializers.CharField(default="contraseña",write_only=True)

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

class UsuarioLoginResponseSerializer(serializers.ModelSerializer):
    # Exponemos el valor numérico…
    rol = serializers.IntegerField(read_only=True)
    rol_nombre = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'email',
            'avatar',
            'pais',
            'ciudad',
            'rol',
            'rol_nombre',
        ]
class UsuarioSerializer(serializers.ModelSerializer):
    # Serializa el campo avatar devolviendo la URL de la imagen
    avatar = serializers.ImageField(read_only=True)
    rol = serializers.IntegerField(read_only=True)
    rol_nombre = serializers.CharField(source='get_rol_display', read_only=True)

    # 1) Suscripción activa (anidada)
    suscripcion = SuscripcionSerializer(
        source='suscripcion_activa',  # usa el método del modelo
        read_only=True
    )

    # 2) Contadores semanales
    relatos_creados_semana = serializers.SerializerMethodField()
    participaciones_semana = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'email',
            'avatar',
            'biografia',
            'fecha_nacimiento',
            'pais',
            'ciudad',
            'generos_favoritos',
            'total_relatos_publicados',
            'total_votos_recibidos',
            'total_palabras_escritas',
            'rol',
            'rol_nombre',

            'suscripcion',
            'relatos_creados_semana',
            'participaciones_semana',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'avatar',
            'total_relatos_publicados',
            'total_votos_recibidos',
            'total_palabras_escritas',
            'rol',
            'rol_nombre',
            'suscripcion',
            'relatos_creados_semana',
            'participaciones_semana',
        ]

    def get_relatos_creados_semana(self, obj):
        """
        Cuenta cuántos relatos *creó* este usuario en los últimos 7 días:
        ParticipacionRelato con orden=1 y relato.fecha_creacion >= hace 7 días.
        """
        inicio_semana = timezone.now() - timedelta(days=7)
        return ParticipacionRelato.objects.filter(
            usuario=obj,
            orden=1,
            relato__fecha_creacion__gte=inicio_semana
        ).count()

    def get_participaciones_semana(self, obj):
        """
        Cuenta cuántas participaciones (ParticipacionRelato) de este usuario
        tienen fecha_ultima_aportacion en los últimos 7 días.
        """
        inicio_semana = timezone.now() - timedelta(days=7)
        return ParticipacionRelato.objects.filter(
            usuario=obj,
            fecha_ultima_aportacion__gte=inicio_semana
        ).count()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(default="usuario123")
    password = serializers.CharField(default="contraseña123")

#PERFIL----------------------------------------------------------------------------------------
class UsuarioUpdateSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Usuario
        fields = [
            'biografia', 'fecha_nacimiento', 'pais',
            'ciudad', 'generos_favoritos','avatar', 
        ]

    def validate_biografia(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("La biografía no puede superar los 500 caracteres.")
        return value

    def validate_fecha_nacimiento(self, value):
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return value

    def validar_campo_texto(self, valor, nombre_campo):
        import re
        if valor and not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]+$', valor):
            raise serializers.ValidationError(f"El campo {nombre_campo} contiene caracteres inválidos.")
        return valor

    def validate_pais(self, value):
        return self.validar_campo_texto(value, "país")

    def validate_ciudad(self, value):
        return self.validar_campo_texto(value, "ciudad")

    def validate_generos_favoritos(self, value):
        import re
        if value:
            if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ,]+$', value):
                raise serializers.ValidationError("Los géneros favoritos deben contener solo letras y comas.")
            generos = [g.strip() for g in value.split(',')]
            if any(not g for g in generos):
                raise serializers.ValidationError("Los géneros deben estar separados por comas correctamente.")
        return value
    
#RELATOS----------------------------------------------------------------------------------------
class ParticipacionRelatoSerializer(serializers.ModelSerializer):
    usuario = serializers.ReadOnlyField(source='usuario.id')

    class Meta:
        model = ParticipacionRelato
        fields = [
            'id',
            'usuario',
            'orden',
            'contenido_fragmento',
            'listo_para_publicar',
            'fecha_ultima_aportacion',
        ]
        read_only_fields = ('id', 'usuario', 'orden', 'fecha_ultima_aportacion')

class RelatoSerializer(serializers.ModelSerializer):
    autores = serializers.StringRelatedField(many=True)
    participaciones = ParticipacionRelatoSerializer(
        source='participacionrelato_set',
        many=True,
        read_only=True
    )

    # Campos de solo lectura para mostrar la etiqueta legible
    idioma_display  = serializers.CharField(source='get_idioma_display', read_only=True)
    generos_display = serializers.CharField(source='get_generos_display', read_only=True)

    class Meta:
        model = Relato
        fields = [
            'id',
            'titulo',
            'descripcion',
            'contenido',
            'idioma',
            'idioma_display',
            'generos',
            'generos_display',
            'estado',
            'fecha_creacion',
            'num_escritores',
            'autores',
            'participaciones',
        ]


class RelatoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relato
        fields = [
            'titulo',
            'descripcion',
            'contenido',
            'idioma',
            'generos',
            'num_escritores'
        ]

    def validate_titulo(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("El título debe tener al menos 3 caracteres.")
        return value

    def validate_descripcion(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("La descripción debe tener al menos 10 caracteres.")
        return value

    def validate_num_escritores(self, value):
        if not (1 <= value <= 4):
            raise serializers.ValidationError("El número de escritores debe estar entre 1 y 4.")
        return value

    def validate_generos(self, value):
        # Opcional: valida que el valor esté en los choices
        choices = dict(Relato.GENERO)
        if value and value not in choices:
            raise serializers.ValidationError("Género no válido.")
        return value


class RelatoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relato
        fields = [
            'titulo',
            'descripcion',
            'contenido',
            'idioma',
            'generos',
            'estado'
        ]

    def validate_titulo(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("El título debe tener al menos 3 caracteres.")
        return value

    def validate_descripcion(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("La descripción debe tener al menos 10 caracteres.")
        return value

    def validate_idioma(self, value):
        choices = dict(Relato.IDIOMAS)
        if value not in choices:
            raise serializers.ValidationError("Idioma no válido.")
        return value

    def validate_generos(self, value):
        choices = dict(Relato.GENERO)
        if value and value not in choices:
            raise serializers.ValidationError("Género no válido.")
        return value

    def validate_estado(self, value):
        valid = [c[0] for c in Relato.ESTADO_CHOICES]
        if value not in valid:
            raise serializers.ValidationError("Estado no válido.")
        return value

class MiFragmentoSerializer(serializers.ModelSerializer):
    relato = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ParticipacionRelato
        fields = [
            'id', 'relato', 'orden', 'contenido_fragmento', 'listo_para_publicar'
        ]
        read_only_fields = ('id', 'relato', 'orden', 'listo_para_publicar')

    
#PETICIONES AMISTAD----------------------------------------------------------------------------------------
class UsuarioAmigoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'avatar', 'pais', 'ciudad']

class SolicitudAmistadSerializer(serializers.Serializer):
    a_usuario = serializers.IntegerField(
        min_value=1,
        help_text="ID del usuario al que se envía la solicitud"
    )

class PeticionAmistadSerializer(serializers.ModelSerializer):
    de_usuario = UsuarioAmigoSerializer(read_only=True)
    a_usuario = UsuarioAmigoSerializer(read_only=True)

    class Meta:
        model = PeticionAmistad
        fields = [
            'id',
            'de_usuario',
            'a_usuario',
            'estado',
            'fecha_solicitud',
            'fecha_aceptacion'
        ]

#COMENTARIOS----------------------------------------------------------------------------------------
class ComentarioSerializer(serializers.ModelSerializer):
    mi_voto = serializers.SerializerMethodField()
    usuario = UsuarioSerializer(read_only=True)
    class Meta:
        model = Comentario
        fields = ['id','usuario','texto','fecha','relato','votos','mi_voto']
        read_only_fields = ('id','usuario','fecha','relato','votos','mi_voto')

    def get_mi_voto(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return 0
        try:
            voto = obj.votos_usuario.get(usuario=user)
            return voto.valor
        except:
            return 0
    
#VOTOS----------------------------------------------------------------------------------------
class VotoSerializer(serializers.ModelSerializer):
    usuario = UsuarioAmigoSerializer(read_only=True)
    
    class Meta:
        model = Voto
        fields = ['id', 'usuario', 'puntuacion', 'fecha', 'relato']
        read_only_fields = ('id', 'usuario', 'fecha', 'relato')

    def validate_puntuacion(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La puntuación debe estar entre 1 y 5.")
        return value
    
#ESTADISTICAS----------------------------------------------------------------------------------------
class EstadisticaSerializer(serializers.ModelSerializer):
    relato = serializers.PrimaryKeyRelatedField(read_only=True)
    titulo = serializers.CharField(source='relato.titulo', read_only=True)

    class Meta:
        model = Estadistica
        fields = [
            'relato',
            'titulo',
            'num_colaboradores',
            'num_comentarios',
            'promedio_votos',
            'total_palabras',
            'tiempo_total'
        ]

class UsuarioRankingSerializer(serializers.ModelSerializer):
    avatar_url = serializers.ImageField(source='avatar', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'avatar_url',
            'total_relatos_publicados',
            'total_votos_recibidos',
            'total_palabras_escritas',
        ]

#MENSAJE----------------------------------------------------------------------------------------
class MensajeSerializer(serializers.ModelSerializer):
    autor = serializers.StringRelatedField()
    class Meta:
        model = Mensaje
        fields = ['id', 'autor', 'texto', 'fecha_envio']