import React, { useState, useEffect } from 'react';
import ChatBox from '../components/ChatBox';
import Modal from 'react-modal';
import { get_encoding } from "@dqbd/tiktoken";
import ModalBar from '../components/ModalBar';
import RightSidebar from '../components/RightSidebar';
import { FiMenu } from 'react-icons/fi';
import SearchBar from '../components/SearchBar';
import { AiOutlineSend } from 'react-icons/ai';


const encoding = get_encoding("cl100k_base");
Modal.setAppElement('#__next');

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };

  const submitMessage = async (e) => {
    e.preventDefault();
    let messageData = null;
    let currentId = null;

    setMessages((prevMessages) => [...prevMessages, { text: input, user: 'human' }]);
    setInput("");

    const response = await fetch('http://127.0.0.1:8000/message_streaming', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input }),
    });
    let reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        console.log("Stream finished.");
        break;
      }
      try {
        messageData = JSON.parse(value);
      } catch (e) {
        console.log("Failed to parse: ", value);
        continue;
      }
      let id = messageData.id;
      let content = messageData.content;
      console.log(content, id);
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

    }
  };

  useEffect(() => {
    // Function to fetch historical messages from the server
    const fetchHistoricalMessages = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/get_messages'); // Replace this with your actual API endpoint
        const historicalMessages = await response.json();
        console.log(historicalMessages.messages);

        // Format and set the messages
        const formattedMessages = historicalMessages.messages.map(message => ({
          text: message.full_content,
          user: message.role === 'user' ? 'human' : 'ai'
        }));
        // console.log(formattedMessages);
        setMessages(formattedMessages);
      } catch (error) {
        console.error('Failed to fetch historical messages:', error);
      }
    };

    // Call the function to fetch historical messages
    fetchHistoricalMessages();
  }, []); // Empty dependency array causes this effect to run only once


  return (
    <div className="flex flex-col bg-gray-800 h-screen">
      <div className="flex flex-row p-2 h-1/8 mx-auto">
        <button className="float-left">
          <FiMenu className="ml-2" />
        </button>
        <h1 className="text-4xl font-bold text-center text-dark-secondary px-5">CodeGPT</h1>
        <button onClick={toggleSidebar} className="float-right">
          <FiMenu className="mr-2" />
        </button>
      </div>
      <div className="flex flex-col items-center">
        <SearchBar />
        <ModalBar />
      </div>
      <RightSidebar isSidebarOpen={isSidebarOpen} />
      <div className="flex-grow overflow-y-scroll" style={{ maxHeight: '75vh' }}>
        <ChatBox messages={messages} />
      </div>

      <div className="input-area flex flex-row bg-gray-800 text-center justify-center items-center w-full text-black" style={{ height: '20vh' }}>
        <form onSubmit={submitMessage} className='flex w-1/2'>
          <input
            id='chat-input-box'
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' ? submitMessage(e) : null}
            placeholder="Type a message..."
            className="p-2 rounded mr-2 flex-grow"
          />
          <button type="submit" className=" text-purple-700 font-bold py-2 px-4 rounded text-xl">
            <AiOutlineSend />
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chat;
