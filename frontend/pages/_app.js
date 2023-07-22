import '@/styles/globals.css'
import React from 'react';
import store from '../store';
import { Provider } from 'react-redux';



export default function App({ Component, pageProps }) {
  return (
    <React.StrictMode>
      <Provider store={store}>

        <Component {...pageProps} />
      </Provider>
    </React.StrictMode>
  )
};
