import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import ReactTooltip from 'react-tooltip';
import { Virtuoso } from 'react-virtuoso';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import { FaClipboardCheck } from 'react-icons/fa';

const CodeBlock = React.memo(({ node, inline, className, children }) => {
    const match = /language-(\w+)/.exec(className || '');
    const lang = match && match[1] ? match[1] : '';
    return !inline && match ? (
        <div className='relative bg-zinc-800 my-4 rounded overflow-x-scroll'>
            <p className='text-sm flex pt-2 pl-2'>{lang}</p>
            <CopyToClipboard className='absolute top-2 right-2 text-sm mb-0' text={String(children)}>
                <button >
                    <FaClipboardCheck data-tip data-for='copyCodeTip' className='text-white' />
                </button>
            </CopyToClipboard>
            <ReactTooltip id='copyCodeTip' place="top" effect='solid'>
                Copy Code
            </ReactTooltip>
            <SyntaxHighlighter language={lang} style={oneDark} className='!mb-0 text-sm'>
                {String(children)}
            </SyntaxHighlighter>
        </div>
    ) : (
        <code className=" text-amber-500 ">{children}</code>
    );
});
CodeBlock.displayName = 'CodeBlock';

// const renderers = {
//     listItem: (props) => {
//         // Use a different className for top-level and nested list items if needed
//         const className = props.checked !== null ? "task-list-item" : "list-item";
//         return <li className={className}>{props.children}</li>;
//     },
//     // ... other renderers
// };



function CustomUnorderedListItem({ node, ordered, ...rest }) {
    return (
        <ul {...rest} ordered={ordered.toString()} className=' whitespace-normal list-inside list-disc' />
    )
}

function CustomListItem({ node, ordered, ...rest }) {
    return (
        <li {...rest} ordered={ordered.toString()} className=' whitespace-normal list-disc flex-wrap' />
    )
}

function CustomOrderedList({ node, ordered, ...rest }) {
    return (
        <ol {...rest} ordered={ordered.toString()} className=' whitespace-normal list-inside list-decimal' />
    )
}


const Chatbox = ({ messages }) => {
    const chatboxRef = useRef(null);
    const Row = ({ index, data }) => {
        const message = data[index];
        if (!message.text) {
            return null;
        }

        return (
            <div className={message.user === 'human' ? "bg-gray-700 text-white p-5" : "bg-gray-600 p-5 text-white"}>
                <div className='flex flex-row w-1/2 mx-auto whitespace-pre-wrap'>
                    <ReactMarkdown children={message.text} className='flex-grow overflow-x-auto' components={{ code: CodeBlock, ol: CustomOrderedList, ul: CustomUnorderedListItem, li: CustomListItem }} />
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
            />
        </div>
    );
};

export default Chatbox;
