import { ChatUI } from './chat-ui.js';
import { ChatAPI } from './chat-api.js';

export class ChatApp {
  constructor(ui) {
    this.ui = ui;
    this.isSending = false;
    this.recognition = null;
    this.initSpeechRecognition();

    const voiceBtn = document.getElementById("voiceBtn");

    this.ui.sendBtn.addEventListener("click", () => this.handleSend());
    this.ui.input.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !this.isSending) {
        this.handleSend();
      }
    });

    if (voiceBtn) {
      voiceBtn.addEventListener("click", () => this.handleVoiceDirect());
    }
  }

  async ensureMicPermission() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (err) {
      console.error("麦克风权限获取失败：", err.name, err.message);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        alert("麦克风权限被拒绝，请点击地址栏左侧的锁图标，将麦克风权限设为“允许”，然后刷新页面。");
      } else {
        alert("无法访问麦克风：" + err.message);
      }
      return false;
    }
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("当前浏览器不支持语音识别");
      return;
    }
    this.recognition = new SpeechRecognition();
    this.recognition.lang = 'zh-CN';
    this.recognition.interimResults = false;
    this.recognition.maxAlternatives = 1;

    this.recognition.onerror = (event) => {
      console.error("语音识别错误：", event.error, event.message);
      this.ui.addMessage("assistant", `嗷呜…听不清呢 (${event.error})，再试试吧~`);
    };
    this.recognition.onend = () => {
      const btn = document.getElementById("voiceBtn");
      if (btn) btn.textContent = "🎤";
    };
  }

  async handleVoiceDirect() {
    if (this.isSending) return;
    if (!this.recognition) {
      alert("当前浏览器不支持语音识别，请使用 Chrome 或 Edge 哦~");
      return;
    }

    const hasPermission = await this.ensureMicPermission();
    if (!hasPermission) return;

    try {
      this.recognition.start();
      const btn = document.getElementById("voiceBtn");
      if (btn) btn.textContent = "🔴";
    } catch (e) {
      console.error("语音启动失败：", e);
      return;
    }

    const originalOnResult = this.recognition.onresult;
    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim();
      if (!transcript) return;

      this.ui.addMessage("user", transcript);
      this.ui.setSending(true);
      this.ui.showTyping();

      ChatAPI.voiceChat(transcript, {
        onStart: () => {},
        onAudio: (audioBlob) => {
          this.ui.hideTyping();
          this.ui.addMessage("assistant", "🔊 狐娘正在说话...");
          this.ui.playAudio(audioBlob);
          this.ui.setSending(false);
        },
        onError: (errMsg) => {
          this.ui.hideTyping();
          this.ui.setSending(false);
          this.ui.addMessage("assistant", `嗷呜…出错了：${errMsg}`);
        }
      });

      this.recognition.onresult = originalOnResult;
    };
  }

  async handleSend() {
    const message = this.ui.input.value.trim();
    if (!message || this.isSending) return;

    this.ui.addMessage("user", message);
    this.ui.clearInput();
    this.isSending = true;
    this.ui.setSending(true);
    this.ui.showTyping();

    let assistantBubble = null;
    let fullText = "";

    await ChatAPI.streamMessage(message, {
      onChunk: (chunk) => {
        if (!assistantBubble) {
          this.ui.hideTyping();
          assistantBubble = this.ui.addMessage("assistant", "");
        }
        fullText += chunk;
        assistantBubble.textContent = fullText;
        this.ui.scrollToBottom();
      },
      onDone: () => {
        this.ui.hideTyping();
        this.isSending = false;
        this.ui.setSending(false);
        if (!assistantBubble) {
          this.ui.addMessage("assistant", "（狐娘没有回答…可能是网络问题哦）");
        }
      },
      onError: (errMsg) => {
        this.ui.hideTyping();
        this.isSending = false;
        this.ui.setSending(false);
        this.ui.addMessage("assistant", `嗷呜…出错了：${errMsg}`);
      }
    });
  }
}

const ui = new ChatUI();
const app = new ChatApp(ui);
ui.input.focus();