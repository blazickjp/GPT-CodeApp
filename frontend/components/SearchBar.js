import React, { useState } from 'react';

const SearchBar = ({ onSearch }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const handleChange = event => {
        setSearchTerm(event.target.value);
    };

    const handleSubmit = event => {
        event.preventDefault();
        onSearch(searchTerm);
    };

    return (
        <div className='flex flex-col w-1/3 mb-5'>
            <form onSubmit={handleSubmit} className='flex felx-grow rounded'>
                <input
                    type="text"
                    placeholder="Add Files to Prompt"
                    className='w-full text-black rounded flex-grow'
                    value={searchTerm}
                    onChange={handleChange}
                    onKeyDown={(e) => e.key === 'Enter' ? handleSubmit(e) : null}
                />
            </form>
        </div>
    );
};

export default SearchBar;
