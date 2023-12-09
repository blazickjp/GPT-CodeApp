
import React from 'react';
import ReactModal from 'react-modal';
import { useDispatch, useSelector } from 'react-redux';
import { setIsFunctionModalOpen } from '../../store/modal_bar_modals/functionsSlice';

const FunctionsModal = () => {
    const agentFunctions = useSelector(state => state.functions.agent_functions);
    const agentTokens = useSelector(state => state.functions.agent_tokens);
    const onDemandFunctions = useSelector(state => state.functions.on_demand_functions);
    const onDemandTokens = useSelector(state => state.functions.onDemandTokens);
    const isOpen = useSelector(state => state.functions.isFunctionModalOpen);
    const dispatch = useDispatch();

    return (
        <ReactModal
            isOpen={isOpen}
            onRequestClose={() => dispatch(setIsFunctionModalOpen(false))}
            shouldCloseOnOverlayClick={true}
            className="fixed inset-0 flex items-center justify-center w-1/2 h-1/2 mx-auto my-auto border border-gray-200 rounded"
            overlayClassName="fixed inset-0 bg-black bg-opacity-50"
        >
            <div className="relative bg-slate-600 rounded p-4 w-full h-full text-gray-200 overflow-scroll">
                <h2 className="text-xl pb-2">Agent Functions: {agentTokens} Tokens</h2>
                <hr />
                <div className='text-gray-400'>
                    Agent functions are automatically called by the agent when needed (like OpenAI indended).
                    You may create new functions in the <pre className='inline-block'>agent_functions.py</pre> file and add them to
                    the agent in the <pre className='inline-block'>setup_app.py</pre> file.
                </div>
                <br />
                {agentFunctions?.map((f) => (
                    <div key={f?.name} className='pt-2'>
                        <pre className="text-md "><strong>{f?.name}</strong></pre>
                        <p className='text-sm whitespace-pre'>{f?.description}</p>
                    </div>
                ))}
                <br /><br />
                <h2 className=" text-xl pb-2 pt-4">On Demand Functions: {onDemandTokens} Tokens</h2>
                <hr />
                <p className='text-gray-400'>
                    On Demand Functions can be run at any time and will not automatically be called by
                    your agent. When activated they will be run on the next turn of the conversation. We find
                    the best way to leverage on demand functions is to work within your normal chat to
                    develop a detailed prompt. Once you have one you like, copy and paste it into the
                    function call.
                </p>
                <br />
                {onDemandFunctions?.map((f) => (
                    <div key={f?.name} className='pt-2'>
                        <pre className="text-md "><strong>{f?.name}</strong></pre>
                        <p className='text-sm whitespace-pre'>{f?.description}</p>
                        {/* {f?.description} */}
                    </div>
                ))}
            </div>
        </ReactModal>
    );
};

export default FunctionsModal;