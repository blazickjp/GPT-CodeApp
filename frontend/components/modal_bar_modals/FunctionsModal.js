The new file "FunctionsModal.js" will contain the code for the functions modal. Here is the content of the file:

```jsx
import React from 'react';
import ReactModal from 'react-modal';

const FunctionsModal = ({ isOpen, onRequestClose, functions }) => {
    return (
        <ReactModal
            isOpen={isOpen}
            onRequestClose={onRequestClose}
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
```

This component receives three props: `isOpen`, `onRequestClose`, and `functions`. `isOpen` is a boolean that determines whether the modal is open or not. `onRequestClose` is a function that will be called when the user requests to close the modal (for example, by clicking on the overlay). `functions` is an array of function objects, each with a `name` and `description` property, which will be displayed in the modal.