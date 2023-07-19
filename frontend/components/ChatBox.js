import React, { useRef, useEffect } from 'react';
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


const encoding = get_encoding("cl100k_base");

const Chatbox = ({ messages }) => {
    const chatboxRef = useRef(null);

    const CodeBlock = React.memo(({ node, inline, className, children }) => {
        const match = /language-(\w+)/.exec(className || '');
        const lang = match && match[1] ? match[1] : '';
        console.log("Language:", lang);
        return !inline && match ? (
            <div className='relative bg-zinc-800 rounded'>
                <text className='text-sm flex pt-2 pl-2'>{lang}</text>
                <CopyToClipboard className='absolute top-2 right-2 text-sm mb-0' text={String(children)}>
                    <button >
                        <FaClipboardCheck className='text-white' />
                    </button>
                </CopyToClipboard>
                <SyntaxHighlighter language={lang} style={oneDark}>
                    {String(children)}
                </SyntaxHighlighter>
            </div>
        ) : (
            <code className={className}>{children}</code>
        );
    });

    const Row = ({ index, data }) => {
        console.log("Message Index:", index)
        const message = data[index];
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

    useEffect(() => {
        if (chatboxRef.current) {
            console.log(chatboxRef.current)
            setTimeout(() => {
                chatboxRef.current.scrollToIndex({ index: messages.length - 1, align: 'end' });
            }, 100); // Adjust the delay as needed
        }
    }, [messages]);  // runs the effect whenever 'messages' changes

    return (
        <div id='chat-box' className='h-full overflow-y-auto'>
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
