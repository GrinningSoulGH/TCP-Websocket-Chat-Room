import asyncio, sys, websockets
from chat_utils.chatroom import ChatRoom
from chat_utils.chat_logic import ChatLogic

class Server:

    def __init__(self):
        self.chatroom = ChatRoom()
        asyncio.get_event_loop().run_until_complete(self.start())
        asyncio.get_event_loop().run_forever()

    async def start(self):
        await self.chatroom.start_database_server()
        await websockets.serve(self.handle, "localhost", 8765)
        await asyncio.start_server(self.handle, '127.0.0.1', 6565)

    async def handle(self, *args):
        streams = ChatLogic(self.chatroom)
        await streams.handle(*args)


server = Server()
server.start()
