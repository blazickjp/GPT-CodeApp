import React from 'react';
import ReactModal from 'react-modal';
import { useDispatch, useSelector } from 'react-redux';
import { setSystemPrompt, setIsModalOpen, setEditablePrompt } from '../../store/modal_bar_modals/systemPromptSlice';

ReactModal.setAppElement('#__next');

const SystemPromptModal = () => {
    const dispatch = useDispatch();
    const isOpen = useSelector(state => state.systemPrompt.isModalOpen);
    const systemTokens = useSelector(state => state.systemPrompt.systemTokens);
    const editablePrompt = useSelector(state => state.systemPrompt.editablePrompt);

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
            <ReactModal
                isOpen={isOpen}
                onRequestClose={() => dispatch(setIsModalOpen(false))}
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
                            onChange={(e) => dispatch(setEditablePrompt(e.target.value))}
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