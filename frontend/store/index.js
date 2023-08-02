import { configureStore } from '@reduxjs/toolkit';
import messageReducer from './messages/messagesSlice';
import sidebarReducer from './sidebar/sidebarSlice';
import systemPromptReducer from './modal_bar_modals/systemPromptSlice';
import functionsReducer from './modal_bar_modals/functionsSlice';
import messageHistoryReducer from './modal_bar_modals/messageHistorySlice';

export default configureStore({
    reducer: {
        messages: messageReducer,
        sidebar: sidebarReducer,
        systemPrompt: systemPromptReducer,
        functions: functionsReducer,
        messageHistory: messageHistoryReducer,
    },
});