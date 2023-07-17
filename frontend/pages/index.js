import React, { useState, useEffect } from 'react';
import ChatBox from '../components/ChatBox';
import Modal from 'react-modal';
import { get_encoding } from "@dqbd/tiktoken";
import ModalBar from '../components/ModalBar';
import RightSidebar from '../components/RightSidebar';
import { FiMenu } from 'react-icons/fi';
import SearchBar from '../components/SearchBar';
import { AiOutlineSend } from 'react-icons/ai';
import ChatInput from '../components/ChatInput';  // adjust this path to point to the ChatInput file
import ModelSelector from '../components/ModelSelector';


const encoding = get_encoding("cl100k_base");
Modal.setAppElement('#__next');

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };

  const submitMessage = async (input) => {
    console.log(input);
    let messageData = null;
    let currentId = null;
    const inputValue = input;  // get the input value from the event

    setMessages((prevMessages) => [...prevMessages, { text: inputValue, user: 'human' }]);

    const response = await fetch('http://127.0.0.1:8000/message_streaming', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input: input }),
    });
    let reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        console.log("Stream finished.");
        if (buffer) {
          console.error('Stream ended unexpectedly; partial JSON object:', buffer);
        }
        break;
      }
      buffer += value;
      while (buffer.includes('\n')) {
        // Find the end of the first JSON object in the buffer.
        const endOfJsonObject = buffer.indexOf('\n');

        // Extract the JSON object from the buffer.
        const jsonObjectStr = buffer.slice(0, endOfJsonObject);

        // Process the JSON object.
        try {
          const messageData = JSON.parse(jsonObjectStr);
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
        } catch (e) {
          console.error('Failed to parse JSON object:', jsonObjectStr);
          throw e;  // Rethrow the error, because it's a programming error.
        }
        // Remove the processed JSON object from the buffer.
        buffer = buffer.slice(endOfJsonObject + 1);
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
      <div className="flex-grow overflow-y-scroll" style={{ maxHeight: '75vh' }}>
        <ChatBox messages={messages} />
      </div>
      <RightSidebar isSidebarOpen={isSidebarOpen} />

      <div className="input-area h-1/5 flex bg-gray-800 text-center justify-center items-center w-full text-gray-900" >
        <div className='w-full'>
          <ChatInput onSubmit={submitMessage} />
          <ModelSelector />
        </div>
      </div>
    </div>
  );
};

export default Chat;
