import React, { useState, useEffect, useRef } from 'react';
import { FaArrowRight } from 'react-icons/fa';  // Importing an icon from react-icons

const DirectorySelectOption = () => {
    const [directory, setDirectory] = useState('');
    const [placeholder, setPlaceholder] = useState('Loading...');
    const inputRef = useRef(null);


    useEffect(() => {
        const fetchHomeDirectory = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_home`)
                if (response.ok) {
                    const data = await response.json();
                    setPlaceholder(data.home_directory);
                } else {
                    console.error('Error fetching home directory: ', response.statusText);
                    setPlaceholder('Error loading home directory');
                }
            } catch (error) {
                console.error('Error fetching home directory: ', error);
                setPlaceholder('Error loading home directory');
            }
        };

        fetchHomeDirectory();
    }, []);



    const handleInputChange = (e) => {
        setDirectory(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        console.log("Submitting directory: ", directory);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/select_directory`, {
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


    return (
        <form onSubmit={handleSubmit} className="p-2">
            <div className="flex flex-grow space-x-10 items-center align-middle border rounded-md overflow-hidden">
                <input
                    ref={inputRef}
                    type="text"
                    value={directory}
                    onChange={handleInputChange}
                    placeholder={placeholder}
                    onKeyDown={handleKeyDown}
                    className="flex-grow p-2 text-sm bg-transparent outline-none"
                />
                <button type="submit" className="px-4 py-2 bg-purple-600 text-white hover:bg-purple-800">
                    <FaArrowRight />
                </button>
            </div>
        </form>
    );
};

export default DirectorySelectOption;
