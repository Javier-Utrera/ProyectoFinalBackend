# Generated by Django 5.2 on 2025-06-08 19:51

import cloudinary_storage.storage
import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Relato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
                ('contenido', models.TextField(blank=True, help_text='Contenido completo del relato (HTML desde CKEditor)', null=True)),
                ('idioma', models.CharField(choices=[('en', 'Inglés'), ('ru', 'Ruso'), ('de', 'Alemán'), ('ja', 'Japonés'), ('es', 'Español')], default='en', help_text='Selecciona el idioma principal del relato', max_length=5)),
                ('generos', models.CharField(blank=True, choices=[('fantasia', 'Fantasía'), ('ciencia_ficcion', 'Ciencia ficción'), ('terror', 'Terror'), ('romance', 'Romance'), ('misterio', 'Misterio'), ('thriller', 'Thriller'), ('historico', 'Histórica'), ('aventura', 'Aventura'), ('poesia', 'Poesía'), ('humor', 'Humor')], help_text='Selecciona el género principal del relato', max_length=20)),
                ('estado', models.CharField(choices=[('CREACION', 'En creación'), ('EN_PROCESO', 'En proceso'), ('PUBLICADO', 'Publicado')], default='CREACION', max_length=20)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('num_escritores', models.PositiveSmallIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Suscripcion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('FREE', 'Gratuita'), ('PREMIUM', 'Premium')], default='FREE', max_length=10)),
                ('activa', models.BooleanField(default=True)),
                ('fecha_inicio', models.DateTimeField(auto_now_add=True)),
                ('fecha_fin', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ParticipacionRelato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenido_fragmento', models.TextField(blank=True, null=True)),
                ('orden', models.PositiveIntegerField(default=1)),
                ('listo_para_publicar', models.BooleanField(default=False)),
                ('fecha_ultima_aportacion', models.DateTimeField(auto_now=True)),
                ('relato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BookRoomAPI.relato')),
            ],
        ),
        migrations.CreateModel(
            name='Estadistica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_colaboradores', models.PositiveIntegerField(default=0)),
                ('num_comentarios', models.PositiveIntegerField(default=0)),
                ('promedio_votos', models.FloatField(default=0.0)),
                ('total_palabras', models.PositiveIntegerField(default=0)),
                ('tiempo_total', models.PositiveIntegerField(default=0)),
                ('relato', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='estadisticas', to='BookRoomAPI.relato')),
            ],
        ),
        migrations.CreateModel(
            name='Factura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.DecimalField(decimal_places=2, max_digits=8)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('pdf_url', models.URLField(blank=True, null=True)),
                ('suscripcion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facturas', to='BookRoomAPI.suscripcion')),
            ],
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('rol', models.PositiveSmallIntegerField(choices=[(1, 'administrador'), (3, 'moderador'), (2, 'cliente')], default=2)),
                ('biografia', models.TextField(blank=True, null=True)),
                ('avatar', models.ImageField(blank=True, default='avatars/img_avatar_ptmeu8', null=True, storage=cloudinary_storage.storage.MediaCloudinaryStorage(), upload_to='avatars/')),
                ('fecha_nacimiento', models.DateField(blank=True, null=True)),
                ('pais', models.CharField(blank=True, max_length=50, null=True)),
                ('ciudad', models.CharField(blank=True, max_length=50, null=True)),
                ('generos_favoritos', models.CharField(blank=True, help_text='Lista separada por comas de géneros favoritos, ejemplo: fantasía, ciencia ficción, drama', max_length=255, null=True)),
                ('total_relatos_publicados', models.PositiveIntegerField(default=0)),
                ('total_votos_recibidos', models.PositiveIntegerField(default=0)),
                ('total_palabras_escritas', models.PositiveIntegerField(default=0)),
                ('total_tiempo_escritura', models.PositiveIntegerField(default=0)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='suscripcion',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suscripciones', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='relato',
            name='autores',
            field=models.ManyToManyField(related_name='relatos_colaborados', through='BookRoomAPI.ParticipacionRelato', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='participacionrelato',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Mensaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField()),
                ('fecha_envio', models.DateTimeField(auto_now_add=True)),
                ('relato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes', to='BookRoomAPI.relato')),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Comentario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('votos', models.IntegerField(default=0, help_text='Contador neto de votos (positivo - negativo)')),
                ('relato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='BookRoomAPI.relato')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Voto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntuacion', models.PositiveSmallIntegerField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('relato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votos', to='BookRoomAPI.relato')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('usuario', 'relato')},
            },
        ),
        migrations.CreateModel(
            name='PeticionAmistad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('ACEPTADA', 'Aceptada'), ('BLOQUEADA', 'Bloqueada')], default='PENDIENTE', max_length=10)),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('fecha_aceptacion', models.DateTimeField(blank=True, null=True)),
                ('a_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amistades_recibidas', to=settings.AUTH_USER_MODEL)),
                ('de_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amistades_enviadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('de_usuario', 'a_usuario')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='participacionrelato',
            unique_together={('usuario', 'relato')},
        ),
        migrations.CreateModel(
            name='ComentarioVoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor', models.SmallIntegerField(choices=[(1, 'Voto-arriba'), (-1, 'VOoto-abajo')])),
                ('comentario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votos_usuario', to='BookRoomAPI.comentario')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('usuario', 'comentario')},
            },
        ),
    ]
