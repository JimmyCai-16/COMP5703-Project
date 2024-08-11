import json
import math
from http import HTTPStatus

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count, Case, When, IntegerField, Q, Sum, F
from django.template.loader import get_template

from notification.models import Notification, NotificationStatus
from project.models import Project


class KMSBaseConsumer(AsyncWebsocketConsumer):
    """Async WebSocket Consumer for the Knowledge Management System. Each instance of KMSProject has its own group,
    where all members of the group are those with active connections."""
    user = None
    group_name = None
    group_users = {}

    def set_group_name(self):
        pass

    async def connect(self):
        self.user = self.scope['user']

        # Only let authenticated users connect to this websocket
        if self.user.is_authenticated:
            self.set_group_name()

            # Broadcast to other users that this user has connected
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user_connected',
                    'user': {'email': self.user.email, 'name': self.user.full_name},
                }
            )

            # Add the user to connected users set
            if self.group_name not in self.group_users:
                self.group_users[self.group_name] = []

            self.group_users[self.group_name].append(self.user)

            # Join the project channel group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

            # Send currently connected users to the connecting user
            await self.send_connected_users()
        else:
            await self.close()

    async def disconnect(self, code):
        # Authenticated users should be removed from the group
        if self.user.is_authenticated:
            # Remove the user from the connected users set
            if self.group_name in self.group_users:
                self.group_users[self.group_name].remove(self.user)

                # Delete the set if it is empty
                if len(self.group_users[self.group_name]) < 1:
                    del self.group_users[self.group_name]

            # Broadcast to other users that this user has disconnected
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user_disconnected',
                    'user': {'email': self.user.email, 'name': self.user.full_name},
                }
            )

            # Leave the channel group
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_connected_users(self):
        """Sends a list of all currently connected users to the current user"""
        # TODO: Discuss whether this is worthwhile/useful
        connected_users = self.group_users[self.group_name]

        await self.send(text_data=json.dumps({
            'event': 'current_users',
            'users': [{'email': user.email, 'name': user.full_name} for user in connected_users if user != self.user]
        }))

    async def user_connected(self, event):
        """When a user connects to the socket, let all the other users in the group know"""
        # TODO: Discuss whether this is worthwhile/useful
        await self.send(text_data=json.dumps({
            'event': 'user_connected',
            'user': event['user']
        }))

    async def user_disconnected(self, event):
        """When a user connects to the socket, let all the other users in the group know"""
        # TODO: Discuss whether this is worthwhile/useful
        await self.send(text_data=json.dumps({
            'event': 'user_disconnected',
            'user': event['user']
        }))


class ProjectPage(KMSBaseConsumer):
    def set_group_name(self):

        project_slug = self.scope['url_route']['kwargs']['slug']

        self.group_name = f"kms-project-page-{project_slug}"

    async def receive(self, text_data=None, bytes_data=None):
        # Exit early if they're not authenticated and close their connection
        if not self.user.is_authenticated:
            return

        # Receiving a message from the user
        data = json.loads(text_data)
        action = data.get('action', None)
        event = {}

        # Assign the message content
        if action == 'active_element':
            # Send the active element to each of the other users
            event = {
                'type': 'send_active_element',
                'user': self.user.email,
                'active_element': data.get('active_element'),
            }

        elif action == 'cursor_position':
            # Send users cursor position to other users
            event = {
                'type': 'send_cursor_position',
                'user': self.user.email,
                'x': data.get('x'),
                'y': data.get('y'),
            }

        # Send the content if it exists
        if event:
            # For keeping track of who sent the message
            event["sender_channel_name"] = self.channel_name

            await self.channel_layer.group_send(self.group_name, event)

    async def send_field_content(self, event):
        """Used to update an HTML element with new content."""
        if self.user != event.get('user'):
            await self.send(
                text_data=json.dumps(
                    {
                        'event': 'field_content',
                        'element': event.get('element'),  # HTML element ID
                        'content': event.get('content'),  # Content
                    }
                )
            )

    async def send_model_instance(self, event):
        """Used to update an HTML element with new content."""
        if self.user != event.get('user'):
            await self.send(
                text_data=json.dumps(
                    {
                        'event': 'model_content',
                        'mode': event.get('mode'),
                        'model': event.get('model'),  # HTML element ID
                        'instance': event.get('instance'),  # Content
                    }
                )
            )

    async def send_active_element(self, event):
        """Sends the users current active element to other users in the group."""
        # TODO: Wasn't really used for anything in particular. Just for testing purposes.
        #  Remove if not required for launch
        await self.send(text_data=json.dumps({
            'user': event.get('user'),
            'active_element': event.get('active_element'),
        })
        )

    async def send_cursor_position(self, event):
        """Sends the users current cursor position to all users in the group."""
        # TODO: This was just for mouse tracking in case we want to draw other users cursors on the screen.
        #   Remove if not required for launch
        sender_channel_name = event.get('sender_channel_name')

        if sender_channel_name != self.channel_name:
            await self.send(text_data=json.dumps({
                'user': event.get('user'),
                'x': event.get('x'),
                'y': event.get('y'),
            })
            )


class ProspectPage(ProjectPage):
    def set_group_name(self):
        project_slug = self.scope['url_route']['kwargs']['slug']
        prospect_id = self.scope['url_route']['kwargs']['prospect']

        self.group_name = f"kms-prospect-page-{project_slug}-{prospect_id}"
