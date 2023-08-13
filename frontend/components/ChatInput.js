import React, { useState } from 'react';
import { AiOutlineSend } from 'react-icons/ai';
import { Hint } from 'react-autocomplete-hint';


const ChatInput = ({ onSubmit }) => {
    const [input, setInput] = useState('');
    const commands = ['/CommandPlan', '/Changes'];

    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.startsWith('/CommandPlan')) {
            onSubmit(input, 'CommandPlan');
            setInput('');
            return;
        }
        if (input.startsWith('/Changes')) {
            onSubmit(input, 'Changes');
            setInput('');
            return;
        }

        onSubmit(input);
        setInput('');
    };

    return (
        <div className="flex flex-row bg-gray-800 text-center justify-center items-center w-full text-black pb-5">
            <form onSubmit={handleSubmit} className="relative w-1/2">
                <Hint options={commands} allowTabFill>
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type a message..."
                        className="p-2 rounded mr-2 flex-grow-2 pr-10 w-full" // Increase flex-grow and add w-full
                    />
                </Hint>
                <button
                    type="submit"
                    className="absolute right-0 top-0 bottom-0 m-auto text-purple-700 font-bold py-2 px-4 rounded text-xl"
                >
                    <AiOutlineSend />
                </button>
            </form>
        </div>
    );
};

export default ChatInput;