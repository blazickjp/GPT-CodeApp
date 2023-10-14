import React, { useState, useEffect, useRef } from 'react';
import { FaArrowRight } from 'react-icons/fa';  // Importing an icon from react-icons

const DirectorySelectOption = () => {
    const [directory, setDirectory] = useState('');
    const [placeholder, setPlaceholder] = useState('Loading...');
    const [tokens, setTokens] = useState(1000);
    const [actualTokens, setActualTokens] = useState(1000);
    const [displayTokens, setDisplayTokens] = useState('1000');
    const inputRef = useRef(null);


    useEffect(() => {
        const fetchHomeDirectory = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_home`)
                if (response.ok) {
                    const data = await response.json();
                    if (!placeholder) {
                        setPlaceholder(data.home_directory);
                    }
                } else {
                    console.error('Error fetching home directory: ', response.statusText);
                }
            } catch (error) {
                console.error('Error fetching home directory: ', error);
            }
        };

        const fetchSavedDirectory = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_directory`)
                if (response.ok) {
                    const data = await response.json();
                    setPlaceholder(data.directory);
                } else {
                    console.error('Error fetching home directory: ', response.statusText);
                }
            } catch (error) {
                console.error('Error fetching home directory: ', error);
            }
        };
        fetchHomeDirectory();
        fetchSavedDirectory();
    }, []);



    const handleInputChange = (e) => {
        setDirectory(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        console.log("Submitting directory: ", directory);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/set_directory`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ "directory": directory }),
            });

            if (response.ok) {
                console.log('Directory submitted successfully');
                window.location.reload();
            } else {
                console.error('Error submitting directory: ', response.statusText);
            }
        } catch (error) {
            console.error('Error submitting directory', error);
        }
    };

    const handleKeyDown = (e) => {
        console.log(e.key, inputRef.current)
        if (e.key === 'Tab' && inputRef.current) {
            e.preventDefault();  // Prevent focus from moving to the next element
            setDirectory(placeholder);
        }
    };

    const handleMaxTokensChange = (e) => {
        const newMaxTokens = parseInt(e.target.value.replace(/,/g, ''), 10);
        setActualTokens(newMaxTokens);
        setDisplayTokens(newMaxTokens.toLocaleString());
    };

    const setMaxMessageTokens = async (maxTokens) => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/set_max_message_tokens`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ "max_message_tokens": maxTokens }),
            });

            if (response.ok) {
                console.log('Max message tokens set successfully');
            } else {
                console.error('Error setting max message tokens: ', response.statusText);
            }
        } catch (error) {
            console.error('Error setting max message tokens', error);
        }
    };

    const handleSubmitTokens = async (e) => {
        e.preventDefault();
        console.log("Submitting max tokens: ", actualTokens);
        setMaxMessageTokens(actualTokens);

    }


    return (
        <div>
            <h3 className='text-lg'>Configurations</h3>
            <hr className='my-2 text-gray-300' />
            <form onSubmit={handleSubmit} className="p-2">
                <div className="flex flex-grow space-x-16 items-center align-middle border rounded-md overflow-hidden">
                    <input
                        ref={inputRef}
                        type="text"
                        value={directory}
                        onChange={handleInputChange}
                        placeholder={placeholder}
                        onKeyDown={handleKeyDown}
                        className="flex-grow p-2 text-sm bg-transparent outline-none"
                    />
                    <button type="submit" className="pr-2 py-2 text-purple-600">
                        <FaArrowRight />
                    </button>
                </div>
            </form>
            {/* Input for Max token */}
            <div className='flex flex-row items-center mb-4 ml-4 mt-2'>
                <text>Message Tokens</text>
                <form onSubmit={handleSubmitTokens} className='flex items-center'>
                    <input
                        type="text"
                        value={displayTokens}
                        onChange={handleMaxTokensChange}
                        placeholder="2,000"
                        className='flex-grow p-2 text-sm items-end outline-none bg-transparent text-right'
                    />
                    <button type="submit" className="px-4 py-2 ">
                        <FaArrowRight className='text-purple-600' />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default DirectorySelectOption;
