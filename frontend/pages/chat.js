import React, { useState, useEffect } from 'react';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import ChatBox from '../components/ChatBox';

const client = new W3CWebSocket('ws://127.0.0.1:8000/ws');


const Chat = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");

    useEffect(() => {
        let currentId = null;
        client.onopen = () => {
            console.log('WebSocket Client Connected');
        };
        client.onmessage = (message) => {
            const messageData = JSON.parse(message.data);
            // console.log(message.data);
            const id = messageData.id;
            const content = messageData.content;
            if (id != currentId) {
                setMessages(prevMessages => [...prevMessages, { text: content, user: 'ai' }]);
                currentId = id;
            } else {
                setMessages(prevMessages => {
                    const lastMessage = { ...prevMessages[prevMessages.length - 1] };
                    lastMessage.text = lastMessage.text + content;
                    return [...prevMessages.slice(0, prevMessages.length - 1), lastMessage];
                })
            }
        };
    }, []);


    const submitMessage = async () => {
        // Add the user's message to the chat
        setMessages((prevMessages) => [...prevMessages, { text: input, user: 'human' }]);
        console.log(input);
        setInput("");

        client.send(JSON.stringify({
            input: input,
        }));

    };

    return (
        <div className="flex flex-col bg-gray-800 h-screen">
            <div className="p-4 h-1/8">
                <h1 className="text-4xl font-bold text-center text-dark-secondary">CodeGPT</h1>
            </div>

            <ChatBox messages={messages} />


            <div className="input-area bg-gray-700 text-center fixed bottom-0 w-full h-1/4 text-black">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type a message..."
                    className="p-2 rounded mr-2 w-1/2"
                />
                <button onClick={submitMessage} className="bg-blue-500 text-white p-2 rounded">Send</button>
            </div>
        </div>
    );
};

export default Chat;
