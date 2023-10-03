import React, { useState, useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import axios from 'axios';

const LeftSidebar = ({ isLeftSidebarOpen }) => {
    const dispatch = useDispatch();
    const [selectedDirectory, setSelectedDirectory] = useState(null);
    const [prompts, setPrompts] = useState([]);
    const fileInput = useRef(null);  // Add a reference to the file input

    // useEffect(() => {
    //     axios.get('/list_prompts')
    //         .then(response => {
    //             setPrompts(response.data.prompts);
    //         })
    //         .catch(error => {
    //             console.error('Error fetching prompts', error);
    //         });
    // }, []);

    const handlePromptClick = (prompt) => {
        dispatch(setEditablePrompt(prompt));
        dispatch(setIsModalOpen(true));
    };
    
    useEffect(() => {
            const fetchPrompts = async () => {
            return [
                {
                    "id": 1,
                    "prompt": "Write a function to calculate the factorial of a number.",
                    "created_at": "2022-01-01T00:00:00.000Z",
                    "updated_at": "2022-01-01T00:00:00.000Z"
                },
                {
                    "id": 2,
                    "prompt": "Write a function to reverse a string.",
                    "created_at": "2022-01-02T00:00:00.000Z",
                    "updated_at": "2022-01-02T00:00:00.000Z"
                },
                {
                    "id": 3,
                    "prompt": "Write a function to check if a number is prime.",
                    "created_at": "2022-01-03T00:00:00.000Z",
                    "updated_at": "2022-01-03T00:00:00.000Z"
                }
            ];
        };
    
        fetchPrompts().then(prompts => {
            setPrompts(prompts);
        });
    }, []);

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
                <h2 className="text-xl font-bold mb-4 text-gray-100">Select Directory</h2>
            </div>
            <input type="file" ref={fileInput} onChange={handleFolderSelect} style={{ display: 'none' }} webkitdirectory="" directory="" mozdirectory="" msdirectory="" odirectory="" />
            <button onClick={handleClick} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Select Directory</button>
            {selectedDirectory && <p className="mt-4 text-gray-300">Selected Directory: {selectedDirectory}</p>}
            <hr className="border-gray-600 my-4" />
            <h2 className="text-xl font-bold mb-4 text-gray-100">System Prompts</h2>
            {prompts.map(prompt => (
                <div key={prompt.id} className="bg-gray-700 rounded p-2 mb-2">
                    <p className="text-gray-300">{prompt.prompt}</p>
                </div>
            ))}
        </div>
    );
};

export default LeftSidebar;