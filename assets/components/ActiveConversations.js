import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

export function ActiveConversations({ username, _x_chatToken }) {
	const [conversations, setActiveConversations] = useState([])

	useEffect(() => {
		async function fetchUsers() {
			const res = await fetch('http://127.0.0.1:8000/chats/conversations/', {
				headers: {
					Authorization: `Token ${_x_chatToken}`
				}
			})
			const data = await res.json()
			setActiveConversations(data)
		}
		fetchUsers()
	}, [username])

	function createConversationName(other_username) {
		const namesAlph = [other_username, username].sort()
		return `${namesAlph[0]}_${namesAlph[1]}`
	}

	function formatMessageTimestamp(timestamp) {
		// if (timestamp) return
		const date = new Date(timestamp)
		return date.toLocaleTimeString().slice(0, 5)
	}

	return (
		<div>
			{conversations.map((c, index) =>
				c.last_message ? (
					<div key={index}>
						<a href={`/chats/chat_room/${createConversationName(c.other_user.username)}`}>
							{c.other_user.username}
						</a>
						<span>Last Message: {c.last_message?.content}</span>
						<span>Timestamp: {formatMessageTimestamp(c.last_message?.timestamp)}</span>
					</div>
				) : null
			)}
		</div>
	)
}
