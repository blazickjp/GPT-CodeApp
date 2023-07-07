import React, { useState, useEffect } from 'react';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import ChatBox from '../components/ChatBox';
import Modal from 'react-modal';
import { get_encoding } from "@dqbd/tiktoken";
import ModalBar from '../components/ModalBar';
import RightSidebar from '../components/RightSidebar';
import { FiMenu } from 'react-icons/fi';
import { AiOutlineClose } from 'react-icons/ai';
import { FaRegWindowMinimize } from 'react-icons/fa';
import { FaRegWindowMaximize } from 'react-icons/fa';
import { FaRegWindowRestore } from 'react-icons/fa';
import { FaRegWindowClose } from 'react-icons/fa';


const encoding = get_encoding("cl100k_base");
const client = new W3CWebSocket('ws://127.0.0.1:8000/ws');
Modal.setAppElement('#__next');

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };


  const fetchMessagesAndOpenModal = (modal = true) => {
    setMessages([]);
    fetch('http://127.0.0.1:8000/get_messages')
      .then(response => response.json())
      .then(data => {
        console.log(data.messages);
        data.messages.forEach(message => {
          setMessages(prevMessages => [...prevMessages, { text: message.content, user: message.role }]);
        });
        // let m_tokens = 0;
        // for (const message of data.messages) {
        //     console.log(message);
        //     m_tokens += encoding.encode(message.content).length;
        // }
        // console.log(m_tokens);
        // setMessageTokens(m_tokens);
      })
      .catch(console.error);
  };

  useEffect(() => {
    let currentId = null;
    const connect = () => {

      client.onopen = () => {
        console.log('WebSocket Client Connected');
        fetchMessagesAndOpenModal(false);
        console.log(messages)
      };

      client.onmessage = (message) => {
        const messageData = JSON.parse(message.data);
        // console.log(message.data);
        let id = messageData.id;
        let content = messageData.content;
        if (id != currentId) {
          setMessages(prevMessages => [...prevMessages, { text: content, user: 'ai' }]);
          currentId = id;
        } else {
          setMessages(prevMessages => {
            // console.log(prevMessages);
            const lastMessage = { ...prevMessages[prevMessages.length - 1] };
            lastMessage.text = lastMessage.text + content;
            return [...prevMessages.slice(0, prevMessages.length - 1), lastMessage];
          })
        }
      };

      client.onclose = (event) => {
        console.log('WebSocket connection closed');
        if (event.wasClean) {
          console.log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
          // e.g. server process killed or network down
          // event.code is usually 1006 in this case
          console.log('[close] Connection died');
          // Reconnect after a delay
          setTimeout(connect, 5000); // 5 second delay
        }
      };

      client.onerror = (error) => {
        console.log('WebSocket Client Error', error);
      };
    };

    connect();

    return () => {
      client.close();
    };

  }, []);


  const submitMessage = async (e) => {
    e.preventDefault(); // Prevent form from causing a page reload

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
      <div className="flex flex-row p-4 h-1/8 mx-auto">
        <h1 className="text-4xl font-bold text-center text-dark-secondary px-5">CodeGPT</h1>
        <button onClick={toggleSidebar} className="float-right">
          <FiMenu className="mr-2" />
        </button>
      </div>

      <ModalBar />
      <RightSidebar isSidebarOpen={isSidebarOpen} />
      <div className="flex-grow overflow-y-scroll" style={{ maxHeight: '75vh' }}>
        <ChatBox messages={messages} />
      </div>

      <div className="input-area flex flex-row bg-gray-700 text-center justify-center items-center w-full text-black" style={{ height: '20vh' }}>
        <form onSubmit={submitMessage} className='flex w-1/2'>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' ? submitMessage(e) : null}
            placeholder="Type a message..."
            className="p-2 rounded mr-2 flex-grow"
          />
          <button type="submit" className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-full">Send</button>
        </form>
      </div>
    </div>
  );
};

export default Chat;
