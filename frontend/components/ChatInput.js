import React, { useState } from 'react';
import { AiOutlineSend, AiOutlineCloseCircle } from 'react-icons/ai';
import { Hint } from 'react-autocomplete-hint';
import PropTypes from 'prop-types';

const ChatInput = ({ onSubmit }) => {
    const [input, setInput] = useState('');
    const commands = ['/CommandPlan', '/Changes'];
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);

    const handlePaste = (event) => {
        event.preventDefault();
        const text = event.clipboardData.getData('text/plain');
        if (text) {
            setInput(input + text);
            return;
        }
        const file = event.clipboardData.files[0];
        if (file && file.type.startsWith('image')) {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64String = reader.result.split(',')[1];
                setFile(base64String);
                setPreviewUrl(reader.result);
            };
            reader.readAsDataURL(file);
        } else {
            alert('Unsupported file type');
        }
    };

    const handleRemoveImage = () => {
        setFile(null);
        setPreviewUrl(null);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log(file);
        if (input.trim() || file) {
            onSubmit(input, null, file);  // Handle the submission logic here
            setInput('');
            setFile(null);
            setPreviewUrl(null);
        }
    };

    return (
        <div className="flex flex-row bg-gray-800 text-center justify-center items-center w-full text-black pb-5">
            <form onSubmit={handleSubmit} className="relative w-1/2">
                <Hint options={commands} allowTabFill>
                    <input
                        type="text"
                        id='message-input'
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onPaste={handlePaste}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);

                            }
                        }}
                        placeholder="Type a message..."
                        className="p-2 rounded mr-2 flex-grow-2 pr-10 w-full"
                    />
                </Hint>
                {previewUrl && (
                    <div className="preview-container absolute right-20 top-0 bottom-0 m-auto flex items-center">
                        <img src={previewUrl} alt="Preview" className="max-w-xs max-h-32 rounded" />
                        <button
                            onClick={handleRemoveImage}
                            className="ml-2 text-red-500"
                            aria-label="Remove image"
                        >
                            <AiOutlineCloseCircle size={16} />
                        </button>
                    </div>
                )}
                <button
                    id='message-submit'
                    type="submit"
                    className="absolute right-0 top-0 bottom-0 m-auto text-purple-700 font-bold py-2 px-4 rounded text-xl"
                >
                    <AiOutlineSend />
                </button>
            </form>
        </div>
    );
};

// Define prop types for ChatInput
ChatInput.propTypes = {
    onSubmit: PropTypes.func.isRequired // Define the prop type and mark it as required
};

export default ChatInput;