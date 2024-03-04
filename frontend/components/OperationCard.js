// OperationCard.js
import React, { useState, useEffect } from 'react';
import { FiPlayCircle, FiInfo, FiLoader } from 'react-icons/fi'; // Example icons
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { setOpList } from '../store/sidebar/sidebarSlice';
import { useDispatch, useSelector } from 'react-redux';


const OperationCard = ({ operation }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isClient, setIsClient] = useState(false);
  const dispatch = useDispatch();

  const executeOperation = async (operationId) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/execute_ops`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ op_id: operationId })
      });
      if (!response.ok) {
        throw new Error('Operation failed to execute');
      }
      const result = await response.json();
      // set op list
      dispatch(setOpList(result.ops));
      return result;
    } catch (error) {
      console.error('There was an error executing the operation:', error);
      throw error;
    }
  };


  const handleExecute = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log('Executing operation: ', operation.id)
      let result = await executeOperation(operation.id); // Pass the operation ID instead of the type and details
      console.log('Operation executed successfully');
      console.log('Result: ', result);

      // Handle success state here, maybe refresh data or provide user feedback
    } catch (err) {
      setError('Failed to execute operation');
      console.error(err);
    }
    setIsLoading(false);
  };


  const handleDetails = () => {
    // Logic to show operation details
    console.log(`Showing details for operation: ${operation.function_name || operation.class_name || operation.method_name}`);
  };

  useEffect(() => {
    // Once the component mounts, we know it's client-side
    setIsClient(true);
  }, []);

  return (
    <div className="bg-neutral-700 shadow-md rounded-lg p-4 max-w-sm w-full mx-auto my-4 text-gray-200 flex flex-col max-h-56"> {/* Added flex and flex-col */}
      <div className="flex-grow overflow-y-auto max-h-[200px]"> {/* Adjust the max height as needed */}
        <h3 className="text-lg font-bold mb-2">{operation.type}</h3>
        <div className="text-sm mb-2 font-bold">File: <pre className="font-medium inline">{operation.file_name}</pre></div>
        {/* Display relevant operation details based on the operation type */}
        {operation.function_name && <div className="text-sm mb-2 font-bold">Function: <pre className="font-medium inline">{operation.function_name}</pre></div>}
        {operation.class_name && <div className="text-sm mb-2 font-bold">Class: <pre className="font-medium inline">{operation.class_name}</pre></div>}
        {operation.method_name && <div className="text-sm mb-2 font-bold">Method: <pre className="font-medium inline">{operation.method_name}</pre></div>}
        {operation.body && (
          <div className="mt-2">
            {isClient && (
              <SyntaxHighlighter language="python" style={oneDark}>
                {operation.body}
              </SyntaxHighlighter>
            )}
          </div>
        )}
        {/* Add other details as necessary */}
      </div>
      <div className="flex justify-between mt-4"> {/* This is your footer area where the buttons are */}
        <button className={`p-2 rounded-full transition-colors duration-200 ease-in-out ${isLoading ? 'text-purple-300' : 'text-purple-500 hover:text-pruple-600'
          }`}
          onClick={handleExecute}
          title="Click to Execute Op" // Tooltip for execute button
          disabled={isLoading}
        >
          {isLoading ? (
            <FiLoader className="animate-spin text-xl" />
          ) : error ? (
            <FiInfo className="text-xl text-red-500" />
          ) : (
            <FiPlayCircle className="text-xl" />
          )}
        </button>
        <button
          className="p-2 text-gray-200 hover:text-gray-400 rounded-full transition-colors duration-200 ease-in-out"
          onClick={handleDetails}
          title="Refine Op - Not yet implemented" // Tooltip for details button
        >
          <FiInfo className="text-xl" />
        </button>
      </div>
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </div >

  );
};

export default OperationCard;