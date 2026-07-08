export class ChatUI {
  constructor() {
    this.messageList = document.getElementById("messageList");
    this.input = document.getElementById("messageInput");
    this.sendBtn = document.getElementById("sendBtn");
    this.typingIndicator = null;
  }

  addMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;
    const senderSpan = document.createElement("span");
    senderSpan.className = "sender";
    senderSpan.textContent = role === "user" ? "你" : "狐娘";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    msgDiv.appendChild(senderSpan);
    msgDiv.appendChild(bubble);
    this.messageList.appendChild(msgDiv);
    this.scrollToBottom();
    return bubble;
  }

  showTyping() {
    this.typingIndicator = document.createElement("div");
    this.typingIndicator.className = "typing-indicator";
    this.typingIndicator.innerHTML = `
      <span>白狐正在思考</span>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    `;
    this.messageList.appendChild(this.typingIndicator);
    this.scrollToBottom();
  }

  hideTyping() {
    if (this.typingIndicator) {
      this.typingIndicator.remove();
      this.typingIndicator = null;
    }
  }

  scrollToBottom() {
    this.messageList.scrollTop = this.messageList.scrollHeight;
  }

  clearInput() {
    this.input.value = "";
    this.input.focus();
  }

  setSending(isSending) {
    this.input.disabled = isSending;
    this.sendBtn.disabled = isSending;
    if (!isSending) this.input.focus();
  }

  playAudio(audioBlob) {
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play().catch(e => console.warn("自动播放被阻止，请点击页面任意位置后再试", e));
    audio.onended = () => URL.revokeObjectURL(audioUrl);
  }
}