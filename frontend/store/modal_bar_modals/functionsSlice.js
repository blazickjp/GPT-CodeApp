import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    functions: [],
    functionTokens: 0,
    isFunctionModalOpen: false,
};

export const functionsSlice = createSlice({
    name: 'functions',
    initialState,
    reducers: {
        setFunctions: (state, action) => {
            state.functions = action.payload;
        },
        setFunctionTokens: (state, action) => {
            state.functionTokens = action.payload;
        },
        setIsFunctionModalOpen: (state, action) => {
            state.isFunctionModalOpen = action.payload;
        },
    },
});

export const { setFunctions, setFunctionTokens, setIsFunctionModalOpen } = functionsSlice.actions;

export default functionsSlice.reducer;