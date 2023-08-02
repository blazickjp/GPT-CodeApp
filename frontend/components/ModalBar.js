import React, { useEffect, useState } from 'react';
import { get_encoding } from "@dqbd/tiktoken";
import ReactModal from 'react-modal';
import FunctionsModal from './modal_bar_modals/FunctionsModal';
import SystemPromptModal from './modal_bar_modals/SystemPromptModal';
import MessageHistoryModal from './modal_bar_modals/MessageHistoryModal';
import { useDispatch, useSelector } from 'react-redux';
import { setSystemPrompt, setSystemTokens, setIsModalOpen, setEditablePrompt } from '../store/modal_bar_modals/systemPromptSlice';
import { setFunctions, setFunctionTokens, setIsFunctionModalOpen } from '../store/modal_bar_modals/functionsSlice';
import { setMessageHistory, setMessageTokens, setIsMessageModalOpen } from '../store/modal_bar_modals/messageHistorySlice';


ReactModal.setAppElement('#__next');

const encoding = get_encoding("cl100k_base");

const ModalBar = () => {
    const dispatch = useDispatch();
    const systemTokens = useSelector(state => state.systemPrompt.systemTokens);
    const functionTokens = useSelector(state => state.functions.functionTokens);
    const messageTokens = useSelector(state => state.messageHistory.messageTokens);


    const fetchSystemPromptAndOpenModal = (modal = true) => {
        fetch('http://127.0.0.1:8000/system_prompt')
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
        fetch('http://127.0.0.1:8000/get_functions')
            .then(response => response.json())
            .then(data => {
                dispatch(setFunctions(data.functions));
                if (modal) {
                    dispatch(setIsFunctionModalOpen(true));
                }
                const f_tokens = encoding.encode(JSON.stringify(data.functions[0]));
                dispatch(setFunctionTokens(f_tokens.length));
            })
            .catch(console.error);
    };

    const fetchMessagesAndOpenModal = (modal = true) => {
        dispatch(setMessageHistory([]));
        fetch('http://127.0.0.1:8000/get_messages')
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
                console.log(m_tokens);
                dispatch(setMessageTokens(m_tokens));
            })
            .catch(console.error);
    };

    useEffect(() => {
        fetchSystemPromptAndOpenModal(false);
        fetchFunctionsAndOpenModal(false);
        fetchMessagesAndOpenModal(false);
    }, []); //
    return (
        <div className='flex flex-row mx-auto pb-3'>
            <div>
                <button onClick={fetchSystemPromptAndOpenModal}>
                    System Prompt:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {systemTokens} tokens
                    </span>
                </button>
                <SystemPromptModal />
            </div>
            <div className='px-5'>
                < button onClick={fetchFunctionsAndOpenModal} >
                    Functions:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {functionTokens} tokens
                    </span>
                </button >
                <FunctionsModal />
            </div >
            <div className='px-5'>
                <button onClick={fetchMessagesAndOpenModal}>
                    Message History:
                    <span className="ml-2 inline-block bg-green-500 text-white text-xs px-2 rounded-full uppercase font-semibold tracking-wide">
                        {messageTokens} tokens
                    </span>
                </button>
                <MessageHistoryModal />
            </div>
        </div >
    );
}

export default ModalBar;