import React, { useState, useRef } from "react";
import axios from "axios";
import "./HomePage.css";

export default function HomePage() {
  const [file, setFile] = useState(null);
  const [recording, setRecording] = useState(false);
  const [audioURL, setAudioURL] = useState(null);
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setAudioURL(URL.createObjectURL(selectedFile));
    }
  };

  const startRecording = async () => {
    setRecording(true);
    audioChunksRef.current = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    mediaRecorderRef.current.ondataavailable = (e) => {
      audioChunksRef.current.push(e.data);
    };
    mediaRecorderRef.current.onstop = () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
      setAudioURL(URL.createObjectURL(audioBlob));
      setFile(audioBlob);
    };
    mediaRecorderRef.current.start();
  };

  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    setRecording(false);
  };
  
  const handleClear = () => {
    setFile(null);
    setAudioURL(null);
    setRecording(false);
    audioChunksRef.current = [];
    setName("");
    setAge("");
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select or record an audio file first!");
      return;
    }
    if (!name || !age) {
      alert("Please enter patient name and age!");
      return;
    }

    setLoading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", name);
    formData.append("age", age);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/upload_audio",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 120000,
        }
      );
      setMessage(`Upload successful!`);
    } catch (error) {
      console.error(error);
      if (error.response) {
        setMessage("Upload failed: " + JSON.stringify(error.response.data));
      } else if (error.code === "ECONNABORTED") {
        setMessage("Upload timed out. The audio might be too long.");
      } else {
        setMessage("Upload failed. Check backend server.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Medicare</h1>

      <div className="upload-section">
        <h2>Patient Details</h2>
        <input
          type="text"
          placeholder="Patient Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          type="number"
          placeholder="Age"
          value={age}
          onChange={(e) => setAge(e.target.value)}
        />

        <h2>Upload Audio</h2>
        <input type="file" accept="audio/*" onChange={handleFileChange} />
        {file && <p>Selected File: {file.name || "Recorded audio"}</p>}

        <h2>Or Record Audio</h2>
        <button onClick={recording ? stopRecording : startRecording}>
          {recording ? "Stop Recording" : "Start Recording"}
        </button>

        {audioURL && (
          <div>
            <p>Preview:</p>
            <audio controls src={audioURL}></audio>
          </div>
        )}

        <div className="button-group">
          <button onClick={handleUpload} disabled={loading}>
            {loading ? "Uploading..." : "Upload Audio"}
          </button>
          <button onClick={handleClear} className="clear-btn">
            Clear All
          </button>
        </div>

        {message && (
          <div className="message-box">
            <pre>{message}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
