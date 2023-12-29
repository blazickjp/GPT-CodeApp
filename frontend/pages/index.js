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
import { setLogMessages } from '../store/messages/logMessagesSlice';
import { toggleSidebar } from '../store/sidebar/sidebarSlice';


const encoding = get_encoding("cl100k_base");
Modal.setAppElement('#__next');

const Chat = () => {
  const dispatch = useDispatch();
  const messages = useSelector(state => state.messages);
  const isSidebarOpen = useSelector(state => state.sidebar.isOpen);
  const [sidebarKey, setSidebarKey] = useState(0);
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(false);


  // Add a function to toggle the left sidebar
  const toggleLeftSidebar = () => {
    setIsLeftSidebarOpen(!isLeftSidebarOpen);
    console.log(isLeftSidebarOpen);
  };

  const fetchLogMessages = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/logs/errors`); // Adjust the endpoint as necessary
      if (response.ok) {
        const logs = await response.json();
        console.log("Logs:")
        console.log(logs);
        dispatch(setLogMessages(logs.error_logs)); // Update the state with the fetched log messages
      } else {
        console.error('Failed to fetch log messages:', response.status);
      }
    } catch (error) {
      console.error('Error fetching log messages:', error);
    }
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

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/message_streaming`, {
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
      while (buffer.includes('@@')) {
        const endOfJsonObject = buffer.indexOf('@@');
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
        buffer = buffer.slice(endOfJsonObject + 2); // Accounts for the length of the delimiter.
      }
    }
  };





  useEffect(() => {
    const fetchHistoricalMessages = async () => {
      console.log(`${process.env.NEXT_PUBLIC_API_URL}`)
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_messages?chatbox=true`);
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
    fetchLogMessages();

  }, []);


  return (
    <div className="flex flex-col bg-gray-800 h-screen">
      <div className="flex flex-row p-2 h-1/8 mx-auto">
        <button onClick={toggleLeftSidebar} className="float-left">
          <FiMenu className="ml-2" />
        </button>
        <h1 className="text-4xl text-center text-dark-secondary px-5 ">CodeKnot</h1>
        {/* <img src="/codeknot.png" className="bg-transparent" height={100} width={100} /> */}
        <button onClick={() => dispatch(toggleSidebar())} className="float-right">
          <FiMenu className="mr-2" />
        </button>
      </div>
      <div className="flex flex-col items-center border-b border-slate-500">
        <SearchBar />
        <ModalBar />
      </div>
      <div className="flex-grow overflow-y-scroll" style={{ maxHeight: '75vh' }}>
        <ChatBox messages={messages} />
      </div>
      <RightSidebar isSidebarOpen={isSidebarOpen} />
      <LeftSidebar key={sidebarKey} isLeftSidebarOpen={isLeftSidebarOpen} />

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
