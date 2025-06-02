from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from cloudinary_storage.storage import MediaCloudinaryStorage
avatar_storage = MediaCloudinaryStorage()
# Create your models here.
class Usuario(AbstractUser):
    ADMINISTRADOR = 1
    CLIENTE       = 2
    MODERADOR     = 3

    ROLES = (
        (ADMINISTRADOR, "administrador"),
        (MODERADOR,     "moderador"),
        (CLIENTE,       "cliente"),
    )
    rol = models.PositiveSmallIntegerField(choices=ROLES, default=CLIENTE)

    # Datos personales
    biografia = models.TextField(blank=True, null=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        storage=avatar_storage,
        blank=True,
        null=True,
        default='avatars/img_avatar_ptmeu8'
    )
    fecha_nacimiento = models.DateField(blank=True, null=True)
    pais = models.CharField(max_length=50, blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    generos_favoritos = models.CharField(
        max_length=255,
        help_text='Lista separada por comas de géneros favoritos, ejemplo: fantasía, ciencia ficción, drama',
        blank=True,
        null=True
    )

    # Estadísticas globales
    total_relatos_publicados = models.PositiveIntegerField(default=0)
    total_votos_recibidos    = models.PositiveIntegerField(default=0)
    total_palabras_escritas  = models.PositiveIntegerField(default=0)
    total_tiempo_escritura   = models.PositiveIntegerField(default=0)  # en minutos

    def save(self, *args, **kwargs):
        # Forzar rol según flags de Django
        if self.is_superuser:
            self.rol = Usuario.ADMINISTRADOR
        elif self.is_staff:
            self.rol = Usuario.MODERADOR
        else:
            self.rol = Usuario.CLIENTE
        super().save(*args, **kwargs)

    # Métodos útiles (sin cambios)
    def amigos(self):
        desde = Usuario.objects.filter(
            amistades_enviadas__a_usuario=self,
            amistades_enviadas__estado='ACEPTADA'
        )
        hacia = Usuario.objects.filter(
            amistades_recibidas__de_usuario=self,
            amistades_recibidas__estado='ACEPTADA'
        )
        return desde.union(hacia)

    def amistades_pendientes(self):
        return self.amistades_enviadas.filter(estado='PENDIENTE')

    def amistades_por_responder(self):
        return self.amistades_recibidas.filter(estado='PENDIENTE')

    def total_colaboraciones(self):
        return self.relatos_colaborados.count()

    def __str__(self):
        return self.username
    
class Relato(models.Model):
    ESTADO_CHOICES = [
        ('CREACION', 'En creación'),
        ('EN_PROCESO', 'En proceso'),
        ('PUBLICADO', 'Publicado'),
    ]

    IDIOMAS = [
        ('en', 'Inglés'),
        ('ru', 'Ruso'),
        ('de', 'Alemán'),
        ('ja', 'Japonés'),
        ('es', 'Español'),
    ]

    GENERO = [
        ('fantasia',      'Fantasía'),
        ('ciencia_ficcion','Ciencia ficción'),
        ('terror',        'Terror'),
        ('romance',       'Romance'),
        ('misterio',      'Misterio'),
        ('thriller',      'Thriller'),
        ('historico',     'Histórica'),
        ('aventura',      'Aventura'),
        ('poesia',        'Poesía'),
        ('humor',         'Humor'),
    ]

    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    contenido = models.TextField(help_text="Contenido completo del relato (HTML desde CKEditor)",blank=True, null=True)
    idioma = models.CharField(max_length=5,choices=IDIOMAS,default='en',help_text='Selecciona el idioma principal del relato')
    generos = models.CharField(max_length=20,choices=GENERO,blank=True,help_text='Selecciona el género principal del relato')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='CREACION')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    num_escritores = models.PositiveSmallIntegerField(default=1)

    # Relación N:M con Usuario (colaboradores)
    autores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ParticipacionRelato',
        related_name='relatos_colaborados'
    )

    def num_colaboradores(self):
        # Devuelve el número de colaboradores en el relato
        return self.autores.count()
    
    def comprobar_estado_y_actualizar(self):
        # Cambia el estado a 'EN_PROCESO' si ya hay suficientes autores
        # según el num_escritores definido.
        if self.estado == 'CREACION' and self.autores.count() >= self.num_escritores:
            self.estado = 'EN_PROCESO'
            self.save()

    def comprobar_si_publicar(self):
        total_autores = self.autores.count()
        total_listos = self.participacionrelato_set.filter(listo_para_publicar=True).count()

        if total_autores == total_listos and self.estado != 'PUBLICADO':
            self.estado = 'PUBLICADO'
            self.save()


    def __str__(self):
        return self.titulo
    
class ParticipacionRelato(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    relato = models.ForeignKey('Relato', on_delete=models.CASCADE)

    # donde se guardara el HTML de este fragmento
    contenido_fragmento = models.TextField(blank=True, null=True)

    # posicion del fragmento en el relato
    orden = models.PositiveIntegerField(default=1)

    listo_para_publicar = models.BooleanField(default=False)
    fecha_ultima_aportacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('usuario', 'relato')
    
class PeticionAmistad(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADA', 'Aceptada'),
        ('BLOQUEADA', 'Bloqueada'),
    ]

    de_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='amistades_enviadas',
        on_delete=models.CASCADE
    )

    a_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='amistades_recibidas',
        on_delete=models.CASCADE
    )

    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_aceptacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        # Solo una solicitud entre los mismos dos usuarios
        unique_together = ('de_usuario', 'a_usuario')

    def __str__(self):
        return f"{self.de_usuario.username} → {self.a_usuario.username} ({self.estado})"
    
class Estadistica(models.Model):
    relato = models.OneToOneField('Relato', on_delete=models.CASCADE, related_name='estadisticas')

    num_colaboradores = models.PositiveIntegerField(default=0)
    num_comentarios = models.PositiveIntegerField(default=0)
    promedio_votos = models.FloatField(default=0.0)
    total_palabras = models.PositiveIntegerField(default=0)
    tiempo_total = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Estadísticas de: {self.relato.titulo}"

class Comentario(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    relato = models.ForeignKey(
        'Relato',
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    votos = models.IntegerField(
        default=0,
        help_text="Contador neto de votos (positivo - negativo)"
    )

    def __str__(self):
        return f"{self.usuario.username} comentó en '{self.relato.titulo}'"
    
class ComentarioVoto(models.Model):
    VOTOARRIBA = 1
    VOTOABAJO = -1
    VALOR_CHOICES = [
        (VOTOARRIBA, 'Voto-arriba'),
        (VOTOABAJO, 'VOoto-abajo'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    comentario = models.ForeignKey(
        Comentario,
        on_delete=models.CASCADE,
        related_name='votos_usuario'
    )
    valor = models.SmallIntegerField(choices=VALOR_CHOICES)

    class Meta:
        unique_together = ('usuario', 'comentario')

    def __str__(self):
        tipo = '+1' if self.valor == 1 else '-1'
        return f"{self.usuario.username} {tipo} comentario {self.comentario_id}"
    
class Voto(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votos'
    )
    relato = models.ForeignKey(
        'Relato',
        on_delete=models.CASCADE,
        related_name='votos'
    )
    puntuacion = models.PositiveSmallIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Un usuario solo puede votar una vez cada relato
        unique_together = ('usuario', 'relato')  

    def __str__(self):
        return f"{self.usuario.username} votó {self.puntuacion} a '{self.relato.titulo}'"
    
class Suscripcion(models.Model):
    TIPO_CHOICES = [
        ('FREE', 'Gratuita'),
        ('PREMIUM', 'Premium'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suscripciones'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='FREE')
    activa = models.BooleanField(default=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo} ({'Activa' if self.activa else 'Inactiva'})"
    
class Factura(models.Model):
    suscripcion = models.ForeignKey(
        'Suscripcion',
        on_delete=models.CASCADE,
        related_name='facturas'
    )
    total = models.DecimalField(max_digits=8, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Factura de {self.suscripcion.usuario.username} - {self.total}€"
    
class Mensaje(models.Model):
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    relato = models.ForeignKey(Relato, on_delete=models.CASCADE, related_name='mensajes')
    texto = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.autor.username} @ {self.fecha_envio}: {self.texto[:20]}…"