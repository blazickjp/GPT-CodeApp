import { configureStore } from '@reduxjs/toolkit';
import messageReducer from './messages/messagesSlice';
import sidebarReducer from './sidebar/sidebarSlice';
import systemPromptReducer from './modal_bar_modals/systemPromptSlice';
import functionsReducer from './modal_bar_modals/functionsSlice';
import messageHistoryReducer from './modal_bar_modals/messageHistorySlice';
import contextViewerReducer from './modal_bar_modals/contextViewerSlice';
import logMessagesReducer from './messages/logMessagesSlice';

export default configureStore({
    reducer: {
        messages: messageReducer,
        sidebar: sidebarReducer,
        systemPrompt: systemPromptReducer,
        functions: functionsReducer,
        messageHistory: messageHistoryReducer,
        logMessages: logMessagesReducer,
        contextViewer: contextViewerReducer,
    },
});