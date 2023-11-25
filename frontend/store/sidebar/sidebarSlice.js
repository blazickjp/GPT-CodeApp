import { createSlice } from '@reduxjs/toolkit';

export const sidebarSlice = createSlice({
    name: 'sidebar',
    initialState: { isOpen: false, currentDirectory: '' },
    reducers: {
        toggleSidebar: (state) => {
            state.isOpen = !state.isOpen;
        },
        setDirectory: (state, action) => {
            state.currentDirectory = action.payload;
        }
    },
});



export const { toggleSidebar, setDirectory } = sidebarSlice.actions;

export default sidebarSlice.reducer;