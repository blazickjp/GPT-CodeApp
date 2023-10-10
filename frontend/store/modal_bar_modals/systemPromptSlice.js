import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    systemPrompt: "",
    systemTokens: 0,
    isModalOpen: false,
    editablePrompt: "",
};

const systemPromptSlice = createSlice({
    name: 'systemPrompt',
    initialState,
    reducers: {
        setSystemPrompt: (state, action) => {
            state.systemPrompt = action.payload;
        },
        setSystemTokens: (state, action) => {
            state.systemTokens = action.payload;
        },
        setIsModalOpen: (state, action) => {
            state.isModalOpen = action.payload;
        },
        setEditablePrompt: (state, action) => {
            state.editablePrompt = action.payload;
        },
        setPromptName: (state, action) => {
            state.promptName = action.payload;
        }
    },
});

export const { setSystemPrompt, setSystemTokens, setIsModalOpen, setEditablePrompt, setPromptName } = systemPromptSlice.actions;

export default systemPromptSlice.reducer;