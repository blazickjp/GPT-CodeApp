
import React from 'react';
import ReactModal from 'react-modal';
import { useDispatch, useSelector } from 'react-redux';
import { setIsFunctionModalOpen } from '../../store/modal_bar_modals/functionsSlice';

const FunctionsModal = () => {
    const functions = useSelector(state => state.functions.functions);
    const isOpen = useSelector(state => state.functions.isFunctionModalOpen);
    const dispatch = useDispatch();

    return (
        <ReactModal
            isOpen={isOpen}
            onRequestClose={() => dispatch(setIsFunctionModalOpen(false))}
            shouldCloseOnOverlayClick={true}
            className="fixed inset-0 flex items-center justify-center m-96 w-auto"
            overlayClassName="fixed inset-0 bg-black bg-opacity-50"
        >
            <div className="relative bg-white rounded p-4 max-w-screen-lg mx-auto text-gray-900 overflow-scroll">
                <h2 className="text-xl">Functions</h2>
                <pre>
                    {functions?.map((f) => (
                        <div key={f?.name}>
                            <h3 className="text-lg">{f?.name}</h3>
                            <p>{f?.description}</p>
                            <hr />
                        </div>
                    ))}
                </pre>
            </div>
        </ReactModal>
    );
};

export default FunctionsModal;