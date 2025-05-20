#!/bin/bash
set -e

# Carga variables de .env si las necesitas
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Fuerza el settings correcto
export DJANGO_SETTINGS_MODULE=app.settings

echo "🧹 Recolectando estáticos..."
python manage.py collectstatic --noinput

echo "✅ Estáticos listos. Arrancando Daphne..."
exec daphne -b 0.0.0.0 -p 8000 app.asgi:application
