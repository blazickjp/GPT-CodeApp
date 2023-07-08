import React, { useState } from 'react';
import { scaleLinear } from 'd3-scale';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { get_encoding } from "@dqbd/tiktoken";
import { MdAddChart } from 'react-icons/md';
import { AiOutlineFileMarkdown } from 'react-icons/ai';
import { FcList } from 'react-icons/fc';
import ReactTooltip from "react-tooltip";

const CodeBlock = ({ node, inline, className, children }) => {
    const match = /language-(\w+)/.exec(className || '')
    const lang = match && match[1] ? match[1] : ''
    console.log("Language:", lang);
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
    const [readme, setReadme] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const fetchSummaries = () => {
        setSummaries([]);
        fetch('http://127.0.0.1:8000/get_summaries')
            .then(response => response.json())
            .then(data => {
                const maxTokensFound = Math.max(...data.map(file => file.token_count));
                setMaxTokens(maxTokensFound); // Update the maxTokens state here
                data.forEach(file => {
                    setSummaries(prevSummaries => [...prevSummaries, { file_path: file.file_path, summary: file.summary, tokens: file.token_count }]);
                });
            })
            .catch(console.error);
    };

    const generateReadme = () => {
        setIsLoading(true);
        setReadme([]);
        // Fetch your data here
        fetch('http://127.0.0.1:8000/generate_readme')
            .then(response => response.json())
            .then(data => {
                setReadme(data.readme);
                console.log(data.readme);
                setIsLoading(false);
            })
            .catch(error => {
                console.error(error);
                setIsLoading(false);
            });
    };

    const addFile = (file_path) => {
        console.log("Adding file:", file_path);
    }

    const colorScale = scaleLinear()
        .domain([0, maxTokens / 2, maxTokens])
        .range(['green', 'yellow', 'red']);

    return (
        <div className={`fixed h-full w-2/5 right-0 bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full'}`}>
            {/* Add your sidebar content here */}
            <div className="flex flex-row justify-between items-center mb-4">
                <h2 className="text-2xl font-bold mb-4 text-gray-100">Project File Summaries</h2>
                <button onClick={fetchSummaries} className="py-1 px-2 bg-purple-500 text-white rounded hover:bg-purple-700 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-opacity-50">Fetch Summaries</button>
            </div>
            <hr className="border-gray-600 mb-4" />
            {summaries.map((summary, index) => {
                const intensity = Math.floor((summary.tokens / maxTokens) * 100);
                const colorStyle = {
                    color: colorScale(summary.tokens)
                };

                return (
                    <details>
                        <summary className="font-semibold hover:text-white cursor-pointer">
                            <span data-tip data-for="addFileTip">
                                <AiOutlineFileMarkdown className="inline" onClick={() => addFile(summary.file_path)} /> &nbsp;
                            </span>
                            <ReactTooltip id="addFileTip" place="top" effect="solid">
                                Add file to README.md
                            </ReactTooltip>
                            <span data-tip data-for="addSummaryTip">
                                <MdAddChart className="inline" /> {summary.file_path}:&nbsp;
                            </span>
                            <ReactTooltip id="addSummaryTip" place="top" effect="solid">
                                Add summary to README.md
                            </ReactTooltip>

                            <span style={colorStyle}>{summary.tokens}</span> tokens
                        </summary>
                        <br />
                        {/* <p className="pl-2 text-sm">{summary.summary}</p> */}
                        <ReactMarkdown components={{ code: CodeBlock }} children={summary.summary} />
                        <br />
                        <hr className="border-gray-600" />
                    </details>
                );
            })}
            <hr className="border-gray-600 mb-4" />

            <div className="flex flex-row justify-between items-center mb-4">
                <h2 className="text-2xl font-bold mb-4 text-gray-100">Project README.md</h2>
                <button
                    onClick={generateReadme}
                    className="py-1 px-2 bg-purple-500 text-white rounded hover:bg-purple-700 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-opacity-50">
                    {isLoading ? 'Loading...' : 'Generate README'}
                </button>
            </div>
            <ReactMarkdown components={{ code: CodeBlock }}>
                {readme}
            </ReactMarkdown>
        </div>

    );
};

export default RightSidebar;
