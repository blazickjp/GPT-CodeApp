import React, { useState, useEffect } from 'react';
import { scaleLinear } from 'd3-scale';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { BiCheckCircle } from 'react-icons/bi'; // import the icon
import { BiAddToQueue, BiBookAdd, BiRefresh } from 'react-icons/bi';
import ReactTooltip from "react-tooltip";
import { AiOutlineMinus, AiOutlineSend } from "react-icons/ai";

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
    const [bookIconScale, setBookIconScale] = useState(1);
    const [queueIconScale, setQueueIconScale] = useState(1);
    const [filesInPrompt, setFilesInPrompt] = useState([]);  // array of file paths
    const [summariesInPrompt, setSummariesInPrompt] = useState([]);  // array of file paths
    const [summaryStatus, setSummaryStatus] = useState(''); // add this line to your existing state declarations
    const [fileStatus, setFileStatus] = useState(''); // add this line to your existing state declarations

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

    const handleSummaryIconPress = (file_path) => {
        setBookIconScale(0.8);
        setSummariesInPrompt(prevSummaries => {
            if (!prevSummaries.includes(file_path)) {
                return [...prevSummaries, file_path];
            } else {
                return prevSummaries;
            }
        });
        setTimeout(() => setBookIconScale(1), 200);  // return to original size after 200ms
    };

    const handleFileIconPress = (file_path) => {
        setQueueIconScale(0.8);
        setFilesInPrompt(file => {
            if (!file.includes(file_path)) {
                return [...file, file_path];
            } else {
                return file;
            }
        }); setTimeout(() => setQueueIconScale(1), 200);  // return to original size after 200ms
    };

    const removeSummaryFile = (file_path) => {
        setSummariesInPrompt(prevSummaries => {
            return prevSummaries.filter(summary => summary !== file_path);
        });
    };

    const removeFile = (file_path) => {
        setFilesInPrompt(prevFiles => {
            return prevFiles.filter(file => file !== file_path);
        });
    };

    const sendSummaryFiles = () => {
        // assuming this function makes a call to your backend
        fetch("http://127.0.0.1:8000/set_summary_files_in_prompt", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ files: summariesInPrompt })
        }).then(response => {
            console.log(response.status);
            if (response.status === 200) {
                setSummaryStatus('success');
                setTimeout(() => setSummaryStatus(''), 1000);
            } else {
                console.log(response.status)
                setSummaryStatus('error');
                setTimeout(() => setSummaryStatus(''), 1000);
            }
        }).catch(error => {
            // handle request errors here
            console.error(error);
            setSummaryStatus('error');
        });
    };

    const sendFiles = () => {
        console.log(filesInPrompt);
        fetch('http://127.0.0.1:8000/set_files_in_prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ files: filesInPrompt })
        }).then(response => {
            if (response.status === 200) {
                setFileStatus('success');
                setTimeout(() => setFileStatus(''), 1000);
            } else {
                // handle non-200 responses here
                console.log(response.status)
                setFileStatus('error');
                setTimeout(() => setFileStatus(''), 1000);
            }
        }).catch(error => {
            // handle request errors here
            console.error(error);
            setFileStatus('error');
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
                const intensity = Math.floor((summary.file_token_count / maxTokens) * 100);
                const colorStyle = {
                    color: colorScale(summary.file_token_count)
                };

                return (
                    <details>
                        <summary className="font-semibold hover:text-white cursor-pointer py-1">
                            {summary.file_path} &nbsp;
                            <span style={colorStyle}>{summary.file_token_count}</span> tokens
                        </summary>
                        <div className='flex flex-row-reverse'>
                            <span data-tip={`Add Summary to Prompt (${summary.summary_token_count})`} data-for="addSummaryTip" className='mr-5 pl-1'>
                                <BiBookAdd className="inline" onClick={() => handleSummaryIconPress(summary.file_path)} style={{ transform: `scale(${bookIconScale})` }} />
                            </span>
                            <ReactTooltip id="addSummaryTip" place="top" effect='solid' />
                            <span data-tip={`Add File to Prompt (${summary.file_token_count})`} data-for="addFileTip">
                                <BiAddToQueue className="inline" onClick={() => handleFileIconPress(summary.file_path)} style={{ transform: `scale(${queueIconScale})` }} />
                            </span>
                            <ReactTooltip id="addFileTip" place="top" effect='solid' />
                        </div>
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
