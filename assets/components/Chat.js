import React, { useEffect, useState, useRef } from 'react'
import useWebSocket, { ReadyState } from 'react-use-websocket'
import InfiniteScroll from 'react-infinite-scroll-component'
import Message from './messages'
import { ActiveConversations } from './ActiveConversations'
import { ChatLoader } from './ChatLoader'
import { useHotkeys } from "react-hotkeys-hook"; // in our case it is used to treat the enter button as if the user clicked the submit button

const Chat = () => {
	const [messageHistory, setMessageHistory] = useState([])
	const [message, setMessage] = useState('')
	const [_x_chatToken, set_x_chatToken] = useState('')
	const [_x_username, set_x_username] = useState('')
	const [page, setPage] = useState(2)
	const [hasMoreMessages, setHasMoreMessages] = useState(false)
	const [participants, setParticipants] = useState([])
	const [conversation, setConversation] = useState([])
	const [conversationName, setConversationName] = useState('')
	const [meTyping, setMeTyping] = useState(false);
    const [typing, setTyping] = useState(false);
	const timeout = useRef()

	// Set the LocalStorage variables in the state
	useEffect(() => {
		setConversationName(getSecondToLastPartOfUrl())
		setTimeout(() => {
			// NOTE: the _x_chatToken is stored as a string with quotes around it and it works to send it as is to
			const chatToken = localStorage.getItem('_x_chatToken')
			const username = localStorage.getItem('_x_username')
			if (chatToken) {
				set_x_chatToken(chatToken)
			}
			if (username) {
				set_x_username(username.replace(/['"]/g, '')) // remove the quotes which are placed around the username when it is placed in the localStorage
			}
		}, 200)
	}, [])


	//127.0.0.1:8000/chats/messages/?conversation_name=mendel_test
	useEffect(() => {
		async function fetchConversation() {
			const apiRes = await fetch(`http://127.0.0.1:8000/chats/conversation/${conversationName}/`, {
				method: 'GET',
				headers: {
					Accept: 'application/json',
					'Content-Type': 'application/json',
					Authorization: `Token ${_x_chatToken.replace(/['"]/g, '')}`
				}
			})
			if (apiRes.status === 200) {
				const data = await apiRes.json()
				setConversation(data)
			}
		}
		// give the previous state time to fetch the tokens from localStorage
		setTimeout(() => {
			if (conversationName) {
				fetchConversation()
			}
		}, 350)
	}, [_x_chatToken])



	const getSecondToLastPartOfUrl = () => {
	const url = window.location.href;
	const parts = url.split('/').filter((part) => part.trim() !== ''); // Exclude empty parts
	return parts[parts.length - 2];
	};


	const { readyState, sendJsonMessage } = useWebSocket(
		_x_chatToken ? `ws://127.0.0.1:8000/ws/${conversationName}/` : null,
		{
			queryParams: {
				token: _x_chatToken ? _x_chatToken : ''
			},
			onOpen: () => {
				console.log('Connected!')
			},
			onClose: () => {
				console.log('Disconnected!')
			},
			// onMessage handler
			onMessage: (e) => {
				const data = JSON.parse(e.data)
				switch (data.type) {
					case 'last_50_messages':
						setMessageHistory(data.messages)
						setHasMoreMessages(data.has_more)
						break
					case 'chat_message_echo':
						setMessageHistory((prev) => [data.message, ...prev])
						sendJsonMessage({
							type: "read_messages",
						});
						break
					case 'user_join':
						setParticipants((pcpts) => {
							if (!pcpts.includes(data.user)) {
								return [...pcpts, data.user]
							}
							return pcpts
						})
						break
					case 'user_leave':
						setParticipants((pcpts) => {
							const newPcpts = pcpts.filter((x) => x !== data.user)
							return newPcpts
						})
						break
					case 'online_user_list':
						setParticipants(data.users)
						break
					case 'typing':
						updateTyping(data);
						break;
					default:
						bash.error('Unknown message type!')
						break
				}
			}
		}
	)

	const connectionStatus = {
		[ReadyState.CONNECTING]: 'Connecting',
		[ReadyState.OPEN]: 'Open',
		[ReadyState.CLOSING]: 'Closing',
		[ReadyState.CLOSED]: 'Closed',
		[ReadyState.UNINSTANTIATED]: 'Uninstantiated'
	}[readyState]


	// mark the messages as read when the connection is open
	useEffect(() => {
		if (connectionStatus === "Open") {
			sendJsonMessage({
			type: "read_messages"
			});
		}
	}, [connectionStatus, sendJsonMessage]);


	function updateTyping(event) {
		if (event.user !== _x_username) {
			setTyping(event.typing);
		}
	}

	function timeoutFunction() {
		setMeTyping(false);
		sendJsonMessage({ type: "typing", typing: false });
	}

	function onType() {
		if (meTyping === false) {
		setMeTyping(true);
		sendJsonMessage({ type: "typing", typing: true });
		timeout.current = setTimeout(timeoutFunction, 5000);
		} else {
		clearTimeout(timeout.current);
		timeout.current = setTimeout(timeoutFunction, 5000);
		}
	}

	function handleChangeMessage(e) {
		setMessage(e.target.value);
		onType();
	}

  useEffect(() => () => clearTimeout(timeout.current), []);
	const handleSubmit = () => {
		if (message.length === 0) return;
		if (message.length > 512) return;
		sendJsonMessage({
			type: 'chat_message',
			message
		})
		setMessage('')
		clearTimeout(timeout.current);
		timeoutFunction();
	}

const inputReference = useHotkeys(
  "enter",
  () => {
    handleSubmit();
  },
  {
    enableOnTags: ["INPUT"],
  }
);

useEffect(() => {
  if (inputReference.current !== null) {
    inputReference.current.focus();
  }
}, [inputReference]);


	async function fetchMessages() {
		const apiRes = await fetch(
			`http://127.0.0.1:8000/chats/messages/?conversation_name=${conversationName}&page=${page}`,
			{
				method: 'GET',
				headers: {
					Accept: 'application/json',
					'Content-Type': 'application/json',
					Authorization: `Token ${_x_chatToken}`
				}
			}
		)
		if (apiRes.status === 200) {
			const data = await apiRes.json()
			const { count, next, previous, results } = data
			setHasMoreMessages(next !== null)
			setPage(page + 1)
			setMessageHistory((prev) => prev.concat(results))
		}
	}

	return conversation.length < 1 ? null : (
		<div>
			<span>The WebSocket is currently {connectionStatus}</span>
			<hr />
			<div className="py-6">
				<h3 className="text-3xl font-semibold text-gray-900">
					Chat with user: {conversation.other_user.username}
				</h3>
				<hr />
				<span className="text-sm">
					{conversation.other_user.username} is currently
					{participants.includes(conversation.other_user.username) ? ' online' : ' offline'}
				
							{
					 typing && <p className="truncate text-sm text-gray-500">and typing...</p>
					}
				
					
				</span>
			</div>
			<hr />
			<div className="flex w-full items-center justify-between border border-gray-200 p-3">
				<input
				type="text"
				placeholder="Message"
				className="block w-full rounded-full bg-gray-100 py-2 outline-none focus:text-gray-700"
				name="message"
				value={message}
				onChange={handleChangeMessage}
				required
				ref={inputReference}
				maxLength={511}
				/>
				<button className="ml-3 bg-gray-300 px-3 py-1" onClick={handleSubmit}>
				Submit
				</button>
      		</div>
			<hr />
			{/* import the ActiveConversations component */}
			<h3>Active Conversations</h3>
			<hr />
			<ActiveConversations username={_x_username} _x_chatToken={_x_chatToken} />
			<hr />

			<div
				id="scrollableDiv"
				className="h-[40rem] mt-3 flex flex-col-reverse relative w-full border border-gray-200 overflow-y-auto p-6"
			>
				<div>
					{/* Put the scroll bar always on the bottom */}
					<InfiniteScroll
						dataLength={messageHistory.length}
						next={fetchMessages}
						className="flex flex-col-reverse" // To put endMessage and loader to the top
						inverse={true}
						hasMore={hasMoreMessages}
						loader={<ChatLoader />}
						scrollableTarget="scrollableDiv"
					>
						{messageHistory.map((message) => (
							<Message key={message.id} message={message} username={_x_username} />
						))}
					</InfiniteScroll>
				</div>
			</div>
		</div>
	)
}

export default Chat
