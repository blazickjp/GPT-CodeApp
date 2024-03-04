// frontend/store/modal_bar_modals/contextViewerSlice.js
import { createSlice } from '@reduxjs/toolkit';

export const contextViewerSlice = createSlice({
    name: 'contextViewer',
    initialState: {
        isModalOpen: false,
        workingContext: '',
    },
    reducers: {
        setIsContextModalOpen: (state, action) => {
            state.isModalOpen = action.payload;
        },
        setWorkingContext: (state, action) => {
            state.workingContext = action.payload;
        },
    },
});

export const { setIsContextModalOpen, setWorkingContext } = contextViewerSlice.actions;

export default contextViewerSlice.reducer;