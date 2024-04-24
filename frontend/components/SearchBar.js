import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import { AiOutlineSend, AiFillPython } from 'react-icons/ai';
import { HiOutlineRefresh } from 'react-icons/hi';
import { DiJavascript1 } from 'react-icons/di'; // JS icon
import { MdDescription } from 'react-icons/md'; // Readme icon
import { FaPython } from 'react-icons/fa';


const SearchBar = ({ addFileToContext }) => {
    const [selectedOptions, setSelectedOptions] = useState(null);
    const [options, setOptions] = useState([]);
    const [refreshStatus, setRefreshStatus] = useState(null);  // Add this state
    const [fileStatus, setFileStatus] = useState(null);  // Add this state

    const timetout = 1000;
    const fileIcon = (fileType) => {
        switch (fileType) {
            case 'py':
                return <span className='text-python-blue'><FaPython /></span>
            case 'js':
                return <span className='text-yellow-500'><DiJavascript1 /></span>
            case 'md':
                return <span className="text-black"><MdDescription /></span>
            default:
                return null;
        }
    };
    // Modify the option labels
    const formatOptionLabel = ({ value, label }) => (
        <div className="flex items-center" title={value}>
            {fileIcon(value.split('.').pop())} <span className="ml-2">{label}</span>
        </div>
    );

    const handleChange = option => {
        setSelectedOptions(option);
    };

    const fetchFilesInContext = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_files_in_prompt`);
            const data = await response.json();
            // Assuming you have a state setter like setSelectedOptions
            setSelectedOptions(data.files.map(file => ({ label: file, value: file })));
        } catch (error) {
            console.error('Failed to fetch files in context:', error);
        }
    };


    const sendFiles = () => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/set_files_in_prompt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                files: selectedOptions ? [...selectedOptions.map(option => option.value)] : []
            })
        }).then(response => {
            if (response.status === 200) {
                setFileStatus('success');
                setTimeout(() => setFileStatus(null), timetout);
            } else {
                // handle non-200 responses here
                setFileStatus('warning');
                setTimeout(() => setFileStatus(null), timetout);
            }
        }).catch(error => {
            // handle request errors here
            console.error(error);
            setFileStatus('error');
            setTimeout(() => setFileStatus(null), timetout);
        });
    };

    const fetchSearchData = () => {
        setOptions([]);
        setRefreshStatus('loading');
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_summaries?reset=true`)
            .then(response => response.json())
            .then(data => {
                data.forEach(file => {
                    let group = file.file_path.split('/')[0];
                    setOptions(prevSummaries => [...prevSummaries, {
                        label: file.file_path.split('/').pop(),
                        value: file.file_path,
                        groups: group,
                        summary: file.summary,
                        file_token_count: file.file_token_count,
                        summary_token_count: file.summary_token_count
                    }]);
                    setRefreshStatus('success');
                    setTimeout(() => setRefreshStatus(null), timetout);  // Reset status after 2 seconds

                });
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
                setRefreshStatus('error');
                setTimeout(() => setRefreshStatus(null), timetout);  // Reset status after 2 seconds
            });
    };

    // This was taking too long everytime you make a change and need to refresh to UI
    useEffect(() => {
        fetchFilesInContext();
        sendFiles();
    }, []);


    // Define custom styles
    const customStyles = {
        control: (provided, state) => ({
            ...provided,
            backgroundColor: '#1F2937',  // bg-gray-800
            boxShadow: state.isFocused ? 5 : null,
            border: 'none',  // border-none
        }),

        valueContainer: (provided, state) => ({
            ...provided,
            flexWrap: 'wrap', // Prevent the options from wrapping to the next line
        }),

        input: (provided, state) => ({
            ...provided,
            margin: '0px',
            color: '#D1D5DB',  // text-gray-400
        }),
        indicatorSeparator: state => ({
            display: 'none',

        }),
        indicatorsContainer: (provided, state) => ({
            ...provided,
        }),
        option: (provided, { data, isDisabled, isFocused, isSelected }) => ({
            ...provided,
            backgroundColor: isSelected
                ? '#4B5563'  // bg-gray-700
                : isFocused
                    ? '#374151'  // bg-gray-600
                    : '#4B5563',
            ':active': {
                ...provided[':active'],
                backgroundColor: isSelected
                    ? '#4B5563'  // bg-gray-700
                    : '#374151',  // bg-gray-600
            },
        }),
        multiValue: (provided, state) => {
            return {
                ...provided,
                backgroundColor: '#4B5563',  // This is the background color for selected items
            };
        },
        multiValueLabel: (provided, state) => {
            return {
                ...provided,
                color: '#D1D5DB',  // This is the text color for selected items
            };
        },
        menu: (provided, state) => ({
            ...provided,
            // outline is equivalent to border but it doesn't affect layout - preferred for accessibility
            outline: '1px solid #D1D5DB', // Replace color as needed
            // Or if you prefer a border:
            // border: '1px solid #D1D5DB',
            boxShadow: '0px 0px 10px rgba(0, 0, 0, 0.1)', // Optional for extra styling (drop shadow)
        }),
        menuList: (provided, state) => ({
            ...provided,
            // This padding matches the border width, but could be customized
            padding: '1px',
        }),
    };

    return (
        <div className='flex flex-row w-full mb-4 justify-center'>
            <button className='text-purple-700 mr-5 text-lg' onClick={fetchSearchData} title="Refresh options">
                {refreshStatus === null && <HiOutlineRefresh className='text-purple-700' />}
                {refreshStatus === 'loading' && <div className='animate-spin rounded-full h-6 w-6 border-b-2 border-purple-700'></div>}
                {refreshStatus === 'success' && <HiOutlineRefresh className="text-green-500" />}  {/* Green check */}
                {refreshStatus === 'error' && <HiOutlineRefresh className="text-red-500" />}  {/* Red cross */}
            </button>
            <Select
                isMulti
                className='w-1/3 border-b-2 border-gray-500'
                options={options.sort((a, b) => a.groups.localeCompare(b.groups))}
                value={selectedOptions}
                onChange={handleChange}
                styles={customStyles}
                closeMenuOnSelect={false}
                blurInputOnSelect={false}
                formatOptionLabel={formatOptionLabel} // Use the custom format here
                placeholder='Add File to Context'
            />
            <button className='text-purple-700 ml-5 text-lg' onClick={sendFiles}>
                {fileStatus === null && <AiOutlineSend className='text-purple-700' />}
                {fileStatus === 'success' && <AiOutlineSend className="text-green-500" />}  {/* Green check */}
                {fileStatus === 'error' && <AiOutlineSend className="text-red-500" />}  {/* Red cross */}
            </button>

        </div>
    );
};

export default SearchBar;
