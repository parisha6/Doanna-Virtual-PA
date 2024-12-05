import { useRef, useState } from "react";
import { useChat } from "../hooks/useChat";

export const UI = ({ hidden, ...props }) => {
  const input = useRef();
  const { chat, loading, cameraZoomed, setCameraZoomed, message } = useChat();
  const [listening, setListening] = useState(false);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [enableFileOptions, setEnableFileOptions] = useState(false);
  const fileInputRef = useRef(null); // Add this in your component's top-level
  
  // // Handle sending a typed message
  // const sendMessage = () => {
  //   const text = input.current.value.trim().toLowerCase(); // Normalize user input
  //   const noteKeywords = ["transcribe", "convert to text"]; // Define note-related keywords

  //   if (!loading && !message) {
  //     // Check if user input contains any note-related keyword
  //     const containsNoteKeyword = noteKeywords.some((keyword) =>
  //       text.includes(keyword)
  //     );

  //     // Update the state based on whether note-related keywords are found
  //     setEnableFileOptions(containsNoteKeyword);

  //     if (containsNoteKeyword) {
  //       chat("Please say that upload your files using the Choose file button.");
  //     } else {
  //       chat(text);
  //     }

  //     input.current.value = ""; // Clear the input field
  //   }
  // };
  
  const sendMessage = async () => {
    const text = input.current.value.trim().toLowerCase(); // Normalize user input
    const noteKeywords = ["transcribe", "convert to text"]; // Define note-related keywords
    const kbKeywords = ["knowledge base", "kb"]; // Define knowledge base related keywords
  
    if (!loading && !message) {
      // Check if user input contains any note-related keyword
      const containsNoteKeyword = noteKeywords.some((keyword) =>
        text.includes(keyword)
      );
  
      // Check if user input contains any knowledge base related keyword
      const containsKBKeyword = kbKeywords.some((keyword) =>
        text.includes(keyword)
      );
  
      // Update the state based on whether note-related keywords are found
      setEnableFileOptions(containsNoteKeyword);
  
      if (containsNoteKeyword) {
        chat("Please say that upload your files using the Choose file button.");
      } else if (containsKBKeyword) 
        {
        try {
          // Call the RAG API
          const response = await fetch('http://localhost:3000/rag', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({message: input.current.value}),
          });
         
          const data = await response.text();
          console.log(data);
          const test="Please say this content:"+data;
          chat(test);
        } catch (error) {
          console.error('Error calling RAG API:', error);
        }
      } else 
      {
        chat(text);
      }
    }
    input.current.value = ""; // Clear the input field
  
  };
  
// // let isNoting = false;
// // let noteContent = "";

// // const handleVoiceInput = () => {
// //   const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

// //   if (!SpeechRecognition) {
// //     alert("Speech Recognition API is not supported in this browser.");
// //     return;
// //   }

// //   const recognition = new SpeechRecognition();
// //   recognition.lang = "en-US";
// //   recognition.interimResults = true;
// //   recognition.continuous = true;

// //   recognition.onstart = () => setListening(true);
// //   recognition.onend = () => {
// //     setListening(false);
// //     if (isNoting) {
// //       downloadTextFile(noteContent.trim());
// //       isNoting = false;
// //       noteContent = "";
// //     }
// //   };

// //   recognition.onresult = (event) => {
// //     const lastResultIndex = event.results.length - 1;
// //     const lastTranscript = event.results[lastResultIndex][0].transcript;

// //     if (!isNoting && (lastTranscript.toLowerCase().startsWith("note") || lastTranscript.toLowerCase().startsWith("take notes"))) {
// //       isNoting = true;
// //       noteContent = lastTranscript.substring(lastTranscript.indexOf(" ") + 1);
// //     } else if (isNoting && event.results[lastResultIndex].isFinal) {
// //       noteContent += "" + lastTranscript;
// //     }

// //     // input.current.value = lastTranscript;
// //   };

// //   recognition.start();
// // };

let isNoting = false;
let noteContent = "";
let recognition = null; // Declare recognition globally to control it explicitly

const handleVoiceInput = () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    alert("Speech Recognition API is not supported in this browser.");
    return;
  }

  // Initialize recognition if not already done
  if (!recognition) {
    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    // recognition.continuous = true;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => {
      setListening(false);
      if (isNoting) {
        if (noteContent.trim()) {
          // Only download if content is not empty
          downloadTextFile(noteContent.trim());
        }
        isNoting = false;
        noteContent = "";
      }
    };

    recognition.onresult = (event) => {
      const lastResultIndex = event.results.length - 1;
      const lastTranscript = event.results[lastResultIndex][0].transcript;

      if (!isNoting && (lastTranscript.toLowerCase().startsWith("note") || lastTranscript.toLowerCase().startsWith("take notes"))) {
        isNoting = true;
        noteContent = lastTranscript.substring(lastTranscript.indexOf(" ") + 1);
      } else if (isNoting && event.results[lastResultIndex].isFinal) {
        noteContent += " " + lastTranscript;
      }
      input.current.value = lastTranscript;
    };
  }

  // Start or stop recognition based on isNoting state
  if (listening) {
    recognition.stop(); // Stop listening
  } else {
    recognition.start(); // Start listening
  }
};

const downloadTextFile = (content) => {
  const element = document.createElement("a");
  const file = new Blob([content], {type: 'text/plain'});
  element.href = URL.createObjectURL(file);
  element.download = "note.txt";
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
  chat("Please say note taking is done successfully.");
};


  // Handle file selection
  const handleFileSelection = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type.startsWith("audio/")) {
      setFile(selectedFile);
    } else {
      alert("Please select a valid audio file.");
      setFile(null);
    }
  };

  // Handle transcription (call /transcript API)
  const handleSubmit = async () => {
    if (!file) {
      alert("Please select an audio file before submitting.");
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file); // Match the backend's expected field name

      const response = await fetch("http://localhost:3000/transcript", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Error calling /transcript API: ${response.statusText}`);
      }

      const data = await response.json();

      // Download transcription
      const transcripttext = data.messages[0].text;
      const blob = new Blob([transcripttext], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "transcription.txt";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      chat("Please say that Transcription successful!");

      // Reset state after successful transcription
      setFile(null);
      setEnableFileOptions(false);
      fileInputRef.current.value = ""; // Reset file input DOM element
    } catch (error) {
      console.error("Error handling transcription:", error);
      alert("Failed to process the transcription. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  if (hidden) {
    return null;
  }

  return (
    <>
      <div className="fixed top-0 left-0 right-0 bottom-0 z-10 flex justify-between p-4 flex-col pointer-events-none">
        <div className="self-start backdrop-blur-md bg-white bg-opacity-50 p-4 rounded-lg">
          <h1 className="font-black text-xl">Donna</h1>
          <p>Personalized Virtual Assistant</p>
        </div>
        <div className="w-full flex flex-col items-end justify-center gap-4">
          {/* Zoom Camera Button */}
          <button
            onClick={() => setCameraZoomed(!cameraZoomed)}
            className="pointer-events-auto bg-black-500 hover:bg-gold-600 text-white p-4 rounded-md"
          >
            {cameraZoomed ? (
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
        </div>
        {message && message.text && (
          <div className="w-full flex justify-center mb-4">
            <p className="bg-white bg-opacity-90 p-2 rounded-md shadow-md max-w-sm text-center">
              {message.text}
            </p>
          </div>
        )}
        <div className="flex items-center gap-2 pointer-events-auto max-w-screen-sm w-full mx-auto">
          {/* Text Input */}
          <input
            className="w-98 max-w-xl h-16 placeholder:text-gray-800 placeholder:italic p-4 rounded-md bg-opacity-50 bg-white backdrop-blur-md"
            placeholder="Type a message..."
            ref={input}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage();
              }
            }}
          />
          {/* Voice Input Button */}
          <button
            onClick={handleVoiceInput}
            className={`bg-black hover:bg-gray-800 text-white p-4 rounded-full ${listening ? "bg-green-500" : ""}`}
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
                strokeLinejoin="round"
                d="M12 1.5a3.75 3.75 0 00-3.75 3.75v6A3.75 3.75 0 0012 15a3.75 3.75 0 003.75-3.75v-6A3.75 3.75 0 0012 1.5zM19.5 10.5v.75A7.5 7.5 0 0112 18.75a7.5 7.5 0 01-7.5-7.5v-.75M12 21.75v-3"
              />
            </svg>
          </button>
          {/* File Upload Input */}
          <input
            type="file"
            accept="audio/*"
            ref={fileInputRef} // Attach ref
            onChange={handleFileSelection}
            className="bg-black hover:bg-gray-300 text-white p-4 px-2 rounded-md"
            disabled={!enableFileOptions || isUploading}
          />
          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            className="bg-black hover:bg-gray-800 text-white p-4 px-10 font-semibold uppercase rounded-md"
            disabled={!enableFileOptions || isUploading || !file}
          >
            Submit
          </button>
          {/* Send Button */}
          <button
            disabled={loading || message || enableFileOptions || isUploading}
            onClick={sendMessage}
            className={`bg-black hover:bg-gray-800 text-white p-4 px-10 font-semibold uppercase rounded-md ${
              loading || message || isUploading ? "cursor-not-allowed opacity-30" : ""
            }`}
          >
            Send
          </button>
        </div>
      </div>
    </>
  );
};
