File Name: frontend/components/SystemPromptModal.js

```javascript
import React from 'react';
import ReactModal from 'react-modal';

const SystemPromptModal = ({ isOpen, onRequestClose, systemTokens, editablePrompt, setEditablePrompt, updateSystemPrompt }) => {
    return (
        <ReactModal
            isOpen={isOpen}
            onRequestClose={onRequestClose}
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
    );
}

export default SystemPromptModal;
```

File Name: frontend/components/FunctionsModal.js

```javascript
import React from 'react';
import ReactModal from 'react-modal';

const FunctionsModal = ({ isOpen, onRequestClose, functions }) => {
    return (
        <ReactModal
            isOpen={isOpen}
            onRequestClose={onRequestClose}
            shouldCloseOnOverlayClick={true}
            className="fixed inset-0 flex items-center justify-center m-96 w-auto"
            overlayClassName="fixed inset-0 bg-black bg-opacity-50"
        >
            <div className="relative bg-white rounded p-4 max-w-screen-lg mx-auto text-gray-900 overflow-scroll">
                <h2 className="text-xl">Functions</h2>
                <pre>
                    {functions?.map((f) => (
                        <div key={f?.name}>
                            <h3 className="text-lg">{f?.name}</h3>
                            <p>{f?.description}</p>
                            <hr />
                        </div>
                    ))}
                </pre>
            </div>
        </ReactModal>
    );
}

export default FunctionsModal;
```

File Name: frontend/components/MessageHistoryModal.js

```javascript
import React from 'react';
import ReactModal from 'react-modal';

const MessageHistoryModal = ({ isOpen, onRequestClose, messageHistory }) => {
    return (
        <ReactModal
            isOpen={isOpen}
            onRequestClose={onRequestClose}
            shouldCloseOnOverlayClick={true}
            className="fixed inset-0 flex items-center justify-center m-96"
            overlayClassName="fixed inset-0 bg-black bg-opacity-50"
        >
            <div className="bg-gray-700 rounded p-4 max-w-screen-lg max-h-96 overflow-y-scroll mx-auto text-gray-200">
                <h2 className="text-xl text-white">Messages</h2>
                {messageHistory.map((m, index) => (
                    <div key={index} className={m.role === 'user' ? 'my-4 p-2 rounded bg-blue-600 text-white' : 'my-4 p-2 rounded bg-green-600 text-white'}>
                        <h3 className="text-lg font-bold">{m.role.toUpperCase()}</h3>
                        <pre className="text-md whitespace-pre-wrap">{m.content}</pre>
                    </div>
                ))}
            </div>
        </ReactModal>
    );
}

export default MessageHistoryModal;
```

Updated File: frontend/components/ModalBar.js

```javascript
import React, { useState, useEffect } from 'react';
import { get_encoding } from "@dqbd/tiktoken";
import ReactModal from 'react-modal';
import SystemPromptModal from './SystemPromptModal';
import FunctionsModal from './FunctionsModal';
import MessageHistoryModal from './MessageHistoryModal';

ReactModal.setAppElement('#__next');

const encoding = get_encoding("cl100k_base");

const ModalBar = () => {
    // ... existing state variables ...

    // ... existing fetch functions ...

    // ... existing useEffect ...

    return (
        <div className='flex flex-row mx-auto pb-3'>
            <div>
                <button onClick={fetchSystemPromptAndOpenModal}>
                    System Prompt:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {systemTokens} tokens
                    </span>
                </button>
                <SystemPromptModal 
                    isOpen={isModalOpen} 
                    onRequestClose={() => setIsModalOpen(false)} 
                    systemTokens={systemTokens} 
                    editablePrompt={editablePrompt} 
                    setEditablePrompt={setEditablePrompt} 
                    updateSystemPrompt={updateSystemPrompt} 
                />
            </div>
            <div className='px-5'>
                < button onClick={fetchFunctionsAndOpenModal} >
                    Functions:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {functionTokens} tokens
                    </span>
                </button >
                <FunctionsModal 
                    isOpen={isFunctionModalOpen} 
                    onRequestClose={() => setIsFunctionModalOpen(false)} 
                    functions={functions} 
                />
            </div >
            <div className='px-5'>
                <button onClick={fetchMessagesAndOpenModal}>
                    Message History:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {messageTokens} tokens
                    </span>
                </button>
                <MessageHistoryModal 
                    isOpen={isMessageModalOpen} 
                    onRequestClose={() => setIsMessageModalOpen(false)} 
                    messageHistory={messageHistory} 
                />
            </div>
        </div >
    );
}

export default ModalBar;
```