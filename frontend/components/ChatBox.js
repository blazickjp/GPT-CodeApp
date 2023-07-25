import React, { useRef, useEffect, useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { get_encoding } from "@dqbd/tiktoken";
import ReactTooltip from 'react-tooltip';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle } from '@fortawesome/free-solid-svg-icons';
import { Virtuoso } from 'react-virtuoso';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import { FaClipboardCheck } from 'react-icons/fa';
import { AiFillFileAdd } from 'react-icons/ai';
import DiffViewer from 'react-diff-viewer';


const encoding = get_encoding("cl100k_base");

// Modal Component
const Modal = ({ isOpen, handleClose, children, code, file, lang }) => {
    const handleInputChange = (event) => setInputValue(event.target.value);
    const [inputValue, setInputValue] = useState('');
    const [oldFile, setOldFile] = useState(null);
    const [newFile, setNewFile] = useState(null);
    const [firstLoad, setFirstLoad] = useState(true);
    const [status, setStatus] = useState(null);

    const createProgram = async (input, code, save, fileList) => {
        setStatus('loading');
        try {
            const response = await fetch(`http://127.0.0.1:8000/edit_files`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input: input, code: code, save: save, fileList: fileList }),
            });
            if (!response.ok) {
                setStatus('error');
                throw new Error('Network response was not ok');
            }
            setStatus('success');
            const data = await response.json();
            console.log(data);
            return data;
        } catch (error) {
            console.error('Failed to create program:', error);
        }
    };

    const firstSubmit = useCallback(async () => {
        console.log("First Submit");
        let data = await createProgram(inputValue, code, false, file);
        console.log(data.old_file);
        console.log(data.new_file);
        setOldFile(data.old_file);
        setNewFile(data.new_file);
    }, [inputValue, code, file]);  // add dependencies here

    useEffect(() => {
        if (isOpen && firstLoad) {
            firstSubmit();
            setFirstLoad(false);
        }
    }, [isOpen, firstLoad, firstSubmit]);


    const handleSave = () => {
        // setSave(true);
    };


    if (!isOpen) {
        return null;
    }

    return (
        <div className='relative inset-0 flex items-center justify-center border-2 border-red-500'>
            <div className='modal bg-onedark rounded-lg shadow-lg p-6 w-full max-h-96 overflow-scroll border-gray-400 border-2'>
                {status === 'loading' && (
                    <div className='flex flex-col mb-4 justify-center items-center'>
                        <div className='flex flex-row items-center justify-center'>
                            <p className='text-white'>Loading...</p>
                        </div>
                    </div>
                )}
                {oldFile && newFile && (
                    <div className='mt-4 items-center justify-center'>
                        <DiffViewer
                            oldValue={oldFile}
                            newValue={newFile}
                            splitView={true}
                            extraLinesSurroundingDiff={2}
                        />
                        <button onClick={handleSave} className='mt-4 bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline'>
                            Save
                        </button>
                        <button onClick={handleClose} className='mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline'>
                            Close
                        </button>
                    </div>
                )}
            </div>
        </div >
    );
};

// CodeBlock Component
const CodeBlock = React.memo(({ node, inline, className, children }) => {
    const [isOpen, setIsOpen] = useState(false);
    const handleOpen = () => setIsOpen(true);
    const handleClose = () => setIsOpen(false);

    const match = /language-(\w+)/.exec(className || '');
    const lang = match && match[1] ? match[1] : '';

    return !inline && match ? (
        <div className='relative bg-zinc-800 rounded overflow-x-scroll'>
            <text className='text-sm flex pt-2 pl-2'>{lang}</text>
            <button onClick={handleOpen} className='absolute top-2 right-2 text-sm mb-0 mr-10' data-tip data-for='addFileTip'>
                <AiFillFileAdd />
            </button>
            <ReactTooltip id='addFileTip' place="top" effect='solid'>
                Add code to file
            </ReactTooltip>
            <Modal isOpen={isOpen} handleClose={handleClose} code={String(children)} lang={lang} />
            <CopyToClipboard className='absolute top-2 right-2 text-sm mb-0' text={String(children)}>
                <button >
                    <FaClipboardCheck data-tip data-for='copyCodeTip' className='text-white' />
                </button>
            </CopyToClipboard>
            <ReactTooltip id='copyCodeTip' place="top" effect='solid'>
                Copy Code
            </ReactTooltip>
            <SyntaxHighlighter language={lang} style={oneDark}>
                {String(children)}
            </SyntaxHighlighter>
        </div>
    ) : (
        <code className={className}>{children}</code>
    );
});

const Chatbox = ({ messages }) => {
    const chatboxRef = useRef(null);
    const Row = ({ index, data }) => {
        const message = data[index];

        // If the message has no text, or if we don't have an encoding (e.g., if the model hasn't been loaded yet),
        // then don't render a row
        if (!message.text || !encoding) {
            return null;
        }

        // Encode the message text
        const tokens = encoding.encode(message.text);

        return (
            <div className={message.user === 'human' ? "bg-gray-700 text-white p-5" : "bg-gray-600 p-5 text-white"}>
                <div className='flex flex-row w-1/2 mx-auto'>
                    <FontAwesomeIcon icon={faInfoCircle} className="cursor-pointer mr-5" data-tip data-for={`tokenTip${index}`} />
                    <ReactTooltip id={`tokenTip${index}`} place="top" effect='solid' delayHide={500} globalEventOff='mouseout'>
                        Tokens: {tokens.length}
                    </ReactTooltip>
                    <ReactMarkdown children={message.text} className='flex-grow overflow-x-auto' components={{ code: CodeBlock }} />
                </div>
            </div>
        );
    };

    // Scroll to the latest message
    useEffect(() => {
        if (chatboxRef.current) {
            const timerId = setTimeout(() => {
                if (chatboxRef.current) {
                    chatboxRef.current.scrollToIndex({ index: messages.length - 1, align: 'end' });
                }
            }, 100);

            // Return a cleanup function that will be called when the component unmounts
            return () => {
                clearTimeout(timerId);
            };
        }
    }, [messages]);
    const random = Math.random();

    return (
        <div id={random} className='h-full overflow-y-auto'>
            <Virtuoso
                ref={chatboxRef}
                data={messages}
                itemContent={(index) => Row({ index, data: messages })}
            // style={{ height: '400px', width: '500px' }}
            />
        </div>
    );
};

export default Chatbox;
