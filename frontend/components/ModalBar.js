import React, { useState, useEffect } from 'react';
import { get_encoding } from "@dqbd/tiktoken";
// import CustomModal from './CustomModal';
import Modal from 'react-modal';


const encoding = get_encoding("cl100k_base");
Modal.setAppElement('#__next');

const ModalBar = () => {
    const [systemPrompt, setSystemPrompt] = useState("");
    const [systemTokens, setSystemTokens] = useState(0);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editablePrompt, setEditablePrompt] = useState("");
    const [functions, setFunctions] = useState([]);
    const [functionTokens, setFunctionTokens] = useState(0);
    const [isFunctionModalOpen, setIsFunctionModalOpen] = useState(false);
    const [messageHistory, setMessageHistory] = useState([]);
    const [isMessageModalOpen, setIsMessageModalOpen] = useState(false);
    const [messageTokens, setMessageTokens] = useState(0);

    const fetchSystemPromptAndOpenModal = (modal = true) => {
        fetch('http://127.0.0.1:8000/system_prompt')
            .then(response => response.json())
            .then(data => {
                setEditablePrompt(data.system_prompt);
                setSystemPrompt(data.system_prompt);
                const tokens = encoding.encode(data.system_prompt);
                setSystemTokens(tokens.length);
                if (modal) {
                    setIsModalOpen(true);
                }
            })
            .catch(console.error);
    };

    const fetchFunctionsAndOpenModal = (modal = true) => {
        fetch('http://127.0.0.1:8000/get_functions')
            .then(response => response.json())
            .then(data => {
                setFunctions(data.functions);
                if (modal) {
                    setIsFunctionModalOpen(true);
                }
                console.log(JSON.stringify(data.functions[0]));
                const f_tokens = encoding.encode(JSON.stringify(data.functions[0]));
                console.log(f_tokens);
                setFunctionTokens(f_tokens.length);
            })
            .catch(console.error);
    };

    const fetchMessagesAndOpenModal = (modal = true) => {
        setMessageHistory([]);
        fetch('http://127.0.0.1:8000/get_messages')
            .then(response => response.json())
            .then(data => {
                setMessageHistory(data.messages);
                if (modal) {
                    setIsMessageModalOpen(true);
                }
                let m_tokens = 0;
                for (const message of data.messages) {
                    console.log(message);
                    m_tokens += encoding.encode(message.content).length;
                }
                console.log(m_tokens);
                setMessageTokens(m_tokens);
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
        fetchSystemPromptAndOpenModal(false);
        fetchFunctionsAndOpenModal(false);
    }, []); //
    return (
        <div className='flex flex-row mx-auto pb-3'>
            <div>
                <button onClick={fetchSystemPromptAndOpenModal}>
                    System Prompt:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {systemTokens} tokens
                    </span>
                </button>
                <Modal
                    isOpen={isModalOpen}
                    onRequestClose={() => setIsModalOpen(false)}
                    className="fixed inset-0 flex items-center justify-center p-4"
                    overlayClassName="fixed inset-0 bg-black bg-opacity-50"
                >
                    <div className="relative bg-white rounded p-4 w-full max-w-screen-lg mx-auto text-gray-900">
                        <h2 className="text-xl">System Prompt</h2>
                        <p className="text-sm text-green-800">Tokens: {systemTokens}</p>
                        <form onSubmit={updateSystemPrompt}>
                            <textarea
                                value={editablePrompt}
                                onChange={(e) => setEditablePrompt(e.target.value)}
                                className="mt-2 w-full h-96 p-2 border border-gray-300 rounded"
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
                <button onClick={fetchFunctionsAndOpenModal}>
                    Functions:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {functionTokens} tokens
                    </span>
                </button>

                <Modal
                    isOpen={isFunctionModalOpen}
                    onRequestClose={() => setIsFunctionModalOpen(false)}
                    className="fixed inset-0 flex items-center justify-center p-4 w-auto"
                    overlayClassName="fixed inset-0 bg-black bg-opacity-50"
                >
                    <div className="relative bg-white rounded p-4 max-w-screen-lg mx-auto text-gray-900 overflow-scroll">
                        <h2 className="text-xl">Functions</h2>
                        <pre>
                            {functions.map((f) => (
                                <div key={f.name}>
                                    <h3 className="text-lg">{f.name}</h3>
                                    <p>{f.description}</p>
                                    <hr />
                                </div>
                            ))}
                        </pre>
                    </div>
                </Modal>

            </div>
            <div className='px-5'>
                <button onClick={fetchMessagesAndOpenModal}>
                    Message History:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {messageTokens} tokens
                    </span>
                </button>

                <Modal
                    isOpen={isMessageModalOpen}
                    onRequestClose={() => setIsMessageModalOpen(false)}
                    className="fixed inset-0 flex items-center justify-center p-4 w-full"
                    overlayClassName="fixed inset-0 bg-black bg-opacity-50"
                >
                    <div className="relative bg-gray-700 rounded p-4 max-w-screen-lg mx-auto text-gray-200 overflow-scroll">
                        <h2 className="text-xl text-white">Messages</h2>
                        {messageHistory.map((m, index) => (
                            <div key={index} className={m.role === 'user' ? 'my-4 p-2 rounded bg-blue-600 text-white' : 'my-4 p-2 rounded bg-green-600 text-white'}>
                                <h3 className="text-lg font-bold">{m.role.toUpperCase()}</h3>
                                <p className="text-md">{m.content}</p>
                            </div>
                        ))}
                    </div>

                </Modal>
            </div>
        </div>
    );
}

export default ModalBar;
