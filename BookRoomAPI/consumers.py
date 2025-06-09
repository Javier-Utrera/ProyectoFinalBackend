from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
import asyncio
import json
from channels.db import database_sync_to_async
from .models import Relato, Mensaje
from django.shortcuts import get_object_or_404

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "¡Conexión WebSocket operativa!"}))

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({"echo": data}))

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("[ChatConsumer] Conectando...")
        # 1) Extraer relato_id de la URL y definir grupo
        self.relato_id = self.scope['url_route']['kwargs']['relato_id']
        self.group_name = f"chat_relato_{self.relato_id}"

        # 2) Validar que el usuario sea colaborador
        user = self.scope['user']
        relato = await database_sync_to_async(get_object_or_404)(Relato, id=self.relato_id)
        es_colab = await database_sync_to_async(
            lambda: relato.autores.filter(id=user.id).exists()
        )()
        if not es_colab:
            return await self.close()

        # 3) Añadir al grupo y aceptar conexión
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Quitar del grupo
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # 1) Parsear y limpiar
        data = json.loads(text_data)
        texto = data.get('texto', '').strip()
        if not texto:
            return  # ignorar vacíos

        # 2) Guardar en BD
        user = self.scope['user']
        try:
            mensaje = await database_sync_to_async(Mensaje.objects.create)(
                autor=user,
                relato_id=self.relato_id,
                texto=texto
            )
            print(f"[ChatConsumer] → Mensaje guardado con id={mensaje.id}")
        except Exception as e:
            print(f"[ChatConsumer] ERROR al guardar: {e}")
            return

        # 3) Difundir al grupo
        payload = {
            'type': 'chat.message',            # invoca chat_message()
            'id': mensaje.id,
            'autor': user.username,
            'texto': mensaje.texto,
            'fecha_envio': mensaje.fecha_envio.isoformat(),
        }
        await self.channel_layer.group_send(self.group_name, payload)

    async def chat_message(self, event):
        # Reenvía el evento JSON a cada cliente
        await self.send(text_data=json.dumps({
            'id': event['id'],
            'autor': event['autor'],
            'texto': event['texto'],
            'fecha_envio': event['fecha_envio'],
        }))
