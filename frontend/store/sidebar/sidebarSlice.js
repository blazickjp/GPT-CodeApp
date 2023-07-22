import { createSlice } from '@reduxjs/toolkit';

export const sidebarSlice = createSlice({
    name: 'sidebar',
    initialState: { isOpen: false },
    reducers: {
        toggleSidebar: (state) => {
            state.isOpen = !state.isOpen;
        },
    },
});

export const { toggleSidebar } = sidebarSlice.actions;

export default sidebarSlice.reducer;