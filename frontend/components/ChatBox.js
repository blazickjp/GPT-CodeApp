import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';


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

        <div id='chat-box' ref={chatboxRef} style={{ overflowY: 'scroll', height: '300px' }}>
            {messages.map((message, index) => (
                <div key={index} className={message.user === 'human' ? "bg-gray-700 text-white p-5" : "bg-gray-600 p-5 text-white"}>
                    <ReactMarkdown className="mx-auto w-1/2" children={message.text} components={{ code: CodeBlock }} />
                </div>
            ))}
        </div>
    );
};

export default Chatbox;