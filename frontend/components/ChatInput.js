import React, { useState } from 'react';
import { AiOutlineSend } from 'react-icons/ai';

const ChatInput = ({ onSubmit }) => {
    const [input, setInput] = useState("");

    const handleSubmit = (e) => {
        console.log("input", input);
        e.preventDefault();
        onSubmit(input);
        setInput("");
    };

    return (
        <div className="flex flex-row bg-gray-800 text-center justify-center items-center w-full text-black pb-5">
            <form onSubmit={handleSubmit} className='flex w-1/2'>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type a message..."
                    className="p-2 rounded mr-2 flex-grow"
                />
                <button type="submit" className=" text-purple-700 font-bold py-2 px-4 rounded text-xl">
                    <AiOutlineSend />
                </button>
            </form>
        </div>
    );
};

export default ChatInput;
