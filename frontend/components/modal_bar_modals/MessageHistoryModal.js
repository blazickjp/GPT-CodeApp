import React from 'react';
import ReactModal from 'react-modal';
import { useDispatch, useSelector } from 'react-redux';
import { setIsMessageModalOpen } from '../../store/modal_bar_modals/messageHistorySlice';

const MessageHistoryModal = () => {
    const dispatch = useDispatch();
    const messageHistory = useSelector(state => state.messageHistory.messageHistory);
    const isMessageModalOpen = useSelector(state => state.messageHistory.isMessageModalOpen);

    return (
        <ReactModal
            isOpen={isMessageModalOpen}
            onRequestClose={() => dispatch(setIsMessageModalOpen(false))}
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
