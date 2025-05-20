# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class BookroomapiComentario(models.Model):
    id = models.BigAutoField(primary_key=True)
    texto = models.TextField()
    fecha = models.DateTimeField()
    relato = models.ForeignKey('BookroomapiRelato', models.DO_NOTHING)
    usuario = models.ForeignKey('BookroomapiUsuario', models.DO_NOTHING)
    votos = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_comentario'


class BookroomapiComentariovoto(models.Model):
    id = models.BigAutoField(primary_key=True)
    comentario = models.ForeignKey(BookroomapiComentario, models.DO_NOTHING)
    usuario = models.ForeignKey('BookroomapiUsuario', models.DO_NOTHING)
    valor = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_comentariovoto'
        unique_together = (('usuario', 'comentario'),)


class BookroomapiEstadistica(models.Model):
    id = models.BigAutoField(primary_key=True)
    num_colaboradores = models.PositiveIntegerField()
    num_comentarios = models.PositiveIntegerField()
    promedio_votos = models.FloatField()
    total_palabras = models.PositiveIntegerField()
    tiempo_total = models.PositiveIntegerField()
    relato = models.OneToOneField('BookroomapiRelato', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_estadistica'


class BookroomapiFactura(models.Model):
    id = models.BigAutoField(primary_key=True)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    fecha = models.DateTimeField()
    suscripcion = models.ForeignKey('BookroomapiSuscripcion', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_factura'


class BookroomapiParticipacionrelato(models.Model):
    id = models.BigAutoField(primary_key=True)
    listo_para_publicar = models.IntegerField()
    fecha_ultima_aportacion = models.DateTimeField()
    relato = models.ForeignKey('BookroomapiRelato', models.DO_NOTHING)
    usuario = models.ForeignKey('BookroomapiUsuario', models.DO_NOTHING)
    contenido_fragmento = models.TextField(blank=True, null=True)
    orden = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_participacionrelato'
        unique_together = (('usuario', 'relato'),)


class BookroomapiPeticionamistad(models.Model):
    id = models.BigAutoField(primary_key=True)
    estado = models.CharField(max_length=10)
    fecha_solicitud = models.DateTimeField()
    fecha_aceptacion = models.DateTimeField(blank=True, null=True)
    a_usuario = models.ForeignKey('BookroomapiUsuario', models.DO_NOTHING)
    de_usuario = models.ForeignKey('BookroomapiUsuario', models.DO_NOTHING, related_name='bookroomapipeticionamistad_de_usuario_set')

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_peticionamistad'
        unique_together = (('de_usuario', 'a_usuario'),)


class BookroomapiRelato(models.Model):
    id = models.BigAutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    contenido = models.TextField(blank=True, null=True)
    idioma = models.CharField(max_length=50)
    estado = models.CharField(max_length=20)
    fecha_creacion = models.DateTimeField()
    num_escritores = models.PositiveSmallIntegerField()
    generos = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_relato'


class BookroomapiSuscripcion(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo = models.CharField(max_length=10)
    activa = models.IntegerField()
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    usuario = models.ForeignKey('BookroomapiUsuario', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_suscripcion'


class BookroomapiUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()
    rol = models.PositiveSmallIntegerField()
    biografia = models.TextField(blank=True, null=True)
    avatar = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    pais = models.CharField(max_length=50, blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    generos_favoritos = models.CharField(max_length=255, blank=True, null=True)
    total_relatos_publicados = models.PositiveIntegerField()
    total_votos_recibidos = models.PositiveIntegerField()
    total_palabras_escritas = models.PositiveIntegerField()
    total_tiempo_escritura = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_usuario'


class BookroomapiUsuarioGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING)
    group = models.ForeignKey('AuthGroup', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_usuario_groups'
        unique_together = (('usuario', 'group'),)


class BookroomapiUsuarioUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_usuario_user_permissions'
        unique_together = (('usuario', 'permission'),)


class BookroomapiVoto(models.Model):
    id = models.BigAutoField(primary_key=True)
    puntuacion = models.PositiveSmallIntegerField()
    fecha = models.DateTimeField()
    relato = models.ForeignKey(BookroomapiRelato, models.DO_NOTHING)
    usuario = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'BookRoomAPI_voto'
        unique_together = (('usuario', 'relato'),)


class AccountEmailaddress(models.Model):
    email = models.CharField(max_length=254)
    verified = models.IntegerField()
    primary = models.IntegerField()
    user = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailaddress'
        unique_together = (('user', 'email'),)


class AccountEmailconfirmation(models.Model):
    created = models.DateTimeField()
    sent = models.DateTimeField(blank=True, null=True)
    key = models.CharField(unique=True, max_length=64)
    email_address = models.ForeignKey(AccountEmailaddress, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailconfirmation'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthtokenToken(models.Model):
    key = models.CharField(primary_key=True, max_length=40)
    created = models.DateTimeField()
    user = models.OneToOneField(BookroomapiUsuario, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'authtoken_token'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class Oauth2ProviderAccesstoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.TextField()
    expires = models.DateTimeField()
    scope = models.TextField()
    application = models.ForeignKey('Oauth2ProviderApplication', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING, blank=True, null=True)
    created = models.DateTimeField()
    updated = models.DateTimeField()
    source_refresh_token = models.OneToOneField('Oauth2ProviderRefreshtoken', models.DO_NOTHING, blank=True, null=True)
    id_token = models.OneToOneField('Oauth2ProviderIdtoken', models.DO_NOTHING, blank=True, null=True)
    token_checksum = models.CharField(unique=True, max_length=64)

    class Meta:
        managed = False
        db_table = 'oauth2_provider_accesstoken'


class Oauth2ProviderApplication(models.Model):
    id = models.BigAutoField(primary_key=True)
    client_id = models.CharField(unique=True, max_length=100)
    redirect_uris = models.TextField()
    client_type = models.CharField(max_length=32)
    authorization_grant_type = models.CharField(max_length=32)
    client_secret = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING, blank=True, null=True)
    skip_authorization = models.IntegerField()
    created = models.DateTimeField()
    updated = models.DateTimeField()
    algorithm = models.CharField(max_length=5)
    post_logout_redirect_uris = models.TextField()
    hash_client_secret = models.IntegerField()
    allowed_origins = models.TextField()

    class Meta:
        managed = False
        db_table = 'oauth2_provider_application'


class Oauth2ProviderGrant(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=255)
    expires = models.DateTimeField()
    redirect_uri = models.TextField()
    scope = models.TextField()
    application = models.ForeignKey(Oauth2ProviderApplication, models.DO_NOTHING)
    user = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING)
    created = models.DateTimeField()
    updated = models.DateTimeField()
    code_challenge = models.CharField(max_length=128)
    code_challenge_method = models.CharField(max_length=10)
    nonce = models.CharField(max_length=255)
    claims = models.TextField()

    class Meta:
        managed = False
        db_table = 'oauth2_provider_grant'


class Oauth2ProviderIdtoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    jti = models.CharField(unique=True, max_length=32)
    expires = models.DateTimeField()
    scope = models.TextField()
    created = models.DateTimeField()
    updated = models.DateTimeField()
    application = models.ForeignKey(Oauth2ProviderApplication, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth2_provider_idtoken'


class Oauth2ProviderRefreshtoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.CharField(max_length=255)
    access_token = models.OneToOneField(Oauth2ProviderAccesstoken, models.DO_NOTHING, blank=True, null=True)
    application = models.ForeignKey(Oauth2ProviderApplication, models.DO_NOTHING)
    user = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING)
    created = models.DateTimeField()
    updated = models.DateTimeField()
    revoked = models.DateTimeField(blank=True, null=True)
    token_family = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth2_provider_refreshtoken'
        unique_together = (('token', 'revoked'),)


class SocialaccountSocialaccount(models.Model):
    provider = models.CharField(max_length=200)
    uid = models.CharField(max_length=191)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    extra_data = models.JSONField()
    user = models.ForeignKey(BookroomapiUsuario, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialaccount'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialapp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=191)
    secret = models.CharField(max_length=191)
    key = models.CharField(max_length=191)
    provider_id = models.CharField(max_length=200)
    settings = models.JSONField()

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp'


class SocialaccountSocialappSites(models.Model):
    id = models.BigAutoField(primary_key=True)
    socialapp = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp_sites'
        unique_together = (('socialapp', 'site'),)


class SocialaccountSocialtoken(models.Model):
    token = models.TextField()
    token_secret = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)
    account = models.ForeignKey(SocialaccountSocialaccount, models.DO_NOTHING)
    app = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialtoken'
        unique_together = (('app', 'account'),)
