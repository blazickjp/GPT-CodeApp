import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const fetchMessages = createAsyncThunk('messages/fetchMessages', async () => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_messages?chatbox=true`);
    const historicalMessages = await response.json();
    const formattedMessages = historicalMessages.messages.map(message => ({
        text: message.full_content,
        user: message.role === 'user' ? 'human' : 'ai'
    }));
    return formattedMessages;
});


export const messageSlice = createSlice({
    name: 'messages',
    initialState: [],
    reducers: {
        addMessage: (state, action) => {
            state.push(action.payload);
        },
        addAIResponse: (state, action) => {
            state.push(action.payload);
        },
        addAIPartResponse: (state, action) => {
            if (state.length > 0) {
                console.log("State:", state);
                const lastMessage = { ...state[state.length - 1] };
                lastMessage.text = lastMessage.text + action.payload.text;
                state[state.length - 1] = lastMessage;
            }
            console.log(state);
            // setMessages(prevMessages => {
            //   // console.log(prevMessages);
            //   const lastMessage = { ...prevMessages[prevMessages.length - 1] };
            //   lastMessage.text = lastMessage.text + content;
            //   return [...prevMessages.slice(0, prevMessages.length - 1), lastMessage];
            // })
        },
    },
    extraReducers: (builder) => {
        builder.addCase(fetchMessages.fulfilled, (state, action) => {
            state.push(...action.payload);
        });
    },
});

export const { addMessage, addAIResponse, addAIPartResponse } = messageSlice.actions;

export default messageSlice.reducer;
