import React, { useState, useEffect, useRef } from 'react';

const LeftSidebar = ({ isLeftSidebarOpen }) => {
    const [selectedDirectory, setSelectedDirectory] = useState(null);
    const fileInput = useRef(null);  // Add a reference to the file input

    const handleFolderSelect = (event) => {
        // Extract the directory from the relative path of the first selected file.
        // We're not uploading this file; we're just using its path to get the directory.
        console.log(event.target.files);
        const directory = event.target.files[0].webkitRelativePath;
        setSelectedDirectory(directory);
    };

    const changeProject = () => {
        // Implement your fetch request here
    };

    const handleClick = () => {
        fileInput.current.click();  // When the button is clicked, programmatically click the file input
    };

    return (
        <div className={`fixed h-full w-1/5 left-0 bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isLeftSidebarOpen ? 'translate-x-0' : '-translate-x-full'} overflow-x-hidden`}>
            <div className="flex flex-row justify-between items-center mb-2">
                <h2 className="text-xl font-bold mb-4 text-gray-100">Select Directory</h2>
            </div>
            <input type="file" ref={fileInput} onChange={handleFolderSelect} style={{ display: 'none' }} webkitdirectory="" directory="" mozdirectory="" msdirectory="" odirectory="" />
            <button onClick={handleClick}>Select Directory</button>
            {selectedDirectory && <p>Selected Directory: {selectedDirectory}</p>}
            <hr className="border-gray-600 mb-4" />
        </div>
    );
};

export default LeftSidebar;
