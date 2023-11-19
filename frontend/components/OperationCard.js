import React, { useState, useEffect } from 'react';
import { FiPlayCircle, FiInfo } from 'react-icons/fi'; // Example icons


const OperationCard = ({ operation }) => {
  const [opsToExecute, setOpsToExecute] = useState(null);

  const handleExecute = () => {
    // Logic to execute the operation
    console.log(`Executing operation: ${operation.name}`);
  };

  const handleDetails = () => {
    // Logic to show operation details
    console.log(`Showing details for operation: ${operation.name}`);
  };



  useEffect(() => {
    const fetchSystemState = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_ops`);
        console.log(response);
        const data = await response.json();
        setOpsToExecute(data.ops);
      } catch (error) {
        console.error('Error fetching system state:', error);
      }
    };

    fetchSystemState();
  }, []);



  return (
    <div className="bg-white shadow-md rounded p-4 max-w-sm w-full mx-auto my-4">
      <div className="flex justify-end mt-4">
        <button className="btn-blue flex items-center" onClick={handleExecute}>
          <FiPlayCircle className="mr-2" />
          Execute
        </button>
        <button className="btn-gray flex items-center ml-2" onClick={handleDetails}>
          <FiInfo className="mr-2" />
          Details
        </button>
      </div>
    </div>
  );
};

export default OperationCard;
