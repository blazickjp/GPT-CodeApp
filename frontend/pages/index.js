import React, { useState, useEffect } from 'react';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import ChatBox from '../components/ChatBox';
import Modal from 'react-modal';




const client = new W3CWebSocket('ws://127.0.0.1:8000/ws');
Modal.setAppElement('#__next');



const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editablePrompt, setEditablePrompt] = useState("");
  const [functions, setFunctions] = useState([]);
  const [isFunctionModalOpen, setIsFunctionModalOpen] = useState(false);



  const fetchSystemPromptAndOpenModal = () => {
    fetch('http://127.0.0.1:8000/system_prompt')
      .then(response => response.json())
      .then(data => {
        setEditablePrompt(data.system_prompt);
        setSystemPrompt(data.system_prompt);
        setIsModalOpen(true);
      })
      .catch(console.error);
  };

  const fetchFunctionsAndOpenModal = () => {
    fetch('http://127.0.0.1:8000/get_functions')
      .then(response => response.json())
      .then(data => {
        setFunctions(data.functions);
        setIsFunctionModalOpen(true);
      })
      .catch(console.error);
  };

  const updateSystemPrompt = (e) => {
    e.preventDefault();
    fetch('http://127.0.0.1:8000/update_system', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ system_prompt: editablePrompt }),
    })
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        setSystemPrompt(editablePrompt); // Update original systemPrompt
        setIsModalOpen(false); // Close modal
      })
      .catch(console.error);
  };



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
      <div className="p-4 h-1/8">
        <h1 className="text-4xl font-bold text-center text-dark-secondary">CodeGPT</h1>
      </div>
      <div className='flex flex-row mx-auto'>

        <div className='px-5'>
          <button onClick={fetchSystemPromptAndOpenModal}>Show System Prompt</button>

          <Modal
            isOpen={isModalOpen}
            onRequestClose={() => setIsModalOpen(false)}
            className="fixed inset-0 flex items-center justify-center p-4"
            overlayClassName="fixed inset-0 bg-black bg-opacity-50"
          >
            <div className="relative bg-white rounded p-4 w-full max-w-lg mx-auto text-gray-900">
              <h2 className="text-xl">System Prompt</h2>
              <form onSubmit={updateSystemPrompt}>
                <textarea
                  value={editablePrompt}
                  onChange={(e) => setEditablePrompt(e.target.value)}
                  className="mt-2 w-full"
                />
                <button
                  type="submit"
                  className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Update System Prompt
                </button>
              </form>
            </div>
          </Modal>
        </div>
        <div className='px-5'>
          <button onClick={fetchFunctionsAndOpenModal}>Show Functions</button>

          <Modal
            isOpen={isFunctionModalOpen}
            onRequestClose={() => setIsFunctionModalOpen(false)}
            className="fixed inset-0 flex items-center justify-center p-4"
            overlayClassName="fixed inset-0 bg-black bg-opacity-50"
          >
            <div className="relative bg-white rounded p-4 w-full max-w-lg mx-auto text-gray-900 overflow-scroll">
              <h2 className="text-xl">Functions</h2>
              <pre>
                {functions.map((f) => (
                  <div key={f.name}>
                    <h3 className="text-lg">{f.name}</h3>
                    <p>{f.description}</p>
                    <p className="text-sm">{f.signature}</p>
                    <hr />
                  </div>
                ))}
              </pre>
            </div>
          </Modal>

        </div>
      </div>


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
