import { useRef, useState } from "react";
import { useChat } from "../hooks/useChat";

// Ingesting Web Speech API for speech recognition with browser compatibility check
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

export const UI = ({ hidden, ...props }) => {
  // Ingesting reference to the input field
  const input = useRef();

  // Ingesting chat-related functions and states from the custom hook `useChat`
  const { chat, loading, cameraZoomed, setCameraZoomed, message } = useChat();

  // Ingesting state to track whether voice recognition is listening
  const [listening, setListening] = useState(false);

  // Sending a text message
  const sendMessage = () => {
    const text = input.current.value;  // Getting input value
    // Ensuring chat isn't loading and no message is already being processed
    if (!loading && !message) {
      chat(text);  // Triggering the chat function
      input.current.value = "";  // Clearing input field after sending
    }
  };

  // Handling voice input using the SpeechRecognition API
  const handleVoiceInput = () => {
    // Checking if SpeechRecognition API is supported by the browser
    if (!SpeechRecognition) {
      alert("Speech Recognition API is not supported in this browser.");
      return;
    }

    // Creating a new instance of SpeechRecognition
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";  // Setting language for recognition
    recognition.interimResults = false;  // Disabling interim results (partial results)
    recognition.maxAlternatives = 1;  // Limiting the number of results

    // Ingesting event triggered when recognition starts
    recognition.onstart = () => setListening(true);

    // Ingesting event triggered when recognition ends
    recognition.onend = () => setListening(false);

    // Ingesting event triggered when a result is received
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;  // Extracting the recognized text
      input.current.value = transcript;  // Populating the input field with recognized text
      sendMessage();  // Automatically sending the recognized message
    };

    // Starting the speech recognition process
    recognition.start();
  };

  // Ignoring rendering if UI is hidden
  if (hidden) {
    return null;
  }

  return (
    <>
      <div className="fixed top-0 left-0 right-0 bottom-0 z-10 flex justify-between p-4 flex-col pointer-events-none">
        {/* Rendering Header Section */}
        <div className="self-start backdrop-blur-md bg-white bg-opacity-50 p-4 rounded-lg">
          <h1 className="font-black text-xl">Donna</h1>
          <p>Personalized Virtual Assistant</p>
        </div>

        {/* Rendering Control Buttons Section */}
        <div className="w-full flex flex-col items-end justify-center gap-4">
          {/* Toggling camera zoom */}
          <button
            onClick={() => setCameraZoomed(!cameraZoomed)}
            className="pointer-events-auto bg-black-500 hover:bg-gold-600 text-white p-4 rounded-md"
          >
            {cameraZoomed ? (
              // Displaying icon for zoomed-in camera
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM13.5 10.5h-6"
                />
              </svg>
            ) : (
              // Displaying icon for zoomed-out camera
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6"
                />
              </svg>
            )}
          </button>

          {/* Toggling green screen mode */}
          <button
            onClick={() => {
              const body = document.querySelector("body");
              if (body.classList.contains("greenScreen")) {
                body.classList.remove("greenScreen");
              } else {
                body.classList.add("greenScreen");
              }
            }}
            className="pointer-events-auto bg-black hover:bg-gray-800 text-white p-4 rounded-md"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-6 h-6"
            >
              <path
                strokeLinecap="round"
                d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"
              />
            </svg>
          </button>
        </div>

        {/* Displaying the avatar's response after a message is sent */}
        {message && message.text && (
          <div className="w-full flex justify-center mb-4">
            <p className="bg-white bg-opacity-90 p-2 rounded-md shadow-md max-w-sm text-center">
              {message.text}
            </p>
          </div>
        )}

        {/* Rendering Message Input and Buttons */}
        <div className="flex items-center gap-2 pointer-events-auto max-w-screen-sm w-full mx-auto">
          {/* Handling text input for typing a message */}
          <input
            className="w-full placeholder:text-gray-800 placeholder:italic p-4 rounded-md bg-opacity-50 bg-white backdrop-blur-md"
            placeholder="Type a message..."
            ref={input}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage();  // Sending message when Enter key is pressed
              }
            }}
          />

          {/* Handling microphone button to trigger voice input */}
          <button
            onClick={handleVoiceInput}
            className={`bg-black hover:bg-gray-800 text-white p-4 rounded-full ${listening ? "bg-green-500" : ""}`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 1.5a3.75 3.75 0 00-3.75 3.75v6A3.75 3.75 0 0012 15a3.75 3.75 0 003.75-3.75v-6A3.75 3.75 0 0012 1.5zM19.5 10.5v.75A7.5 7.5 0 0112 18.75a7.5 7.5 0 01-7.5-7.5v-.75M12 21.75v-3" />
            </svg>
          </button>

          {/* Handling send button to send the message */}
          <button
            disabled={loading || message}  // Disabling button if a message is being sent or is already being processed
            onClick={sendMessage}
            className={`bg-black hover:bg-gray-800 text-white p-4 px-10 font-semibold uppercase rounded-md ${loading || message ? "cursor-not-allowed opacity-30" : ""}`}
          >
            Send
          </button>
        </div>
      </div>
    </>
  );
};
