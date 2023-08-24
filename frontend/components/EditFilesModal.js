import React, { useState, useEffect, useCallback } from 'react';
import DiffViewer from 'react-diff-viewer';


// Modal Component
const EditFilesModal = ({ isOpen, handleClose, children, code, file, lang }) => {
    const handleInputChange = (event) => setInputValue(event.target.value);
    const [inputValue, setInputValue] = useState('');
    const [oldFile, setOldFile] = useState(null);
    const [newFile, setNewFile] = useState(null);
    const [firstLoad, setFirstLoad] = useState(true);
    const [status, setStatus] = useState(null);

    const createProgram = async (input, code, save, fileList) => {
        setStatus('loading');
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/edit_files`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input: input, code: code, save: save, fileList: fileList }),
            });
            if (!response.ok) {
                setStatus('error');
                throw new Error('Network response was not ok');
            }
            setStatus('success');
            const data = await response.json();
            console.log(data);
            return data;
        } catch (error) {
            console.error('Failed to create program:', error);
        }
    };

    const firstSubmit = useCallback(async () => {
        console.log("First Submit");
        let data = await createProgram(inputValue, code, false, file);
        console.log(data.old_file);
        console.log(data.new_file);
        setOldFile(data.old_file);
        setNewFile(data.new_file);
    }, [inputValue, code, file]);  // add dependencies here

    useEffect(() => {
        if (isOpen && firstLoad) {
            firstSubmit();
            setFirstLoad(false);
        }
    }, [isOpen, firstLoad, firstSubmit]);


    const handleSave = () => {
        // setSave(true);
    };


    if (!isOpen) {
        return null;
    }

    return (
        <div className='relative inset-0 flex items-center justify-center border-2 border-red-500'>
            <div className='modal bg-onedark rounded-lg shadow-lg p-6 w-full max-h-96 overflow-scroll border-gray-400 border-2'>
                {status === 'loading' && (
                    <div className='flex flex-col mb-4 justify-center items-center'>
                        <div className='flex flex-row items-center justify-center'>
                            <p className='text-white'>Loading...</p>
                        </div>
                    </div>
                )}
                {oldFile && newFile && (
                    <div className='mt-4 items-center justify-center'>
                        <DiffViewer
                            oldValue={oldFile}
                            newValue={newFile}
                            splitView={true}
                            extraLinesSurroundingDiff={2}
                        />
                        <button onClick={handleSave} className='mt-4 bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline'>
                            Save
                        </button>
                        <button onClick={handleClose} className='mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline'>
                            Close
                        </button>
                    </div>
                )}
            </div>
        </div >
    );
};

export default EditFilesModal;