import React, { useState, useEffect, use } from 'react';
import { GiLightningBranches, GiStarsStack } from 'react-icons/gi';
import { FaAmazon } from 'react-icons/fa';

const ModelSelector = () => {
    const [activeButton, setActiveButton] = useState('anthropic');
    const [modelStatus, setModelStatus] = useState('loading'); // ['loading', 'ready', 'error']

    const fetchCurrentModel = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_model`);
            if (!response.ok) {
                throw new Error('Failed to fetch current model');
            }
            const data = await response.json();
            setActiveButton(data.model); // Assuming response contains the model name
            setModelStatus('ready');
            console.log("Model Set: ", data.model);
        } catch (error) {
            console.error('Failed to fetch current model:', error);
            // Optionally, set a different model status here to reflect the error
            setModelStatus('error');
        }
    };


    const handleButtonClick = (e) => {
        console.log(e);
        setActiveButton(e);
        fetch('http://localhost:8000/set_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: e })
        }).then(response => {
            if (response.status === 200) {
                console.log('success');
            } else {
                // handle non-200 responses here
                console.log(`Response Error with Code: ${response.status}`)
            }
        }
        ).catch(error => {
            // handle request errors here
            console.error(error);
        }
        );
    };

    const Button = ({ id, icon, text }) => {
        return (
            <button
                id={id}
                type="button"
                onClick={() => handleButtonClick(id)}
                className={`group relative flex justify-center items-center py-2 rounded-lg px-6
                        ${activeButton === id ? "bg-gray-500 text-gray-200" : "bg-gray-700 text-gray-400"}
                        hover:opacity-100 transition-opacity duration-100 cursor-pointer hover:text-white`}
            >
                {icon}
                <span>{text}</span>
            </button>
        )
    };

    useEffect(() => {
        if (modelStatus !== 'ready') {
            const interval = setInterval(() => {
                // Need to keep trying until the backend has loaded the model, then stop
            }, 1000);
            fetchCurrentModel();
            // Clear interval when component unmounts or if modelStatus changes to 'ready'
            return () => clearInterval(interval);
        }
        if (modelStatus === 'ready') {
            console.log('Clean Interval');
            // return clearInterval(interval);

        }
    }, [modelStatus]);

    return (
        <div className='inline-flex justify-center bg-gray-700 p-2 rounded-lg'> {/* You can adjust the color (bg-gray-800), padding (p-2), and roundness (rounded-lg) as needed */}
            <Button id="gpt-3.5-turbo-1106" icon={<GiLightningBranches className=' text-green-500 mx-2' />} text="GPT-3.5" />
            < Button id="gpt-4-turbo" icon={< GiStarsStack className='text-purple-500 mx-2' />} text="GPT-4" />
            < Button id="anthropic" icon={< FaAmazon className='text-yellow-500 mx-2' />} text="Anth" />
        </div >
    );
};

export default ModelSelector;
