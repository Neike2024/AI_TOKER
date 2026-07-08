const API_ENDPOINT = "http://localhost:8000/chat-stream";
const VOICE_API_ENDPOINT = "http://localhost:8000/chat-voice";

export class ChatAPI {
  static async streamMessage(message, { onChunk, onDone, onError }) {
    try {
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });
      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`请求失败 (${response.status}): ${errText}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chars = [...buffer];
        buffer = "";
        for (const ch of chars) {
          onChunk(ch);
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      }
      if (buffer.length > 0) {
        for (const ch of buffer) {
          onChunk(ch);
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      }
      onDone();
    } catch (error) {
      onError(error.message);
    }
  }

  static async voiceChat(message, { onStart, onAudio, onError }) {
    try {
      onStart();
      const response = await fetch(VOICE_API_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });
      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`请求失败 (${response.status}): ${errText}`);
      }
      const audioBlob = await response.blob();
      onAudio(audioBlob);
    } catch (error) {
      onError(error.message);
    }
  }
}