import { exec } from "child_process";
import cors from "cors";
import dotenv from "dotenv";
import voice from "elevenlabs-node";
import express from "express";
import { promises as fs } from "fs";
import OpenAI from "openai";
dotenv.config();
import multer from "multer";
import { Pinecone } from '@pinecone-database/pinecone';
const upload = multer({ storage: multer.memoryStorage() });

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const elevenLabsApiKey = process.env.ELEVEN_LABS_API_KEY;
const voiceID = "EXAVITQu4vr4xnSDxMaL";
const DEEPGRAM_API_KEY = "060a21416ed1aa2090b19b52720bf905442a3136";

const app = express();
app.use(express.json());
app.use(cors());
const port = 3000;

const pinecone = new Pinecone();

app.get("/", (req, res) => {
  res.send("Hello World!");
});

app.get("/voices", async (req, res) => {
  res.send(await voice.getVoices(elevenLabsApiKey));
});

const execCommand = (command) => {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) reject(error);
      resolve(stdout);
    });
  });
};

const lipSyncMessage = async (message) => {
  const time = new Date().getTime();
  console.log(`Starting conversion for message ${message}`);
  await execCommand(
    `ffmpeg -y -i audios/message_${message}.mp3 audios/message_${message}.wav`
    // -y to overwrite the file
  );
  console.log(`Conversion done in ${new Date().getTime() - time}ms`);
  await execCommand(
    `bin\\rhubarb -f json -o audios/message_${message}.json audios/message_${message}.wav -r phonetic`
  );
  // -r phonetic is faster but less accurate
  console.log(`Lip sync done in ${new Date().getTime() - time}ms`);
};

app.post("/chat", async (req, res) => {
  const userMessage = req.body.message;
  const completion = await openai.chat.completions.create({
    model: "gpt-3.5-turbo-1106",
    max_tokens: 1000,
    temperature: 0.6,
    response_format: {
      type: "json_object",
    },
    messages: [
      {
        role: "system",
        content: `
        Your name is donna.
        You are a personal assistant for Purdue fort wayne University students.
        You will always reply with a JSON array of messages. With a maximum of 3 messages.
        Each message has a text, facialExpression, and animation property.
        The different facial expressions are: smile, sad, angry, surprised, funnyFace, and default.
        The different animations are: Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, and Angry. 
        `,
      },
      {
        role: "user",
        content: userMessage || "Hello",
      },
    ],
  });
  let messages = JSON.parse(completion.choices[0].message.content);
  if (messages.messages) {
    messages = messages.messages; // ChatGPT is not 100% reliable, sometimes it directly returns an array and sometimes a JSON object with a messages property
  }
  for (let i = 0; i < messages.length; i++) {
    const message = messages[i];
    // generate audio file
    const fileName = `audios/message_${i}.mp3`; // The name of your audio file
    const textInput = message.text; // The text you wish to convert to speech
    await voice.textToSpeech(elevenLabsApiKey, voiceID, fileName, textInput);
    // generate lipsync
    await lipSyncMessage(i);
    message.audio = await audioFileToBase64(fileName);
    message.lipsync = await readJsonTranscript(`audios/message_${i}.json`);
  }

  res.send({ messages });
});

app.post("/transcript", upload.single("file"), async (req, res) => {
  
  try {
    // Ensure a file was uploaded
    if (!req.file) {
      return res.status(400).send({ error: "No file uploaded" });
    }
    
    // Send the uploaded file to Deepgram for transcription
    const deepgramResponse = await fetch("https://api.deepgram.com/v1/listen", {
      method: "POST",
      headers: {
        Authorization: `Token ${DEEPGRAM_API_KEY}`,
        "Content-Type": "audio/mp3", // Adjust this based on file type
      },
      body: req.file.buffer, // Use file buffer from multer
    });

    if (!deepgramResponse.ok) {
      const error = await deepgramResponse.json();
      return res.status(deepgramResponse.status).send({ error });
    }

    const deepgramData = await deepgramResponse.json();
    const texttranscript = deepgramData.results.channels[0].alternatives[0].transcript;
   
    // // Write transcription to a file
    // const filePath = path.join(__dirname, "transcription.txt");
    // fs.writeFileSync(filePath, texttranscript);
 
    //  // Send the file as a response
    // res.download(filePath, "transcription.txt", (err) => {
    //   if (err) {
    //     console.error("Error sending file:", err);
    //     res.status(500).send({ error: "Failed to send file." });
    //   }
    
    // fs.unlinkSync(filePath);
    // })
    
    // Create a message object with transcription text
    const messages = [
      {
        text: texttranscript,
        facialExpression: "smile",
        animation: "Talking_0",
      },
    ];

    // Generate audio and lipsync data
    for (let i = 0; i < messages.length; i++) {
      const message1 = messages[i];
      const fileName = `audios/message_${i}.mp3`; // The name of your audio file
      const fileInput1 = message1.text
      // Convert text to speech
      await voice.textToSpeech(elevenLabsApiKey, voiceID, fileName, fileInput1);

      // Generate lipsync data
      await lipSyncMessage(i);

      // Add audio and lipsync data to the message object
      message1.audio = await audioFileToBase64(fileName);
      message1.lipsync = await readJsonTranscript(`audios/message_${i}.json`);
    }

    res.send({ messages });
  }catch (error) {
    console.error("Error in /transcript:", error);
    res.status(500).send({ error: "Internal server error" });
  }
});


async function queryPinecone(query, topK = 3) {
  const index = pinecone.index("donna-cloud-kb");
  console.log(query);
  try {
    const embeddingResponse = await openai.embeddings.create({
      model: "text-embedding-3-small",
      input: query,
    });

    const queryEmbedding = embeddingResponse.data[0].embedding;

    const queryResult = await index.query({
      vector: queryEmbedding,
      topK,
      includeMetadata: true,
    });

    return queryResult.matches;
  } catch (error) {
    console.error('Error querying Pinecone:', error);
    return [];
  }
}

async function summarizeResults(results, userQuery) {
  const contentToSummarize = results.map(r => r.metadata.text).join('\n\n');
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        { role: "system", content: "You are a helpful assistant that summarizes information." },
        { role: "user", content: `Summarize the following information in response to the query: "${userQuery}"\n\n${contentToSummarize}` }
      ],
      max_tokens: 100
    });
    return response.choices[0].message.content;
  } catch (error) {
    console.error('Error summarizing results:', error);
    return 'Error generating summary';
  }
}


app.post("/rag", async (req, res) => {
  const userMessage = req.body.message;
  console.log("message from user",userMessage);
  if (!userMessage) {
    return res.status(400).json({ error: "Message is required" });
  }

  try {
    const results = await queryPinecone(userMessage, 3);
    console.log("Results**********",results);
    if (results.length > 0) {
      const summary = await summarizeResults(results, userMessage);
      console.log("Generated summary::::",summary);
      res.send(summary);     
    } 
  } catch (error) {
    console.error("Error in /rag:", error);
    res.status(500).send({ error: "Internal server error" });
  }
});

import { spawn } from 'child_process';

app.use(express.json()); // Parse JSON request bodies

app.post('/run-python', (req, res) => {
    const data = JSON.stringify(req.body); // Convert the body data to a JSON string

    // Spawn Python process
    const pythonProcess = spawn('python', ['script.py']); // Ensure the script.py is in the same directory or specify the path

    // Send data to Python script
    pythonProcess.stdin.write(data);
    pythonProcess.stdin.end();

    // Capture Python script output
    let result = '';
    pythonProcess.stdout.on('data', (chunk) => {
        result += chunk.toString(); // Append each chunk of data to the result string
    });

    pythonProcess.on('close', (code) => {
        if (code === 0) {
            try {
                res.json(JSON.parse(result)); // If successful, send parsed JSON data back to the frontend
            } catch (error) {
                res.status(500).send('Error parsing Python output');
            }
        } else {
            res.status(500).send('Python script failed'); // If Python script fails, return error
        }
    });
});



const readJsonTranscript = async (file) => {
  const data = await fs.readFile(file, "utf8");
  return JSON.parse(data);
};

const audioFileToBase64 = async (file) => {
  const data = await fs.readFile(file);
  return data.toString("base64");
};


app.listen(port, () => {
  console.log(`Donna listening on port ${port}`);
});