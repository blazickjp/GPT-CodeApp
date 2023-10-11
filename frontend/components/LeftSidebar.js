import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useDispatch } from 'react-redux';
import { setEditablePrompt, setIsModalOpen } from '../store/modal_bar_modals/systemPromptSlice';
import { FaTrash } from 'react-icons/fa';
import { HiOutlineCheckCircle } from 'react-icons/hi';
import DirectorySelectOption from './DirectorySelectOption';



const LeftSidebar = ({ isLeftSidebarOpen }) => {
    const dispatch = useDispatch();
    const [selectedDirectory, setSelectedDirectory] = useState(null);
    const [prompts, setPrompts] = useState([]);
    const fileInput = useRef(null);  // Add a reference to the file input
    const promptsRef = useRef([]);

    const fetchPrompts = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/list_prompts`);
            if (!response.ok) {
                throw new Error('Error fetching prompts');
            }
            const data = await response.json();
            setPrompts(data.prompts);
            promptsRef.current = response.data;

        } catch (error) {
            console.error('Error fetching prompts', error);
        }
        console.log("Prompts: ", prompts);
    };


    const handleDeletePrompt = async (id) => {
        console.log("Deleting prompt: ", id)
        if (id === null) {
            return;
        }
        try {
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/delete_prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ "prompt_id": id }),
            });
            fetchPrompts();
        } catch (error) {
            console.error('Error deleting prompt', error);
        }

    };
    const savePrompt = async (id, prompt) => {
        try {
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/save_prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ "prompt_id": id, "prompt": prompt }),
            });
            fetchPrompts();
        } catch (error) {
            console.error('Error deleting prompt', error);
        }
    }

    useEffect(() => {
        fetchPrompts();
    }, [isLeftSidebarOpen]);

    const handlePromptClick = (prompt) => {
        dispatch(setEditablePrompt(prompt));
        dispatch(setIsModalOpen(true));
    };


    return (
        <div className={`fixed h-full w-1/5 left-0 bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isLeftSidebarOpen ? 'translate-x-0' : '-translate-x-full'} overflow-x-hidden`}>
            <div className="flex flex-row justify-between items-center mb-2">
                <DirectorySelectOption />
            </div>
            <hr className="border-gray-600 my-4" />
            <h2 className="text-xl font-bold mb-4 text-gray-100">System Prompts</h2>
            {
                prompts.map(prompt => (
                    <details key={prompt.id} className="bg-gray-700 rounded p-2 mb-2">
                        <summary className="text-gray-300 cursor-pointer flex justify-between items-center" onClick={() => handlePromptClick(prompt.prompt)}>
                            <span>{prompt.name}</span>
                            <div className="flex flex-row items-end space-x-4">
                                <button onClick={() => savePrompt(prompt.name, prompt.prompt)}>
                                    <HiOutlineCheckCircle className=' text-green-400' />
                                </button>
                                <button onClick={() => handleDeletePrompt(prompt.name)}>
                                    <FaTrash className=' text-red-400' />
                                </button>
                            </div>
                        </summary>
                        <p className="text-gray-400 pl-4">{prompt.prompt?.substring(0, 200)}</p>
                    </details>
                ))
            }
        </div >
    );
};

export default LeftSidebar;