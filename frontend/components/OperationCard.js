// OperationCard.js
import React, { useState } from 'react';
import { FiPlayCircle, FiInfo, FiLoader } from 'react-icons/fi'; // Example icons
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';

const OperationCard = ({ operation }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleExecute = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Replace the following console.log with your actual execution logic
      console.log(`Executing operation: ${operation.function_name || operation.class_name || operation.method_name}`);
      // Simulate an async operation; remove setTimeout in your actual implementation
      await new Promise((resolve) => setTimeout(resolve, 2000));
      // Operation succeeded
      setIsLoading(false);
    } catch (err) {
      // Operation failed: Handle error
      setError('Failed to execute operation');
      setIsLoading(false);
    }
  };


  const handleDetails = () => {
    // Logic to show operation details
    console.log(`Showing details for operation: ${operation.function_name || operation.class_name || operation.method_name}`);
  };

  return (
    <div className="bg-neutral-700 shadow-md rounded-lg p-4 max-w-sm w-full mx-auto my-4 text-gray-200">
      <div>
        <h3 className="text-lg font-bold mb-2">{operation.type}</h3>
        <p className="text-sm mb-1">File: <span className="font-medium">{operation.file_name}</span></p>
        {/* Display relevant operation details based on the operation type */}
        {operation.function_name && <p className="text-sm mb-1">Function: <span className="font-medium">{operation.function_name}</span></p>}
        {operation.class_name && <p className="text-sm mb-1">Class: <span className="font-medium">{operation.class_name}</span></p>}
        {operation.method_name && <p className="text-sm mb-1">Method: <span className="font-medium">{operation.method_name}</span></p>}
        {operation.body && (
          <div className="mt-2">
            <SyntaxHighlighter language="python" style={oneDark}>
              {operation.body}
            </SyntaxHighlighter>
          </div>
        )}
        {/* Add other details as necessary */}
      </div>
      <div className="flex justify-between mt-4">
        <button
          className={`p-2 rounded-full transition-colors duration-200 ease-in-out ${isLoading ? 'bg-blue-300' : 'bg-blue-500 hover:bg-blue-600'
            }`}
          onClick={handleExecute}
          title="Execute"
          disabled={isLoading}
        >
          {isLoading ? (
            <FiLoader className="animate-spin text-xl" />
          ) : error ? (
            <FiXCircle className="text-xl text-red-500" />
          ) : (
            <FiPlayCircle className="text-xl" />
          )}
        </button>
        <button
          className="p-2 bg-gray-600 hover:bg-gray-700 rounded-full transition-colors duration-200 ease-in-out"
          onClick={handleDetails}
          title="Details"
        >
          <FiInfo className="text-xl" />
        </button>
      </div>
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </div>

  );
};

export default OperationCard;