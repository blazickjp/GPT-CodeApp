import { configureStore } from '@reduxjs/toolkit';
import messageReducer from './messages/messagesSlice';
import sidebarReducer from './sidebar/sidebarSlice';

export default configureStore({
    reducer: {
        messages: messageReducer,
        sidebar: sidebarReducer
    },
});