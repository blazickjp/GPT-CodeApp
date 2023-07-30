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
import EditFilesModal from './EditFilesModal';

const encoding = get_encoding("cl100k_base");



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
            <EditFilesModal isOpen={isOpen} handleClose={handleClose} code={String(children)} lang={lang} />
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
