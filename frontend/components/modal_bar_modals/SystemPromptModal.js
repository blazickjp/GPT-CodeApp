import React, { useEffect, useState } from 'react';
import ReactModal from 'react-modal';
import { useDispatch, useSelector } from 'react-redux';
import { setSystemPrompt, setIsModalOpen, setPromptName } from '../../store/modal_bar_modals/systemPromptSlice';

ReactModal.setAppElement('#__next');

const SystemPromptModal = () => {
    const dispatch = useDispatch();
    const isOpen = useSelector(state => state.systemPrompt.isModalOpen);
    const systemTokens = useSelector(state => state.systemPrompt.systemTokens);
    const [localPrompt, setLocalPrompt] = useState('');
    const promptName = useSelector(state => state.systemPrompt.promptName);
    const [error, setError] = React.useState('');

    useEffect(() => {
        if (isOpen) {
            fetchSystemPrompt();
        }
    }, [isOpen]);

    const saveSystemPrompt = async (e) => {
        e.preventDefault();
        if (!promptName.trim() || !localPrompt.trim()) {
            setError('Both name and prompt content are required.');
            return;
        }

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/save_prompt`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: localPrompt, prompt_name: promptName }),
            });

            if (!response.ok) {
                throw new Error('Failed to save the prompt. Please try again.');
            }

            dispatch(setPromptName(promptName));
            dispatch(setSystemPrompt(localPrompt));
            dispatch(setIsModalOpen(false));
            setError('');
        } catch (err) {
            console.error(err);
            setError(err.message);
        }
    };

    const handleClose = () => {
        dispatch(setIsModalOpen(false));
        setError('');
    };

    const fetchSystemPrompt = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/system_prompt`);
            if (!response.ok) {
                throw new Error('Error fetching system prompt');
            }
            const data = await response.json();
            setLocalPrompt(data.system_prompt);
            dispatch(setPromptName(data.name));
        } catch (error) {
            console.error('Error fetching system prompt', error);
        }
    }

    useEffect(() => {
        fetchSystemPrompt();
    }, []);

    return (
        <div>
            <ReactModal
                isOpen={isOpen}
                onRequestClose={handleClose}
                shouldCloseOnOverlayClick={true}
                className="fixed inset-0 flex items-center justify-center m-96 bg-gray-800 text-white border-blue-500"
                overlayClassName="fixed inset-0 bg-gray-800 bg-opacity-50"
            >
                <div className="relative flex flex-col bg-gray-800 rounded p-4 w-full mx-auto text-white border border-purple-200">
                    <h2 className="text-xl">System Prompt</h2>
                    <p className="text-sm text-green-800">Tokens: {systemTokens}</p>
                    {error && <p className="text-red-500">{error}</p>}
                    <form onSubmit={saveSystemPrompt}>
                        <input
                            type="text"
                            value={promptName}
                            onChange={(e) => dispatch(setPromptName(e.target.value))}
                            placeholder="Include a name to save this system prompt!"
                            className="relative mt-2 w-full p-2 border bg-slate-600 rounded items-center justify-center"
                        />
                        <textarea
                            value={localPrompt}
                            onChange={(e) => setLocalPrompt(e.target.value)}
                            className="relative mt-2 w-full h-96 p-2 border bg-slate-600 rounded items-center justify-center"
                        />
                        <button
                            type="submit"
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