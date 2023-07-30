import React, { useState, useEffect } from 'react';



const LeftSidebar = ({ isLeftSidebarOpen }) => {
    const [directory, setDirectory] = useState('');  // add a state for the directory

    const changeProject = () => {
        fetch('http://127.0.0.1:8000/set_directory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ directory: '.' }),
        })
            .then(response => response.json())
            .then(data => {
                console.log(data);
            })
            .catch(console.error);
    };

    console.log(isLeftSidebarOpen);

    return (
        <div className={`fixed h-full w-1/5 left-0 bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isLeftSidebarOpen ? 'translate-x-0' : '-translate-x-full'} overflow-x-hidden`}>
            <div className="flex flex-row justify-between items-center mb-2">
                <h2 className="text-xl font-bold mb-4 text-gray-100">Select Directory</h2>
            </div>
            <hr className="border-gray-600 mb-4" />
        </div>

    );
};

export default LeftSidebar;
