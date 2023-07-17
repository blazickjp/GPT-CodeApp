import React, { useState } from 'react';
import { GiLightningBranches, GiStarsStack } from 'react-icons/gi';

const ModelSelector = () => {
    const [activeButton, setActiveButton] = useState('gpt-3.5');

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

    const Button = ({ id, icon, text }) => (
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
    );

    return (
        <div className='inline-flex justify-center bg-gray-700 p-2 rounded-lg'> {/* You can adjust the color (bg-gray-800), padding (p-2), and roundness (rounded-lg) as needed */}
            <Button id="gpt-3.5" icon={<GiLightningBranches className=' text-green-500 mx-2' />} text="GPT-3.5" />
            < Button id="gpt-4" icon={< GiStarsStack className='text-purple-500 mx-2' />} text="GPT-4" />
        </div >
    );
};

export default ModelSelector;
