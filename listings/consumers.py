import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message, Listing

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        #joins chat room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    #Receivse message via WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_username = self.scope["user"].username
        receiver_id = text_data_json['receiver_id']
        listing_id = text_data_json.get('listing_id')

        # Saves to database
        await self.save_message(sender_username, receiver_id, message, listing_id)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_username
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    @database_sync_to_async
    def save_message(self, sender_username, receiver_id, message_text, listing_id):
        sender = User.objects.get(username=sender_username)
        receiver = User.objects.get(id=receiver_id)
        
        listing = None
        if listing_id:
            listing = Listing.objects.get(id=listing_id)
            
        Message.objects.create(
            sender=sender,
            receiver=receiver,
            listing=listing,
            message_text=message_text
        )