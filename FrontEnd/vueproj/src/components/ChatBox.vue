<template>
  <div class="chat-box">
    <div class="messages">
      <div v-for="(message, index) in messages" :key="index" class="message">
        <strong>{{ message.user }}:</strong> {{ message.text }}
      </div>
    </div>
    <div class="input">
      <input v-model="newMessage" @keyup.enter="sendMessage" placeholder="Type a message..." />
      <button @click="sendMessage">Send</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      messages: [],
      newMessage: '',
    };
  },
  methods: {
    sendMessage() {
      if (this.newMessage.trim() !== '') {
        this.messages.push({ user: 'You', text: this.newMessage });
        this.newMessage = '';
        // Emit the message to the server or handle it as needed
      }
    },
  },
};
</script>

<style scoped>
.chat-box {
  width: 300px;
  background-color: #222;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px;
  border-left: 2px solid #ccc;
}

.messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
}

.message {
  margin-bottom: 8px;
}

.input {
  display: flex;
}

.input input {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  margin-right: 8px;
  color: #000;
}

.input button {
  padding: 8px 16px;
  background-color: #1890ff;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
}
</style>