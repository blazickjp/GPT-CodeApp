import React, { useEffect, useState } from 'react';
import { get_encoding } from "@dqbd/tiktoken";
import ReactModal from 'react-modal';
import FunctionsModal from './modal_bar_modals/FunctionsModal';
import SystemPromptModal from './modal_bar_modals/SystemPromptModal';
import MessageHistoryModal from './modal_bar_modals/MessageHistoryModal';
import ContextViewerModal from './modal_bar_modals/ContextViewerModal';
import { useDispatch, useSelector } from 'react-redux';
import { setSystemPrompt, setSystemTokens, setIsModalOpen, setEditablePrompt } from '../store/modal_bar_modals/systemPromptSlice';
import { setFunctionTokens, setIsFunctionModalOpen, setAgentFunctions, setAgentTokens, setOnDemandFunctions, setOnDemandTokens } from '../store/modal_bar_modals/functionsSlice';
import { setMessageHistory, setMessageTokens, setIsMessageModalOpen } from '../store/modal_bar_modals/messageHistorySlice';
import { setWorkingContext, setIsContextModalOpen } from '../store/modal_bar_modals/contextViewerSlice';






ReactModal.setAppElement('#__next');

const encoding = get_encoding("cl100k_base");

const ModalBar = () => {
    const dispatch = useDispatch();
    const systemTokens = useSelector(state => state.systemPrompt.systemTokens);
    const functionTokens = useSelector(state => state.functions.functionTokens);
    const messageTokens = useSelector(state => state.messageHistory.messageTokens);
    const editablePrompt = useSelector(state => state.systemPrompt.editablePrompt);
    const files = useSelector(state => state.sidebar.files);


    const fetchSystemPromptAndOpenModal = (modal = true) => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/system_prompt`)
            .then(response => response.json())
            .then(data => {
                dispatch(setEditablePrompt(data.system_prompt));
                dispatch(setSystemPrompt(data.system_prompt));
                const tokens = encoding.encode(data.system_prompt);
                dispatch(setSystemTokens(tokens.length));
                if (modal) {
                    dispatch(setIsModalOpen(true));
                }
            })
            .catch(console.error);
    };

    const fetchFunctionsAndOpenModal = (modal = true) => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_functions`)
            .then(response => response.json())
            .then(data => {
                dispatch(setAgentFunctions(data.agent_functions));
                dispatch(setOnDemandFunctions(data.on_demand_functions));
                if (modal) {
                    dispatch(setIsFunctionModalOpen(true));
                }
                let agent_tokens = 0;
                let on_demand_tokens = 0;
                data.agent_functions.forEach((f) => {
                    agent_tokens += encoding.encode(JSON.stringify(f)).length;
                });
                data.on_demand_functions.forEach((f) => {
                    on_demand_tokens += encoding.encode(JSON.stringify(f)).length;
                });
                // const f_tokens = encoding.encode(JSON.stringify(data.auto_functions[0]));
                dispatch(setFunctionTokens(agent_tokens));
                dispatch(setOnDemandTokens(on_demand_tokens));
                dispatch(setAgentTokens(agent_tokens));
            })
            .catch(console.error);
    };

    const fetchMessagesAndOpenModal = (modal = true) => {
        dispatch(setMessageHistory([]));
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_messages`)
            .then(response => response.json())
            .then(data => {
                dispatch(setMessageHistory(data.messages));
                if (modal) {
                    dispatch(setIsMessageModalOpen(true));
                }
                let m_tokens = 0;
                for (const message of data.messages) {
                    m_tokens += encoding.encode(message.content).length;
                }
                dispatch(setMessageTokens(m_tokens));
            })
            .catch(console.error);
    };

    useEffect(() => {
        fetchSystemPromptAndOpenModal(false);
        fetchFunctionsAndOpenModal(false);
        fetchMessagesAndOpenModal(false);
    }, []); //

    useEffect(() => {
        fetchSystemPromptAndOpenModal(false);
        fetchFunctionsAndOpenModal(false);
        fetchMessagesAndOpenModal(false);
    }, [editablePrompt, messageTokens]);

    return (
        <div className='flex flex-row mx-auto pb-3'>
            <div>
                <button onClick={fetchSystemPromptAndOpenModal}>
                    System Prompt:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {systemTokens}
                    </span>
                </button>
                <SystemPromptModal />
            </div>
            <div className='px-5'>
                < button onClick={fetchFunctionsAndOpenModal} >
                    Functions:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {functionTokens}
                    </span>
                </button >
                <FunctionsModal />
            </div >
            <div className='px-5'>
                <button onClick={fetchMessagesAndOpenModal}>
                    Message History:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {messageTokens}
                    </span>
                </button>
                <MessageHistoryModal />
            </div>
            <div className='px-5'>
                <button onClick={() => dispatch(setIsContextModalOpen(true))}>
                    Working Context
                </button>
                <ContextViewerModal />
            </div>

        </div >
    );
}

export default ModalBar;