from chat_utils.chatdatabase import ChatDatabase

class User:

    def __init__(self, streams, username):
        self.streams = streams
        self.username = username

class ChatRoom:
    
    def __init__(self):
        self.user_list = []
        self.db = ChatDatabase()

    async def start_database_server(self, filename = False):
        await self.db.create_connection(filename)
        await self.db.cursor.execute("PRAGMA foreign_keys = ON;")
        await self.db.cursor.execute('''CREATE TABLE user (
                        username text PRIMARY KEY,
                        password text,
                        last_online text)''')
        await self.db.cursor.execute('''CREATE TABLE message
                        (username text,
                        reciever text,
                        message_text text,
                        date text,
                        FOREIGN KEY(username) REFERENCES user (username))''')
        