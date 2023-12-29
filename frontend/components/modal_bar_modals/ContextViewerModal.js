// frontend/components/modal_bar_modals/ContextViewerModal.js
import React, { useEffect, useState } from 'react';
import ReactModal from 'react-modal';
import { useDispatch, useSelector } from 'react-redux';
import { setIsContextModalOpen, setWorkingContext } from '../../store/modal_bar_modals/contextViewerSlice';

ReactModal.setAppElement('#__next');

const ContextViewerModal = () => {
    const dispatch = useDispatch();
    const isOpen = useSelector(state => state.contextViewer.isModalOpen);
    const workingContext = useSelector(state => state.contextViewer.workingContext);

    // const currentDirectory = useSelector(state => state.sidebar.currentDirectory);
    const fetchContext = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_context`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            // Do something with the context data, e.g., store in state, display in a modal, etc.
            dispatch(setWorkingContext(data.context));
            console.log(data.context);
        } catch (error) {
            console.error('There has been a problem with your fetch operation:', error);
        }
    };

    useEffect(() => {
        if (isOpen) {
            fetchContext();
        }
    }, [isOpen]);


    return (
        <ReactModal
            isOpen={isOpen}
            onRequestClose={() => dispatch(setIsContextModalOpen(false))}
            shouldCloseOnOverlayClick={true}
            className="fixed inset-0 flex items-center justify-center m-96 bg-gray-800 text-white border-blue-500"
            overlayClassName="fixed inset-0 bg-gray-800 bg-opacity-50"
        >
            <div className="relative flex flex-col bg-gray-800 rounded p-4 w-full mx-auto text-white border border-purple-200">
                <h2 className="text-xl">Working Context</h2>
                <textarea
                    value={workingContext}
                    readOnly
                    className="relative mt-2 w-full h-96 p-2 border bg-slate-600 rounded items-center justify-center"
                />
                <button
                    onClick={() => dispatch(setIsContextModalOpen(false))}
                    className="mt-4 ml-2 px-4 py-2 bg-purple-500 text-white rounded hover:bg-gray-600"
                >
                    Close
                </button>
            </div>
        </ReactModal>
    );
}

export default ContextViewerModal;