import json
import datetime

def update_type(jsonMessage, _type):
    return jsonMessage.update({'type': _type})
       
def get_value(jsonMessage, key):
    return json.loads(jsonMessage)[key]

def make_message(data, sender = 'default', _type = 'default', time = None):
    if time is None:
        time = datetime.datetime.now().isoformat()[:-3] + 'Z'
    message = dict.fromkeys(['type','text', 'time', 'sender'])
    message['type'] = _type
    message['text'] = data
    message['time'] = time
    message['sender'] = sender
    return message