import json, asyncio, datetime
from chat_utils.streams_logic import SLogic, WSLogic
from chat_utils.chatroom import User
import chat_utils.json_tools as json_tools


class ChatLogic:
    def __init__(self, chatroom):
        self.chatroom = chatroom

    async def send_server_message(self, data):
        message = json_tools.make_message(data)
        json_tools.update_type(message, 'notice')
        await self.streams.write(json.dumps(message))

    async def get_user_log(self,user):
        for u in self.chatroom.user_list:
            await user.streams.add(u)
   
    async def user_join(self, user):
        for u in self.chatroom.user_list:
            await u.streams.add(user)

    async def user_leave(self, user):
        for u in self.chatroom.user_list:
            await u.streams.leave(user)
                  
    async def handle(self, *args):
        if isinstance(args[0], asyncio.streams.StreamReader):
            self.streams = SLogic(args[0], args[1])
        else:
            self.streams = WSLogic(args[0])
        username = await self.join()
        if username:
            user = User(self.streams, username)
        else:
            return
        await self.get_user_log(user)
        self.chatroom.add(user)
        await self.user_join(user)
        while True:
            data = await self.streams.read()
            if not data:
                await self.end_user_session(user)
                return
            await self.send_message(user, json.loads(data))

    async def login(self, username):
        await self.send_server_message('Input your password:')
        while True:
            json_password = await self.streams.read()
            if not json_password:
                return
            password = json_tools.get_value(json_password, 'text')
            if await self.chatroom.db.check_password(username, password):
                message_log = await self.chatroom.db.get_message_log(username)
                if message_log != 'Empty':
                    for message in message_log:
                        if message[1] == "broadcast":
                            await self.streams.write(json.dumps(json_tools.make_message(message[3], message[0], 'broadcast', datetime.datetime.strptime(message[2], "%Y-%m-%d %H:%M:%S").isoformat() + 'Z')))
                        elif message[1] == username:
                            await self.streams.write(json.dumps(json_tools.make_message(message[3], message[0], 'forward', datetime.datetime.strptime(message[2], "%Y-%m-%d %H:%M:%S").isoformat() + 'Z')))
                return username
            await self.send_server_message('Incorrect password') 

    async def register(self, username):
        await self.send_server_message('Username is available')
        await self.send_server_message('Set your password (max 255 characters):')
        json_password = await self.streams.read()
        if not json_password:
            return
        password = json_tools.get_value(json_password, 'text')
        await self.chatroom.db.add_new_user(username, password) 
        return username

    async def join(self):
        await self.send_server_message('Enter your username(no spaces):')
        while True:
            json_username = await self.streams.read()
            if not json_username:
                return
            username = json_tools.get_value(json_username, 'text')
            if len(username) < 20 and len(username.split()) == 1:
                if username not in await self.chatroom.db.get_user_log(): # Новый пользователь
                    return await self.register(username)
                else: # Существующий пользователь
                    if username in [u.username for u in self.chatroom.user_list]:
                        await self.send_server_message('This user has already logged in')
                    else:
                        return await self.login(username)
            else:
                await self.send_server_message('Incorrect username')    

    async def forward(self, sender, reciever_username, message):
        if reciever_username in await self.chatroom.db.get_user_log():
            json_tools.update_type(message, 'forward')
            await self.chatroom.db.add_message(sender.username, reciever_username, message)
            for u in self.chatroom.user_list:
                if u.username == reciever_username:
                    await u.streams.write(json.dumps(message))
        else:
            await self.send_server_message('No user found')     

    
    async def broadcast(self, sender, message):
        json_tools.update_type(message, 'broadcast')  
        await self.chatroom.db.add_message(sender.username, 'broadcast', message)
        for u in self.chatroom.user_list:
            await u.streams.write(json.dumps(message))

    async def send_message(self, user, message):
        message.update({'sender': user.username})
        if message['text'].split()[0] == '/w':
            reciever_username = message['text'].split()[1]
            message['text'] = message['text'].split(maxsplit = 2)[2]
            await self.forward(user, reciever_username, message)
        else:
            await self.broadcast(user, message)

    async def end_user_session(self, user):
        await self.chatroom.db.update_last_online(user)
        self.chatroom.user_list.remove(user)
        await self.user_leave(user)
        user.streams.close()
