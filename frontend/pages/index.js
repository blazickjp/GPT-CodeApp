import React, { useState, useEffect } from 'react';
import ChatBox from '../components/ChatBox';
import Modal from 'react-modal';
import { get_encoding } from "@dqbd/tiktoken";
import ModalBar from '../components/ModalBar';
import RightSidebar from '../components/RightSidebar';
import LeftSidebar from '../components/LeftSidebar';
import { FiMenu } from 'react-icons/fi';
import SearchBar from '../components/SearchBar';
import ChatInput from '../components/ChatInput';  // adjust this path to point to the ChatInput file
import ModelSelector from '../components/ModelSelector';
import { useDispatch, useSelector } from 'react-redux';
import { addMessage, addAIPartResponse, fetchMessages } from '../store/messages/messagesSlice';
import { toggleSidebar } from '../store/sidebar/sidebarSlice';

const encoding = get_encoding("cl100k_base");
Modal.setAppElement('#__next');

const Chat = () => {
  const dispatch = useDispatch();
  const messages = useSelector(state => state.messages);
  const isSidebarOpen = useSelector(state => state.sidebar.isOpen);
  // Add state for the left sidebar
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(false);

  // Add a function to toggle the left sidebar
  const toggleLeftSidebar = () => {
    setIsLeftSidebarOpen(!isLeftSidebarOpen);
    console.log(isLeftSidebarOpen);
  };


  const submitMessage = async (input, command = null) => {
    console.log(input);
    let messageData = null;
    let currentId = null;
    let body = null;

    dispatch(addMessage({ text: input, user: 'human' }));
    if (command) {
      body = JSON.stringify({ input: input, command: command });
    } else {
      body = JSON.stringify({ input: input })
    };

    const response = await fetch('http://127.0.0.1:8000/message_streaming', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
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
        const endOfJsonObject = buffer.indexOf('\n');
        const jsonObjectStr = buffer.slice(0, endOfJsonObject);

        try {
          const messageData = JSON.parse(jsonObjectStr);
          let id = messageData.id;
          let content = messageData.content;
          if (id != currentId) {
            dispatch(addMessage({ text: content, user: 'ai' }));
            currentId = id;
          } else {
            dispatch(addAIPartResponse({ text: content, user: 'ai' }));
          }
        } catch (e) {
          console.error('Failed to parse JSON object:', jsonObjectStr);
          throw e;  // Rethrow the error, because it's a programming error.
        }
        buffer = buffer.slice(endOfJsonObject + 1);
      }
    }
  };

  useEffect(() => {
    const fetchHistoricalMessages = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/get_messages?chatbox=true');
        const historicalMessages = await response.json();
        const formattedMessages = historicalMessages.messages.map(message => ({
          text: message.full_content,
          user: message.role === 'user' ? 'human' : 'ai'
        }));
        // console.log(formattedMessages);
        formattedMessages.forEach(message => dispatch(addMessage(message)));
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
        {/* <button onClick={toggleLeftSidebar} className="float-left">
          <FiMenu className="ml-2" />
        </button>
        <h1 className="text-4xl font-bold text-center text-dark-secondary px-5">CodeGPT</h1>
        <button onClick={() => dispatch(toggleSidebar())} className="float-right">
          <FiMenu className="mr-2" />
        </button> */}
      </div>
      <div className="flex flex-col items-center border-b border-slate-500">
        <SearchBar />
        <ModalBar />
      </div>
      <div className="flex-grow overflow-y-scroll" style={{ maxHeight: '75vh' }}>
        <ChatBox messages={messages} />
      </div>
      <RightSidebar isSidebarOpen={isSidebarOpen} />
      {/* <LeftSidebar isLeftSidebarOpen={isLeftSidebarOpen} /> */}

      <div className="input-area h-1/6 flex bg-gray-800 text-center justify-center items-center w-full text-gray-900 border-t border-slate-500" >
        <div className='w-full'>
          <ChatInput onSubmit={submitMessage} />
          <ModelSelector />
        </div>
      </div>
    </div>
  );
};

export default Chat;
