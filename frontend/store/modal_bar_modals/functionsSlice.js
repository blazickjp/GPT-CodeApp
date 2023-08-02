import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    agent_functions: [],
    on_demand_functions: [],
    agent_tokens: 0,
    onDemandTokens: 0,
    functionTokens: 0,
    isFunctionModalOpen: false,
};

export const functionsSlice = createSlice({
    name: 'functions',
    initialState,
    reducers: {
        setAgentFunctions: (state, action) => {
            state.agent_functions = action.payload;
        },
        setOnDemandFunctions: (state, action) => {
            state.on_demand_functions = action.payload;
        },
        setFunctionTokens: (state, action) => {
            state.functionTokens = action.payload;
        },
        setAgentTokens: (state, action) => {
            state.autoTokens = action.payload;
        },
        setOnDemandTokens: (state, action) => {
            state.onDemandTokens = action.payload;
        },
        setIsFunctionModalOpen: (state, action) => {
            state.isFunctionModalOpen = action.payload;
        },
    },
});

export const { setFunctionTokens, setIsFunctionModalOpen, setAgentFunctions, setOnDemandFunctions, setAgentTokens, setOnDemandTokens } = functionsSlice.actions;

export default functionsSlice.reducer;