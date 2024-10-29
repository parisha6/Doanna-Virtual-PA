import { createContext, useContext, useEffect, useState } from "react";

// Ingesting backend URL to be used for chat API requests
const backendUrl = "http://localhost:3000";

// Creating context for chat-related data and functions
const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  // Ingesting state to manage messages, current message, loading status, and camera zoom state
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);

  // Sending a chat message and fetching the response from the backend
  const chat = async (message) => {
    setLoading(true);  // Ingesting loading state to true while sending message

    // Fetching chat response from the backend
    const data = await fetch(`${backendUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),  // Sending the user's message in the request body
    });

    // Ingesting response data and updating message list
    const resp = (await data.json()).messages;
    setMessages((messages) => [...messages, ...resp]);  // Appending new messages to the existing list

    setLoading(false);  // Ingesting loading state to false after response is received
  };

  // Handling message playback by removing the played message from the queue
  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));  // Removing the first message from the list after playback
  };

  // Ingesting effect to update the current message whenever the message list changes
  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);  // Setting the current message to the first one in the list
    } else {
      setMessage(null);  // Clearing the current message if no messages are left
    }
  }, [messages]);  // Watching changes in the message list

  // Providing chat context with the available chat functions and states
  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

// Ingesting chat context using custom hook
export const useChat = () => {
  const context = useContext(ChatContext);  // Accessing context
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");  // Throwing an error if the hook is used outside the provider
  }
  return context;  // Returning context with chat-related values
};
