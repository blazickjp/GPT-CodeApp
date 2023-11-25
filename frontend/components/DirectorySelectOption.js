import React, { useState, useEffect, useRef } from 'react';
import { FaArrowRight } from 'react-icons/fa';  // Importing an icon from react-icons
import { useDispatch } from 'react-redux';
import { setMessageTokens, } from '../store/modal_bar_modals/messageHistorySlice';
import { setDirectory, } from '@/store/sidebar/sidebarSlice';



const DirectorySelectOption = () => {
    const [placeholder, setPlaceholder] = useState('Loading...');
    const [tempDirectory, setTempDirectory] = useState('');
    const [actualTokens, setActualTokens] = useState(1000);
    const [displayTokens, setDisplayTokens] = useState('1000');
    const inputRef = useRef(0);
    const dispatch = useDispatch();


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
    }, [placeholder]);



    const handleInputChange = (e) => {
        setTempDirectory(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        console.log("Submitting directory: ", tempDirectory);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/set_directory`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ "directory": tempDirectory }),
            });

            if (response.ok) {
                dispatch(setDirectory(tempDirectory));
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
                dispatch(setMessageTokens(maxTokens));
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
        <div className='overflow-x-scroll'>
            <h3 className='text-lg'>Config</h3>
            <form onSubmit={handleSubmit} className="p-2">
                <div className="flex space-x-2 items-center border-b border-gray-400 text-gray-200">
                    <input
                        ref={inputRef}
                        id={'directory'}
                        type="text"
                        value={tempDirectory}
                        onChange={handleInputChange}
                        placeholder={placeholder}
                        onKeyDown={handleKeyDown}
                        className="flex-grow p-2 text-sm bg-transparent outline-none"
                    />
                    <button type="submit" className="p-2">
                        <FaArrowRight className='text-purple-600' />
                    </button>
                </div>
            </form>
            {/* Input for Max token */}
            <div className='flex flex-row items-center mt-4 ml-4 space-y-2 sm:space-y-0'>
                <span className=' whitespace-nowrap'>Msg Tokens</span>
                <form onSubmit={handleSubmitTokens} className='flex items-center'>
                    <input
                        type="text"
                        id={'maxTokens'}
                        value={displayTokens}
                        onChange={handleMaxTokensChange}
                        placeholder="2,000"
                        className='flex-grow p-2 text-sm items-end outline-none bg-transparent text-right'
                    />
                    <button type="submit" className="px-2 py-1">
                        <FaArrowRight className='text-purple-600' />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default DirectorySelectOption;
