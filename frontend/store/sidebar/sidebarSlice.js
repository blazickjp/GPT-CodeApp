import { createSlice } from '@reduxjs/toolkit';

export const sidebarSlice = createSlice({
    name: 'sidebar',
    initialState: {
        isOpen: false,
        currentDirectory: '',
        opList: [],
    },
    reducers: {
        toggleSidebar: (state) => {
            state.isOpen = !state.isOpen;
        },
        setDirectory: (state, action) => {
            state.currentDirectory = action.payload;
        },
        setOpList: (state, action) => {
            state.opList = action.payload;
        }

    },
});



export const { toggleSidebar, setDirectory, setOpList } = sidebarSlice.actions;

export default sidebarSlice.reducer;