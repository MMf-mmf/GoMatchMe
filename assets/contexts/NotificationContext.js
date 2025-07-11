import React, { createContext, ReactNode, useContext, useState } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";


const DefaultProps = {
  unreadMessageCount: 0,
  connectionStatus: "Uninstantiated"
};



export const NotificationContext = createContext(DefaultProps);

export const NotificationContextProvider = ({ children }) => {
  // STATE
  const [unreadMessageCount, setUnreadMessageCount] = useState(0);
  const [_x_chatToken, set_x_chatToken] = useState('')
	const [_x_username, set_x_username] = useState('')


    // Set the LocalStorage variables in the state
    useEffect(() => {
      setConversationName(getLastPartOfUrl())
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

  const { readyState } = useWebSocket(
      _x_chatToken ? `ws://127.0.0.1:8000/ws/notifications/` : null,
		{
			queryParams: {
				token: _x_chatToken ? _x_chatToken : ''
			},
    onOpen: () => {
      console.log("Connected to Notifications!");
    },
    onClose: () => {
      console.log("Disconnected from Notifications!");
    },
    onMessage: (e) => {
      const data = JSON.parse(e.data);
      switch (data.type) {
        default:
          bash.error("Unknown message type!");
          break;
      }
    }
  });

  const connectionStatus = {
    [ReadyState.CONNECTING]: "Connecting",
    [ReadyState.OPEN]: "Open",
    [ReadyState.CLOSING]: "Closing",
    [ReadyState.CLOSED]: "Closed",
    [ReadyState.UNINSTANTIATED]: "Uninstantiated"
  }[readyState];

  return (
    <NotificationContext.Provider value={{ unreadMessageCount, connectionStatus }}>
      {children}
    </NotificationContext.Provider>
  );
};