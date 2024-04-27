import React, { useState, useEffect, useRef } from 'react';
import { FaCog } from 'react-icons/fa';  // Importing an icon from react-icons
import { useDispatch } from 'react-redux';
import { setMessageTokens, } from '../store/modal_bar_modals/messageHistorySlice';
import { setDirectory, } from '@/store/sidebar/sidebarSlice';



const DirectorySelectOption = () => {
    const [placeholder, setPlaceholder] = useState('Loading...');
    const [tempDirectory, setTempDirectory] = useState('');
    const [actualTokens, setActualTokens] = useState(null);
    const [displayTokens, setDisplayTokens] = useState(null);
    const [temperature, setTemperature] = useState(0.5);
    const [showTooltip, setShowTooltip] = useState(false);


    const inputRef = useRef(null);
    const dispatch = useDispatch();

    const calculateTooltipPosition = (value) => {
        const slider = document.querySelector('.temperature-slider');
        if (slider) {
            const percent = (value - slider.min) / (slider.max - slider.min);
            return percent * slider.offsetWidth + 125; // Adjust '- 50' based on your tooltip width
        }
        return 0;
    };



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

        const fetchMaxTokens = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_max_message_tokens`)
                if (response.ok) {
                    const data = await response.json();
                    setActualTokens(data.max_message_tokens);
                    setDisplayTokens(data.max_message_tokens.toLocaleString());
                } else {
                    console.error('Error fetching max message tokens: ', response.statusText);
                }
            } catch (error) {
                console.error('Error fetching max message tokens: ', error);
            }
        };
        fetchHomeDirectory();
        fetchSavedDirectory();
        fetchMaxTokens();
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
            // setDirectory(placeholder);
            setTempDirectory(placeholder);
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

    // Function to update temperature setting via API
    const updateTemperatureSetting = async (newTemperature) => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/set_temperature`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ temperature: newTemperature }),
            });

            if (!response.ok) {
                throw new Error('Failed to update temperature setting');
            }

            console.log('Temperature setting updated successfully');
        } catch (error) {
            console.error('Error updating temperature setting:', error);
        }
    };

    return (
        <div className='overflow-x-scroll relative'>
            <FaCog className='text-2xl mb-6 text-yellow-400' />
            <span className='flex-grow ml-4'>Project Directory:</span>
            <form onSubmit={handleSubmit} className="p-2">
                <div className="flex flex-row items-center space-x-2 border-b border-gray-400 text-green-600">
                    <input
                        ref={inputRef}
                        id="directory"
                        type="text"
                        value={tempDirectory}
                        onChange={handleInputChange}
                        placeholder={placeholder}
                        onKeyDown={handleKeyDown}
                        className="flex-grow p-2 text-sm bg-transparent outline-none"
                    />
                </div>
            </form>
            {/* Input for Max token */}
            <div className='flex flex-row items-center mt-4 ml-4 space-y-2 sm:space-y-0'>
                <form onSubmit={handleSubmitTokens} className='flex items-center'>
                    <label className=' whitespace-nowrap'>Msg Tokens</label>
                    <input
                        type="text"
                        id={'maxTokens'}
                        value={displayTokens}
                        onChange={handleMaxTokensChange}
                        placeholder="2,000"
                        className='flex-grow text-green-600 p-2 text-sm items-end outline-none bg-transparent text-right'
                    />

                </form>
            </div>
            <div className="flex flex-grow items-center mt-4 mx-4 space-y-2 sm:space-y-0">
                <label className='flex flex-grow '>Temperature</label>
                <div onMouseEnter={() => setShowTooltip(true)} onMouseLeave={() => setShowTooltip(false)}>
                    <input
                        type="range"
                        className="bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 accent-green-600 temperature-slider"
                        min={0}
                        max={2}
                        step={0.1}
                        value={temperature}
                        onChange={(e) => {
                            const newTemp = parseFloat(e.target.value);
                            setTemperature(newTemp);
                            updateTemperatureSetting(newTemp);
                        }}
                    />
                    {showTooltip && (
                        <div
                            className='tooltip text-green-600'
                            style={{
                                position: 'absolute',
                                left: calculateTooltipPosition(temperature) + 'px',
                                bottom: '20px', // Adjust based on your layout
                                backgroundColor: 'transparent',
                                padding: '5px',
                                borderRadius: '5px',
                            }}
                        >
                            {temperature}
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
};

export default DirectorySelectOption;
