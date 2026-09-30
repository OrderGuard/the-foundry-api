

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class OrderConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_name = "orders"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"message": "✅ Connected to order updates"})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        # Optional: handle client pings or filters
        pass

    async def order_update(self, event):
        """Receive order updates from backend"""
        await self.send_json({
            "type": "order_update",
            "order": event["order"],
        })

