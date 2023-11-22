import React, { useState, useEffect } from 'react';
import { scaleLinear } from 'd3-scale';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { AiOutlineMinus } from "react-icons/ai";
import OperationCard from './OperationCard';


const mockOperations = [
    {
        "type": "AddFunction",
        "file_name": "utils.py",
        "function_name": "calculate_sum",
        "args": "a, b",
        "body": "return a + b",
        "decorator_list": ["@staticmethod"],
        "returns": "int"
    },
    {
        "type": "DeleteClass",
        "file_name": "models.py",
        "class_name": "OldModel"
    },
    {
        "type": "ModifyMethod",
        "file_name": "services.py",
        "class_name": "PaymentService",
        "method_name": "process_payment",
        "new_args": "payment_info",
        "new_body": "if payment_info.valid: process_payment()",
        "new_decorator_list": ["@transaction.atomic"],
        "new_returns": "bool"
    },
    {
        "type": "AddClass",
        "file_name": "models.py",
        "class_name": "NewModel",
        "bases": ["BaseModel"],
        "body": "name = models.CharField(max_length=100)\ndef __str__(self):\n    return self.name",
        "decorator_list": ["@dataclass"]
    }
]


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
    const [OpsToExecute, setOpsToExecute] = useState(mockOperations);

    const fetchSummaries = () => {
        setSummaries([]);
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_summaries`)
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

    useEffect(() => {
        // TODO: Fetch operations from the backend and set them in state
        // For now, we'll use a static list
        // setOperations([
        //     { id: 1, name: 'Build Project', description: 'Compile and build the project.' },
        //     // ... other operations
        // ]);
    }, []);

    useEffect(() => {
        const fetchSystemState = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_ops`);
                console.log(response);
                const data = await response.json();
                setOpsToExecute(data.ops);
            } catch (error) {
                console.error('Error fetching system state:', error);
            }
        };

        fetchSystemState();
    }, []);


    return (
        <div className={`fixed h-full z-10 w-1/3 right-0 bg-neutral-800 transition-all duration-500 overflow-y-scroll p-6 text-gray-200 transform ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full'} overflow-x-visible`}>
            <div className="flex flex-row justify-between items-center mb-2">
                <h2 className="text-xl font-bold mb-4 text-gray-100">Available Ops</h2>
            </div>
            <hr className="border-gray-600 mb-4" />
            <div className="grid md:grid-cols-2 gap-4">
                {
                    mockOperations.map((operation, index) => (
                        <OperationCard key={index} operation={operation} />
                    ))
                }
            </div>
            <hr className="border-gray-600 my-4" />

            <div className="flex flex-row justify-between items-center mb-2">
                <h2 className="text-xl font-bold mb-4 text-gray-100">File Token Counts</h2>
            </div>
            <hr className="border-gray-600 mb-4" />
            {summaries.map((summary, index) => {
                const colorStyle = {
                    color: colorScale(summary.file_token_count)
                };

                return (
                    <details>
                        <summary className="flex font-semibold hover:text-white cursor-pointer py-1">
                            {summary.file_path} &nbsp;
                            <span style={colorStyle} className='flex items-center'>{summary.file_token_count}</span>
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
