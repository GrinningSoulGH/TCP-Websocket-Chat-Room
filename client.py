import asyncio, sys, json
from datetime import datetime, date, timezone
from aioconsole import ainput

async def send(writer, data):
    writer.write(data.encode())
    await writer.drain()

async def _message(writer, reader):
    while True:
        text = await ainput()
        print(text)
        if writer.is_closing():
            return
        if text == '':
            print('You can not send an empty message')
        else:
            time = datetime.utcnow().isoformat()[:-3] + 'Z'
            message = dict.fromkeys(['time','text'])
            message['time'] = time
            message['text'] = text
            await send(writer, json.dumps(message))
        

async def _read(writer, reader):
    while True:
        data = await reader.readuntil(b'}')
        if reader.at_eof():
            print('Server Shutdown, press Enter to exit')
            writer.close()
            return
        message = json.loads(data)
        if message['type'] == 'notice':
            print(message['text'])
        else:
            time = datetime.fromisoformat(message['time'][:-1]).replace(tzinfo=timezone.utc).astimezone(tz=None)
            if time.date() != date.today():
                time = time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time = time.strftime("%H:%M:%S")
            if message['type'] == 'forward':
                print(f'[{time}] {message["sender"]}(to You): {message["text"]}')
            else:
                print(f'[{time}] {message["sender"]}: {message["text"]}')

async def main():
    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = sys.argv[2]
    else:
        print('Correct formatting: script name, IP address, port')
        return
    reader, writer = await asyncio.open_connection(ip, port)
    await asyncio.gather(_read(writer, reader), _message(writer, reader))

asyncio.run(main())