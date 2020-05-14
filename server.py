import asyncio, sys, datetime, websockets
from chat_utils.chatdatabase import ChatDatabase
from chat_utils.chatroom import ChatRoom
from chat_utils.chatroom import User

class SLogic:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def read(self):
        data = (await self.reader.read(255)).decode()
        if not self.reader.at_eof():
            return data
        else:
            return False

    async def write(self, data):
        self.writer.write(data.encode())
        await self.writer.drain()

    def close(self):
        self.writer.close()

class WSLogic:
    def __init__(self, websocket):
        self.websocket = websocket
    
    async def read(self):
        try:
            data = await self.websocket.recv()
        except websockets.exceptions.ConnectionClosedOK:
            return False
        else:
            return data

    async def write(self, data):
        await self.websocket.send(data)

    def close(self):
        pass

class IOStreams:
    def __init__(self, *args):
        if isinstance(args[0], asyncio.streams.StreamReader):
            self.streams = SLogic(args[0], args[1])
        else:
            self.streams = WSLogic(args[0])
        self.user_list = chatroom.user_list
        self.db = chatroom.db
        
    async def handle(self):
        username = await self.login()
        if username:
            user = User(self.streams, username)
        else:
            return
        self.add(user)
        await self.db.get_message_log(user)
        message = f"{user.username!s} is connected !!!!\n"
        await self.broadcast(user, message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        while True:
            data = await self.streams.read()
            if not data:
                await self.end_user_session(user)
                return
            await self.send_message(user, data)

    async def login(self):
        while True:
            username = await self.streams.read()
            if not username:
                return False
            if username not in await self.db.get_user_log(): # Новый пользователь
                await self.streams.write('1') # Код для клиента о том, что создание нового пользователя прошло успешно
                password = await self.streams.read()
                if not password:
                    return False
                await self.db.add_new_user(username, password) # Ожидаем ввод пароля   
                return username
            else: # Существующий пользователь
                if username in [u.username for u in self.user_list]:
                    await self.streams.write('2') #Код для клиента о том, что пользователь уже онлайн
                else:
                    await self.streams.write('3') # Код для клиента о том, что пользователь уже существует, в клиенте запрашивается пароль
                    while True:
                        password = await self.streams.read()
                        if not password:
                            return False
                        if await self.db.check_password(username, password):
                            await self.streams.write('1') # Пароль верный
                            return username
                        await self.streams.write('0') # Пароль неверный      

    def add(self, user):
        self.user_list.append(user)

    async def forward(self, sender, reciever_username, message, date):
        is_message = False
        if reciever_username in await self.db.get_user_log():
            await self.db.add_message(sender.username, reciever_username, message, date)
            is_message = True
        for u in self.user_list:
            if u.username == reciever_username:
                u.streams.write(f"[{date}]{sender.username!s}(to you): {message!s}")
        if is_message == False:
            sender.streams.write('No user found\n')     

    
    async def broadcast(self, sender, message, date):
        await self.db.add_message(sender.username, 'broadcast', message, date)
        for u in self.user_list:
            if u.username != sender.username:
                await u.streams.write(f"[{date}]{sender.username!s}: {message!s}")

    async def send_message(self, user, data):
        date = data.split()[0] + ' ' + data.split()[1]
        message = data.split(maxsplit = 2)[2]
        if message.split()[0] == '/w':
            reciever_username = message.split()[1]
            message_text = message.split(maxsplit = 2)[2]
            await self.forward(user, reciever_username, message_text, date)
        else:
            await self.broadcast(user, message, date)

    async def end_user_session(self, user):
        await self.db.update_last_online(user)
        self.user_list.remove(user)
        user.streams.close()


async def sockethandle(reader, writer):
    print(type(reader))
    streams = IOStreams(reader, writer)
    await streams.handle()

async def websockethandle(websocket, path):
    print(type(websocket))
    streams = IOStreams(websocket)
    await streams.handle()

async def main():
    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = sys.argv[2]
    else:
        print('Correct formatting: script name, IP address, port')
        return
    await chatroom.start_database_server()
    w_server = await websockets.serve(websockethandle, "localhost", 8765)
    server = await asyncio.start_server(sockethandle, ip, port)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr!s}')
    await server.start_serving()

chatroom = ChatRoom()

asyncio.get_event_loop().run_until_complete(main())
asyncio.get_event_loop().run_forever()