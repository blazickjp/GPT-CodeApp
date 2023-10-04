import React, { useState, useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { setEditablePrompt, setIsModalOpen } from '../store/modal_bar_modals/systemPromptSlice';
import { FaTrash } from 'react-icons/fa';



const LeftSidebar = ({ isLeftSidebarOpen }) => {
    const [selectedDirectory, setSelectedDirectory] = useState(null);
    const [prompts, setPrompts] = useState([]);

    const fileInput = useRef(null);  // Add a reference to the file input
    const dispatch = useDispatch();
    const fetchPrompts = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/list_prompts`);
            if (!response.ok) {
                throw new Error('Error fetching prompts');
            }
            const data = await response.json();
            setPrompts(data.prompts);
        } catch (error) {
            console.error('Error fetching prompts', error);
        }

        console.log("Prompts: ", prompts);
    };

    const handleDeletePrompt = async (id) => {
        console.log("Deleting prompt: ", id)
        try {
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/delete_prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ "prompt_id": id }),
            });
            // if (!response.ok) {
            //     throw new Error('Error deleting prompt');
            // }
            // After deleting, fetch the prompts again to update the list
            fetchPrompts();
        } catch (error) {
            console.error('Error deleting prompt', error);
        }
    };

    useEffect(() => {
        fetchPrompts();
    }, [isLeftSidebarOpen]);

    const handlePromptClick = (prompt) => {
        dispatch(setEditablePrompt(prompt));
    };

    const handleFolderSelect = (event) => {
        const directory = event.target.files[0].webkitRelativePath;
        setSelectedDirectory(directory);
    };

    const handleClick = () => {
        fileInput.current.click();
    };

    return (
        <div className={`fixed h-full w-1/5 left-0 bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isLeftSidebarOpen ? 'translate-x-0' : '-translate-x-full'} overflow-x-hidden`}>
            <div className="flex flex-row justify-between items-center mb-2">
                <input type="file" ref={fileInput} onChange={handleFolderSelect} style={{ display: 'none' }} webkitdirectory="" directory="" mozdirectory="" msdirectory="" odirectory="" />
                {/* <button onClick={handleClick} className="bg-blue-500 hover:bg-blue-700 text-white py-2 px-4 rounded ">Select Directory</button> */}
                {selectedDirectory && <p className="mt-4 text-gray-300">Selected Directory: {selectedDirectory}</p>}
            </div>
            <hr className="border-gray-600 my-4" />
            <h2 className="text-xl font-bold mb-4 text-gray-100">System Prompts</h2>
            {prompts.map(prompt => (
                <details key={prompt.id} className="bg-gray-700 rounded p-2 mb-2">
                    <summary className="text-gray-300 cursor-pointer flex justify-between items-center" onClick={() => handlePromptClick(prompt)}>
                        <span>{prompt.name}</span>
                        <button onClick={() => handleDeletePrompt(prompt.name)}>
                            <FaTrash className=' text-red-400' />
                        </button>
                    </summary>
                    <p className="text-gray-400 pl-4">{prompt.prompt.substring(0, 200)}</p>
                    <button onClick={() => handleDeletePrompt(prompt.name)}>Delete</button>
                </details>
            ))}
        </div>
    );
};

export default LeftSidebar;