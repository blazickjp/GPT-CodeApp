import React from 'react';
import ReactModal from 'react-modal';
import { useDispatch, useSelector } from 'react-redux';
import { setSystemPrompt, setIsModalOpen, setEditablePrompt, setPromptName } from '../../store/modal_bar_modals/systemPromptSlice';

ReactModal.setAppElement('#__next');

const SystemPromptModal = () => {
    const dispatch = useDispatch();
    const isOpen = useSelector(state => state.systemPrompt.isModalOpen);
    const systemTokens = useSelector(state => state.systemPrompt.systemTokens);
    const editablePrompt = useSelector(state => state.systemPrompt.editablePrompt);
    const promptName = useSelector(state => state.systemPrompt.promptName);

    const saveSystemPrompt = (e) => {
        if (promptName === '') {
            alert('Please enter a name for this prompt');
            return;
        }
        dispatch(setSystemPrompt(editablePrompt));
        dispatch(setPromptName(promptName));
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/save_prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: editablePrompt, prompt_name: promptName }),
        })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                setSystemPrompt(editablePrompt); // Update original systemPrompt
            })
            .catch(console.error);

        dispatch(setIsModalOpen(false));

    }

    return (
        <div>
            <ReactModal
                isOpen={isOpen}
                onRequestClose={() => dispatch(setIsModalOpen(false))}
                shouldCloseOnOverlayClick={true}
                className="fixed inset-0 flex items-center justify-center m-96 bg-gray-800 text-white border-blue-500"
                overlayClassName="fixed inset-0 bg-gray-800 bg-opacity-50"
            >
                <div className="relative flex flex-col bg-gray-800 rounded p-4 w-full mx-auto text-white border border-purple-200">
                    <h2 className="text-xl">System Prompt</h2>
                    <p className="text-sm text-green-800">Tokens: {systemTokens}</p>
                    <form onSubmit={saveSystemPrompt} className=''>
                        <input
                            type="text"
                            value={promptName}
                            onChange={(e) => dispatch(setPromptName(e.target.value))}
                            placeholder="Include a name to save this system prompt!"
                            className="relative mt-2 w-full p-2 border bg-slate-600 rounded items-center justify-center"
                        />
                        <textarea
                            value={editablePrompt}
                            onChange={(e) => dispatch(setEditablePrompt(e.target.value))}
                            className="relative mt-2 w-full h-96 p-2 border bg-slate-600 rounded items-center justify-center"
                        />
                        <button
                            type="submit"
                            onClick={saveSystemPrompt}
                            className="mt-4 ml-2 px-4 py-2 bg-purple-500 text-white rounded hover:bg-gray-600"
                        >
                            Save and Close
                        </button>
                    </form>
                </div>
            </ReactModal>
        </div>
    );
}

export default SystemPromptModal;
