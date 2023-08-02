```javascript
import React, { useState } from 'react';
import ReactModal from 'react-modal';
import { get_encoding } from "@dqbd/tiktoken";

ReactModal.setAppElement('#__next');

const encoding = get_encoding("cl100k_base");

const SystemPromptModal = () => {
    const [systemPrompt, setSystemPrompt] = useState("");
    const [systemTokens, setSystemTokens] = useState(0);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editablePrompt, setEditablePrompt] = useState("");

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

    return (
        <div>
            <button onClick={fetchSystemPromptAndOpenModal}>
                System Prompt:
                <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                    {systemTokens} tokens
                </span>
            </button>
            <ReactModal
                isOpen={isModalOpen}
                onRequestClose={() => setIsModalOpen(false)}
                shouldCloseOnOverlayClick={true}
                className="fixed inset-0 flex items-center justify-center m-96"
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
            </ReactModal>
        </div>
    );
}

export default SystemPromptModal;
```