# The Book Room APIREST

Este repositorio contiene el backend de la aplicación **The Book Room**, desarrollado con Django y Django REST Framework. Proporciona una API REST para registro, autenticación, gestión de perfil de usuario, relatos colaborativos...

---

## Configuración inicial

Antes de ejecutar el proyecto, recuerda crear un archivo `.env` a partir del archivo `.env.example` y completarlo con tus credenciales.

---

## Documentación interactiva

La API incluye documentación auto-generada accesible desde:

- [http://localhost:8000/swagger/](http://localhost:8000/swagger/) → Swagger UI
- [http://localhost:8000/redoc/](http://localhost:8000/redoc/) → ReDoc

### Autenticarse en Swagger con Bearer Token

1. Accede a la documentación Swagger.
2. Realiza login en `POST /api/login/` enviando tu `username` y `password`.
3. Copia el `access_token` que recibas.
4. Haz clic en **Authorize** en Swagger.
5. Pega el token así: `Bearer <tu_token>`.

---

## Modelo de usuario

### `Usuario`

Extiende `AbstractUser` e incluye:

- Rol (`ADMINISTRADOR` o `CLIENTE`)
- Biografía, avatar, fecha de nacimiento, país, ciudad
- Géneros favoritos (formato: texto separado por comas)
- Métricas de actividad: relatos publicados, votos recibidos, palabras escritas, tiempo de escritura

También implementa métodos útiles como:
- `relatos_publicados()`, `relatos_en_proceso()`, `has_votado(relato)`
- Gestión de amistades

---

## Autenticación y sesión con OAuth2

La API utiliza `django-oauth-toolkit` para autenticación con tokens OAuth2.

### Flujo

1. Registro: `POST /api/registro/`
2. Login: `POST /api/login/`
3. El backend devuelve un `access_token` válido por 10 horas
4. El frontend guarda el token en `localStorage`
5. Las peticiones protegidas deben incluir el token como **Bearer**

### Reutilización de tokens

- Si el usuario ya tiene un token válido, se reutiliza.
- Si no, se genera uno nuevo.

### Logout

- `POST /api/logout/`
- Elimina el token activo y cierra la sesión del usuario (Elimino el token de la base de datos, cuando haga login se creara un token nuevo).

### Control de sesión

- `GET /api/perfil/` devuelve los datos del usuario autenticado.
- Lo uso para mantener la sesión activa y mostrar perfil en frontend.

---

## Endpoints principales

### Registro de usuario

`POST /api/registro/`

- Crea un nuevo usuario con rol `CLIENTE`
- Genera automáticamente un token OAuth2
- Añade al grupo "Clientes" si existe

### Login

`POST /api/login/`

- Requiere `username` y `password`
- Devuelve:
  ```json
  {
    "access_token": "abc123...",
    "user": { ... }
  }
  ```

### Logout

`POST /api/logout/`

- Elimina el token activo

### Perfil

`GET /api/perfil/` → obtener datos del usuario autenticado  
`PATCH /api/perfil/` → editar campos: biografía, país, ciudad, géneros favoritos, etc.

### Obtener usuario por token

`GET /api/token/usuario/<token>/`

- Devuelve datos del usuario asociado a ese token

---

## Endpoints de relatos

Todos los endpoints de relatos requieren autenticación **excepto** los públicos.

### Listar relatos publicados (público)

`GET /api/relatos/publicados/`

- Devuelve relatos en estado `PUBLICADO`.

### Listar relatos del usuario

`GET /api/relatos/`

- Devuelve relatos donde el usuario participa.

### Crear relato

`POST /api/relatos/crear/`

- Crea un nuevo relato con `titulo`, `descripcion`, `idioma`, `contenido` y `num_escritores`
- El creador se convierte en el primer participante automáticamente

### Ver relatos abiertos (público)

`GET /api/relatos/abiertos/`

- Devuelve relatos con estado `CREACION` y que aún admiten más escritores.

### Unirse a relato

`POST /api/relatos/<id>/unirse/`

- Permite unirse a relatos abiertos

### Editar relato

`PUT/PATCH /api/relatos/<id>/editar/`

- Solo si el usuario es colaborador del relato

### Eliminar relato

`DELETE /api/relatos/<id>/eliminar/`

- Solo posible si el usuario es el único colaborador

### Marcar relato como listo

`POST /api/relatos/<id>/marcar-listo/`

- Marca al usuario como listo para publicar
- Si todos los autores están listos, el relato cambia a estado `PUBLICADO`

---
## Endpoints de gestión de amigos

La API permite a los usuarios autenticados enviar solicitudes de amistad, aceptarlas, bloquearlas y eliminarlas.

### Enviar solicitud de amistad

`POST /api/amigos/enviar/`

- Envia una solicitud a otro usuario (requiere `a_usuario` en el cuerpo).
- No se permite enviar solicitudes a uno mismo ni duplicadas.

### Ver solicitudes recibidas

`GET /api/amigos/recibidas/`

- Devuelve una lista de solicitudes pendientes que ha recibido el usuario actual.

### Aceptar solicitud

`POST /api/amigos/aceptar/<solicitud_id>/`

- Acepta una solicitud recibida (solo el destinatario puede hacerlo).

### Bloquear solicitud

`POST /api/amigos/bloquear/<solicitud_id>/`

- Bloquea una solicitud de amistad en estado `PENDIENTE`.

### Ver amigos

`GET /api/amigos/`

- Lista todos los usuarios con los que el usuario tiene una amistad aceptada.

### Ver solicitudes enviadas

`GET /api/amigos/enviadas/`

- Devuelve todas las solicitudes enviadas por el usuario que aún están pendientes.

### Eliminar amigo

`DELETE /api/amigos/eliminar/<usuario_id>/`

- Elimina una relación de amistad aceptada con otro usuario.

---

## Serializadores principales

### `UsuarioSerializerRegistro`

- Para `POST /api/registro/`
- Valida campos: username, email, contraseñas

### `UsuarioSerializer`

- Para mostrar datos de usuario (login, perfil, etc.)

### `UsuarioUpdateSerializer`

- Para editar perfil (biografía, fecha, país, ciudad, géneros favoritos)
        return self.validar_campo_texto(value, "ciudad")
- Incluye validaciones : biografia,fecha_nacimiento,país,generos_favoritos

### `RelatoSerializer`

- Devuelve detalles de relato, incluyendo autores

### `RelatoCreateSerializer`

- Para crear un nuevo relato
- Valida título, descripción y número de escritores

### `RelatoUpdateSerializer`

- Para editar relatos existentes
- Valido de momento el estado

### `UsuarioAmigoSerializer`

- Devuelve detalles de un usuario optimizado para listar en amigos

### `PeticionAmistadSerializer`

- Devuelve detalles de las peticiones de amistad

---

## Sistema de permisos

```python
class EsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == Usuario.ADMINISTRADOR

class EsCliente(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == Usuario.CLIENTE
```

Las aplico en las vistas con:

```python
@permission_classes([IsAuthenticated, EsCliente])
```

---

## CORS y Seguridad

- CORS configurado para permitir peticiones desde Angular en:
  - `http://localhost:4200`
  - `http://127.0.0.1:4200`
- Los tokens expiran a las 10 horas.
- Solo usuarios autenticados pueden acceder a rutas protegidas.

---

## Estructura del proyecto

- `models.py`: Modelos de usuario, relato y participación
- `serializers.py`: Validación y transformación de datos
- `views.py`: Lógica de negocio y endpoints
- `urls.py`: Definición de rutas API
- `permissions.py`: Reglas de acceso según rol

---


## Funcionalidades en tiempo real con WebSockets

El backend incluye soporte para comunicación en tiempo real mediante WebSockets, usando **Django Channels** y el servidor ASGI **Daphne**.

### Tecnologías usadas

- `channels` (manejo de WebSocket)
- `daphne` (servidor ASGI)
- `AsyncWebsocketConsumer` para manejar conexiones

---

### Ruta de prueba WebSocket

Se ha creado una ruta WebSocket de prueba accesible en: ws://localhost:8000/ws/test/

Esta ruta permite enviar y recibir mensajes en tiempo real.

#### Comportamiento:

1. Al conectarse, el servidor responde con:
  { "message": "¡Conexión WebSocket establecida!" }

2. Cualquier mensaje que se envíe será devuelto como un "eco":
  { "message": "Echo: tu mensaje aquí" }

### Archivos añadidos

- BookRoomAPI/routing.py: Define rutas WebSocket.
- BookRoomAPI/consumers.py: Contiene el consumidor TestConsumer.
- asgi.py: Ahora usa ProtocolTypeRouter para manejar tanto HTTP como WebSocket.

