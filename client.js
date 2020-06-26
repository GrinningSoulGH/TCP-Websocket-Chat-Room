let sock = new WebSocket("ws://127.0.0.1:8765/");
let messages = document.createElement('ul');
messages.classList.add('messages');
let userLog = document.createElement('ul');
userLog.classList.add('userLog');
document.body.appendChild(messages);
document.body.appendChild(userLog);
sock.onmessage = function (event) {
    let dataContents = JSON.parse(event.data);
    let messageText = '';
    let time = '';
    if (dataContents.type === 'userLog'){
        if (dataContents.text.slice(-1) === '+'){
            userEntry = document.createElement('li');
            username = dataContents.text.slice(0,-1);
            userEntry.setAttribute('id', username);
            content = document.createTextNode(username);
            userEntry.appendChild(content);
            userLog.appendChild(userEntry);
        }
        else{
            userEntry = document.getElementById(dataContents.text.slice(0,-1))
            userLog.removeChild(userEntry);
        }
    }
    else{
        let message = document.createElement('li');
        if (dataContents.type !== 'notice'){
            let messageTime = Date.parse(dataContents.time);
            if (new Date(messageTime).setHours(0,0,0,0) === new Date().setHours(0,0,0,0)){
                time = new Date(messageTime).toLocaleTimeString();
            }
            else{
                time = new Date(messageTime).toLocaleString();
            }
            if (dataContents.type === 'broadcast'){
                messageText = `[${time}] ${dataContents.sender}: ${dataContents.text}`;
                message.classList.add('broadcast')
            }
            else{
                messageText = `[${time}] ${dataContents.sender}(to You): ${dataContents.text}`
                message.classList.add('forward')
            }
        }
        else{
            messageText = `${dataContents.text}`
            message.classList.add('notice')
        }
            content = document.createTextNode(messageText);
            message.appendChild(content);
            messages.appendChild(message);
    };
}
      

function sendMessage(){
    let timeobj = new Date();
    let msgbox = document.getElementById('messagetext');
    let message = {
        time: timeobj.toISOString(),
        text: msgbox.value
    };
    sock.send(JSON.stringify(message));
    msgbox.value = ''
}

    