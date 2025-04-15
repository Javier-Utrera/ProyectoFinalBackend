# https-github.com-Javier-Utrera-ProyectoFinalBackend

Recuerda crear un archivo `.env` a partir de `.env.example` y completarlo con tus credenciales antes de iniciar el proyecto.

## Modelos

La API utiliza un modelo de usuario personalizado y un perfil de cliente para almacenar información personal y literaria.

---

### Usuario (`Usuario`)

Este modelo hereda de `AbstractUser` y añade un campo adicional para el rol del usuario:

```python
class Usuario(AbstractUser):
    ADMINISTRADOR = 1
    CLIENTE = 2

    ROLES = (
        (ADMINISTRADOR, "administrador"),
        (CLIENTE, "cliente")
    )

    rol = models.PositiveSmallIntegerField(choices=ROLES, default=CLIENTE)
```

### Perfil de Cliente (`PerfilCliente`)

El modelo `PerfilCliente` está diseñado para almacenar la información personal y literaria de los usuarios registrados como **clientes** en la plataforma.

Está vinculado al modelo `Usuario` mediante una relación uno a uno (`OneToOneField`), lo que permite extender el perfil sin modificar directamente el modelo de autenticación.

```python
class PerfilCliente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil')
```
------------------------------------------------------------------------

## Views.py

Las vistas actuales implementan: lógica de registro, login, logout ,consulta de sesión mediante OAuth2,

### Registro de usuario (`POST /api/registro/`)

Permite registrar un nuevo usuario de tipo cliente. Incluye validaciones personalizadas para `username`, `email` y coincidencia de contraseñas. Al crear el usuario:

- Se le asigna automáticamente el rol `CLIENTE`.
- Se crea su objeto `PerfilCliente` vinculado.
- Se añade al grupo `Clientes`.

---

### Login (`POST /api/token/`)

Autentica al usuario y devuelve un token OAuth2. Si ya existe un token válido, se reutiliza. En caso contrario, se genera uno nuevo. La respuesta incluye:

- `access_token`
- Datos del usuario autenticado

---

### Logout (`POST /api/logout/`)

Elimina el token actual del usuario autenticado, cerrando su sesión de forma segura. Requiere autenticación mediante token.

---

### Obtener perfil de sesión (`GET /api/perfil/`)

Devuelve los datos del usuario actualmente autenticado, junto con la información de su `PerfilCliente`. Este endpoint permite al frontend verificar si el usuario está logueado y mostrar su información.

---

### Obtener usuario desde token (`GET /api/token/usuario/<token>/`)

Permite obtener la información de un usuario a partir de un token OAuth2 específico.

------------------------------------------------------------------------

## Serializadores (`serializers.py`)

Los serializadores se utilizan para validar datos de entrada y estructurar las respuestas JSON de los modelos: 

`Usuario` , `PerfilCliente`,

---

### UsuarioSerializerRegistro

Usado para registrar nuevos usuarios. Incluye validaciones personalizadas para:
- Username único y mínimo de caracteres
- Email obligatorio y único
- Coincidencia de contraseñas (`password1` y `password2`)

Se utiliza en el endpoint `POST /api/registro/`.

---

### UsuarioSerializer

Serializador simple de lectura que devuelve los campos básicos del modelo `Usuario`:
- `id`, `username`, `email`, `rol`

Se utiliza para devolver los datos de usuario autenticado, como en el login o en `obtener_usuario_por_token`.

---

### PerfilClienteSerializer

Serializa los campos del perfil del cliente (`PerfilCliente`), excluyendo la relación con el usuario. Se utiliza para anidar la información del perfil en respuestas del usuario.

---

### UsuarioConPerfilSerializer

Serializador que combina:
- Datos del modelo `Usuario`
- Datos del modelo `PerfilCliente`

Se utiliza en el endpoint `/api/perfil/` para mostrar la sesión activa.

------------------------------------------------------------------------

## Autenticación y sesión con OAuth2

El sistema de autenticación está basado en tokens OAuth2 usando el paquete `django-oauth-toolkit`

---

### Flujo de autenticación

1. El usuario se registra mediante `POST /api/registro/`
2. Luego se loguea mediante `POST /api/token/`, enviando su `username` y `password`
3. El servidor devuelve un `access_token` OAuth2
4. El frontend guarda el token en `localStorage`
5. En cada petición protegida, el frontend incluye:

---

#### Reutilización de tokens

Para evitar duplicación innecesaria de tokens, el backend:

- Revisa si el usuario ya tiene un token activo (no expirado)
- Si existe, lo reutiliza
- Si no, genera uno nuevo con una duración de 10 horas

---

#### Logout

El endpoint `POST /api/logout/` permite al usuario autenticado cerrar su sesión eliminando el token actual del backend. Esto garantiza que el token no pueda reutilizarse aunque el frontend lo conserve.

---

#### Control de sesión

Se implementa un endpoint `GET /api/perfil/` que:

- Requiere un token válido
- Devuelve los datos del usuario autenticado junto a su perfil cliente
- Permite al frontend validar si la sesión sigue activa al recargar

### Configuración

El backend está configurado para usar:

- OAuth2Authentication como clase de autenticación por defecto

- IsAuthenticatedOrReadOnly como clase de permisos base

Los tokens se configuran con una duración de 10 horas

El CORS permite peticiones desde Angular en http://localhost:4200 y http://127.0.0.1:4200,

### Seguridad
- El login requiere nombre de usuario y contraseña válidos
- Todo acceso a endpoints protegidos requiere un token válido