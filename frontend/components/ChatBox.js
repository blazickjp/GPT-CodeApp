import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { get_encoding } from "@dqbd/tiktoken";
import ReactTooltip from 'react-tooltip';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle } from '@fortawesome/free-solid-svg-icons';


const encoding = get_encoding("cl100k_base");

const Chatbox = ({ messages }) => {
    const chatboxRef = useRef(null);

    const CodeBlock = ({ node }) => {
        if (node.properties.className) {
            const language = node.properties.className[0].replace("language-", "");
            const value = node.children[0].value;
            console.log("Language:", language);
            console.log("Value:", value);
            return (
                <SyntaxHighlighter language={language} style={oneDark} >
                    {value}
                </SyntaxHighlighter>
            );
        }
    };

    useEffect(() => {
        if (chatboxRef.current) {
            chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
        }
    }, [messages]);  // runs the effect whenever 'messages' changes

    return (

        <div id='chat-box' ref={chatboxRef} className='h-full overflow-y-auto'>
            {messages.map((message, index) => {
                const tokens = encoding.encode(message.text);
                return (
                    <div key={index} className={message.user === 'human' ? "bg-gray-700 text-white p-5" : "bg-gray-600 p-5 text-white"}>
                        <div className='flex flex-row w-1/2 mx-auto'>
                            <FontAwesomeIcon icon={faInfoCircle} className="cursor-pointer mr-5" data-tip data-for={`tokenTip${index}`} />
                            <ReactTooltip id={`tokenTip${index}`} place="top" effect='solid' delayHide={500} globalEventOff='mouseout'>
                                Tokens: {tokens.length}
                            </ReactTooltip>
                            <ReactMarkdown children={message.text} components={{ code: CodeBlock }} />
                        </div>
                    </div>
                )
            })}
        </div>
    );
};

export default Chatbox;