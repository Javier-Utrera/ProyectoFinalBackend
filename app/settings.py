import os
from pathlib import Path
import environ
import cloudinary

# ─── 1) BASE_DIR y carga de .env ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost"]),
)
env.read_env(os.path.join(BASE_DIR, '.env'))


# ─── 2) SECURITY ───────────────────────────────────────────────────────────────
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS')


# ─── 3) INSTALLED_APPS ─────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST framework y filtros
    'rest_framework',
    'django_filters',
    'corsheaders',

    # OAuth2 provider (django-oauth-toolkit)
    'oauth2_provider',

    # Autenticación basada en tokens
    'rest_framework.authtoken',
    'dj_rest_auth',

    # Documentación automática
    'drf_yasg',

    # WebSockets / Channels
    'channels',

    # Cloudinary (para subir imágenes)
    'cloudinary',
    'cloudinary_storage',

    # Mi aplicación principal
    'BookRoomAPI',
]


# ─── 4) MIDDLEWARE ─────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ─── 5) URLS y ASGI/WSGI ────────────────────────────────────────────────────────
ROOT_URLCONF = 'app.urls'
ASGI_APPLICATION = 'app.asgi.application'
WSGI_APPLICATION = 'app.wsgi.application'


# ─── 6) TEMPLATES (Solo para la admin y drf_yasg, no hay plantillas propias) ───
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ─── 7) BASE DATOS ──────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('MYSQL_DB'),
        'USER': env('MYSQL_USER'),
        'PASSWORD': env('MYSQL_PASSWORD'),
        'HOST': env('MYSQL_HOST'),
        'PORT': env('MYSQL_PORT'),
    }
}


# ─── 8) VALIDACIÓN DE CONTRASEÑAS ───────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─── 9) INTERNACIONALIZACIÓN ───────────────────────────────────────────────────
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True


# ─── 10) ARCHIVOS ESTÁTICOS Y MEDIA ─────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Cloudinary para archivos subidos (imágenes, etc.)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'RESOURCE_TYPE': 'image',
    'FOLDER': 'avatars',
}


# ─── 11) CORS ────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')


# ─── 12) DJANGO REST FRAMEWORK ─────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5,
}


# ─── 13) MODELO DE USUARIO (personalizado) ─────────────────────────────────────
AUTH_USER_MODEL = 'BookRoomAPI.Usuario'


# ─── 14) CONFIG. DE DJ-OAUTH-TOOLKIT ────────────────────────────────────────────
OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': 36000000,
    'SCOPES': {'read': 'Leer', 'write': 'Escribir'},
}


# ─── 16) DRF-YASG (Swagger) ────────────────────────────────────────────────────
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "Pega tu token: 'Bearer <tu_token>'",
        },
    },
    'DEFAULT_SECURITY': [{'Bearer': []}],
}


# ─── 17) CHANNELS ──────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}


# ─── 18) CLOUDINARY (configuración de credenciales) ────────────────────────────
cloudinary.config(
    cloud_name=env('CLOUDINARY_CLOUD_NAME'),
    api_key=env('CLOUDINARY_API_KEY'),
    api_secret=env('CLOUDINARY_API_SECRET'),
    secure=True,
)

# ─── 19) PAYPAL (configuración de credenciales) ────────────────────────────────
PAYPAL_CLIENT_ID = env('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = env('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = env('PAYPAL_MODE')  # 'sandbox' (dinero de mentira)
