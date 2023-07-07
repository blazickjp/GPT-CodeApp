import React, { useState } from 'react';



const RightSidebar = ({ isSidebarOpen }) => {
    const [summaries, setSummaries] = useState([]);

    const fetchSummaries = () => {
        setSummaries([]);
        fetch('http://127.0.0.1:8000/get_summaries')
            .then(response => response.json())
            .then(data => {
                console.log(data);
                data.forEach(file => {
                    setSummaries(prevSummaries => [...prevSummaries, { file_path: file.file_path, summary: file.summary, tokens: file.tokens }]);
                });
            })
            .catch(console.error);
    };

    return (
        <div className={`fixed h-full w-2/5 right-0 bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full'}`}>
            {/* Add your sidebar content here */}
            <div className="flex flex-row justify-between items-center mb-4">
                <h1 className="text-3xl font-bold mb-4 text-gray-100">Project File Summaries</h1>
                <button onClick={fetchSummaries} className="py-2 px-4 bg-purple-500 text-white rounded hover:bg-purple-700 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-opacity-50">Fetch Summaries</button>
            </div>
            <hr className="border-gray-600 mb-4" />
            {summaries.map((summary, index) => (
                <details key={index} className="mb-4 text-gray-300">
                    <summary className="font-semibold hover:text-white cursor-pointer">{summary.file_path}</summary>
                    <p className="pl-2 text-sm">{summary.summary}</p>
                    <hr className="border-gray-600" />
                </details>
            ))}
        </div>

    );
};

export default RightSidebar;
