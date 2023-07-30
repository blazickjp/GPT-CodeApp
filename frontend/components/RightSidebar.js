import React, { useState, useEffect } from 'react';
import { scaleLinear } from 'd3-scale';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { AiOutlineMinus } from "react-icons/ai";

const CodeBlock = ({ node, inline, className, children }) => {
    const match = /language-(\w+)/.exec(className || '')
    const lang = match && match[1] ? match[1] : ''
    return !inline && match ? (
        <SyntaxHighlighter language={lang} style={oneDark} >
            {String(children)}
        </SyntaxHighlighter>
    ) : (
        <code className={className} >
            {children}
        </code>
    )
};

const RightSidebar = ({ isSidebarOpen }) => {
    const [summaries, setSummaries] = useState([]);
    const [maxTokens, setMaxTokens] = useState(1);
    const [filesInPrompt, setFilesInPrompt] = useState([]);  // array of file paths

    const fetchSummaries = () => {
        setSummaries([]);
        fetch('http://127.0.0.1:8000/get_summaries')
            .then(response => response.json())
            .then(data => {
                const maxTokensFound = Math.max(...data.map(file => file.file_token_count));
                setMaxTokens(maxTokensFound); // Update the maxTokens state here
                data.forEach(file => {
                    setSummaries(prevSummaries => [...prevSummaries, { file_path: file.file_path, summary: file.summary, file_token_count: file.file_token_count, summary_token_count: file.summary_token_count }]);
                });
            })
            .catch(console.error);
    };

    const removeFile = (file_path) => {
        setFilesInPrompt(prevFiles => {
            return prevFiles.filter(file => file !== file_path);
        });
    };

    const colorScale = scaleLinear()
        .domain([0, maxTokens / 2, maxTokens])
        .range(['green', 'yellow', 'red']);

    useEffect(() => {
        if (isSidebarOpen) {
            fetchSummaries();
        }
    }, [isSidebarOpen]);


    return (
        <div className={`fixed h-full w-1/3 right-0 bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full'} overflow-x-visible`}>
            <div className="flex flex-row justify-between items-center mb-2">
                <h2 className="text-xl font-bold mb-4 text-gray-100">Files and Summaries</h2>
            </div>
            {filesInPrompt.map((file, index) => {
                return (
                    <div className="flex justify-between items-center mb-1">
                        <p className=" mb-1 text-gray-100">{file}</p>
                        <AiOutlineMinus onClick={() => removeFile(file)} />
                    </div>
                )
            })}
            <hr className="border-gray-600 mb-4" />
            {summaries.map((summary, index) => {
                const colorStyle = {
                    color: colorScale(summary.file_token_count)
                };

                return (
                    <details>
                        <summary className="font-semibold hover:text-white cursor-pointer py-1">
                            {summary.file_path} &nbsp;
                            <span style={colorStyle}>{summary.file_token_count}</span> tokens
                        </summary>
                        <br />
                        {/* <p className="pl-2 text-sm">{summary.summary}</p> */}
                        <ReactMarkdown components={{ code: CodeBlock }} children={summary.summary} />
                        <br />
                        <hr className="border-gray-600" />
                    </details>
                );
            })}
        </div>

    );
};

export default RightSidebar;
