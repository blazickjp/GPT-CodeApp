import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types'; // Import PropTypes
import { FaTrash } from 'react-icons/fa';
import { HiOutlineCheckCircle } from 'react-icons/hi';
import DirectorySelectOption from './DirectorySelectOption';

const LeftSidebar = ({ isLeftSidebarOpen }) => {
    const [prompts, setPrompts] = useState([]);
    const [sidebarKey] = useState(0);
    const [saving, setSaving] = useState({}); // Track saving status by prompt ID

    const fetchPrompts = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/list_prompts`);
            if (!response.ok) {
                throw new Error('Error fetching prompts');
            }
            const data = await response.json();
            setPrompts(data.prompts);
            console.log(data.prompts);
        } catch (error) {
            console.error('Error fetching prompts', error);
        }
    };

    const handleDeletePrompt = async (id) => {
        console.log(prompts);
        console.log("Deleting prompt: ", id);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/delete_prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ "prompt_id": id }),
            });
            if (!response.ok) {
                throw new Error('Error deleting prompt');
            }
            await fetchPrompts();
        } catch (error) {
            console.error('Error deleting prompt', error);
        }
    };

    const setPrompt = async (id, prompt) => {
        // Set the saving state to 'pending' for the specific prompt ID
        setSaving(prev => ({ ...prev, [id]: 'pending' }));
        console.log("Setting prompt: ", id);

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/save_prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ "prompt_name": id, "prompt": prompt }),
            });
            if (!response.ok) {
                throw new Error('Error setting prompt');
            }

            // After success, update only the status of the specific prompt ID
            setTimeout(() => {
                setSaving(prev => ({ ...prev, [id]: 'success' }));
                setTimeout(() => setSaving(prev => ({ ...prev, [id]: false })), 2000);
            }, 1000);

            fetchPrompts();


        } catch (error) {
            console.error('Error setting prompt', error);
            setTimeout(() => {
                setSaving(prev => ({ ...prev, [id]: 'error' }));
                setTimeout(() => setSaving(prev => ({ ...prev, [id]: false })), 2000);
            }, 1000);
        }
    };

    useEffect(() => {
        fetchPrompts();
    }, [sidebarKey, isLeftSidebarOpen]);

    return (
        <div className={`fixed h-full bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isLeftSidebarOpen ? 'translate-x-0' : '-translate-x-full'
            } ${
            // Here we define different widths for different screen sizes
            'w-full sm:w-4/5 md:w-3/5 lg:w-2/5 xl:w-1/5'
            } overflow-x-hidden`}>
            <div className="flex flex-row justify-between items-center mb-2">
                <DirectorySelectOption />
            </div>
            <hr className="border-gray-600 my-4" />
            <h2 className="text-xl font-bold mb-4 text-gray-100">System Prompts</h2>
            {
                prompts.map(prompt => (
                    <details key={prompt.id} className="bg-gray-700 rounded p-2 mb-2">
                        <summary className="text-gray-300 cursor-pointer flex justify-between items-center">
                            <span>{prompt.name}</span>
                            <div className="flex flex-row items-end space-x-4">
                                <button onClick={() => setPrompt(prompt.name, prompt.prompt)}>
                                    <HiOutlineCheckCircle className={`text-green-400 
                                            ${saving[prompt.id] === 'pending' ? 'text-yellow-400' :
                                            saving[prompt.id] === 'success' ? 'text-green-500' :
                                                saving[prompt.id] === 'error' ? 'text-red-500' :
                                                    'text-green-400'}`} />
                                </button>
                                <button onClick={() => handleDeletePrompt(prompt.id)}>
                                    <FaTrash className=' text-red-400' />
                                </button>
                            </div>
                        </summary>
                        <p className="text-gray-400 pl-4">{prompt.prompt?.substring(0, 200)}</p>
                    </details>
                ))}
        </div >
    );
};

// Define prop types for LeftSidebar
LeftSidebar.propTypes = {
    isLeftSidebarOpen: PropTypes.bool.isRequired // Define the prop type and mark it as required
};

export default LeftSidebar;