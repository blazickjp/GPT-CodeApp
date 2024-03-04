// frontend/store/modal_bar_modals/contextViewerSlice.js
import { createSlice } from '@reduxjs/toolkit';

export const logMessagesSlice = createSlice({
    name: 'logMessages',
    initialState: {
        isLogModalOpen: false,
        logMessages: [],
    },
    reducers: {
        setIsLogModalOpen: (state, action) => {
            state.isLogModalOpen = action.payload;
        },
        setLogMessages: (state, action) => {
            state.logMessages = action.payload;
        },
    },
});

export const { setIsLogModalOpen, setLogMessages } = logMessagesSlice.actions;

export default logMessagesSlice.reducer;