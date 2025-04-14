from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class Usuario(AbstractUser):
    ADMINISTRADOR = 1
    CLIENTE = 2

    ROLES = (
        (ADMINISTRADOR, "administrador"),
        (CLIENTE, "cliente")
    )

    rol = models.PositiveSmallIntegerField(choices=ROLES, default=CLIENTE)

    def __str__(self):
        return self.username

class PerfilCliente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)

    # Datos personales
    biografia = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    pais = models.CharField(max_length=50, blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    
    # Datos literarios
    generos_favoritos = models.CharField(
        max_length=255,
        help_text='Lista separada por comas de géneros favoritos, ejemplo: fantasía, ciencia ficción, drama',
        blank=True,
        null=True
    )
    total_relatos_publicados = models.PositiveIntegerField(default=0)
    total_votos_recibidos = models.PositiveIntegerField(default=0)

    # Seguimiento
    seguidores = models.ManyToManyField('self', symmetrical=False, related_name='siguiendo', blank=True)

    def __str__(self):
        return f'Perfil de {self.usuario.username}'
