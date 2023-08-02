The new file `MessageHistoryModal.js` will contain a React component for the message history modal. The component will receive `messageHistory` and `isMessageModalOpen` as props and will display a list of messages in a modal. The modal will be closed when the `onRequestClose` event is triggered.

Here is the code for the new file:

```jsx
import React from 'react';
import ReactModal from 'react-modal';

const MessageHistoryModal = ({ messageHistory, isMessageModalOpen, setIsMessageModalOpen }) => {
    return (
        <ReactModal
            isOpen={isMessageModalOpen}
            onRequestClose={() => setIsMessageModalOpen(false)}
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

In this component, `messageHistory` is an array of messages, where each message is an object with properties `role` and `content`. The `role` can be either 'user' or 'system', and `content` is the text of the message. The messages are displayed in a list, with user messages having a blue background and system messages having a green background.