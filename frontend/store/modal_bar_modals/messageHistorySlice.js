import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    messageHistory: [],
    messageTokens: 0,
    isMessageModalOpen: false,
};

export const messageHistorySlice = createSlice({
    name: 'messageHistory',
    initialState,
    reducers: {
        setMessageHistory: (state, action) => {
            state.messageHistory = action.payload;
        },
        setMessageTokens: (state, action) => {
            state.messageTokens = action.payload;
        },
        setIsMessageModalOpen: (state, action) => {
            state.isMessageModalOpen = action.payload;
        },
    },
});

export const { setMessageHistory, setMessageTokens, setIsMessageModalOpen } = messageHistorySlice.actions;

export default messageHistorySlice.reducer;