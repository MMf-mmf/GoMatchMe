import React from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
// import { NotificationContextProvider } from './contexts/NotificationContext'


import Chat from './components/Chat'

export default function App() {
	return (
		<BrowserRouter>
			<Routes>
				<Route path="/chats/chat_room/:str/:uuid" element={<Chat />} />
				<Route path="/" element={<Chat />} />
			</Routes>
		</BrowserRouter>
	)
}
