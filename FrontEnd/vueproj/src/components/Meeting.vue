<template>
  <a-layout>
    <a-layout-header>
      <h1 style="color: white; text-align: center">{{ this.tittle }}</h1>
    </a-layout-header>
    <a-layout class="meeting-container">
      <a-layout-content class="video-section">
        <div class="video-container">
          <video ref="video" autoplay></video>
        </div>
        <div class="controls">
          <a-switch checked-children="Camera On" un-checked-children="Camera Off" v-model:checked="cameraOn"
                    @change="toggleCamera"/>
          <a-switch checked-children="Mic On" un-checked-children="Mic Off" v-model:checked="microphoneOn"
                    @change="toggleMicrophone"/>
          <a-button type="primary" class="exit-button" @click="exitMeeting">Exit Meeting</a-button>
        </div>
      </a-layout-content>
      <a-layout-sider class="chat-section" :width="250">
        <div class="chat-messages">
          <div v-for="(message, index) in messages" :key="index" class="chat-message">
            <strong>{{ message.user }}:</strong> {{ message.message }}
          </div>
        </div>
        <div class="chat-input">
          <a-input v-model:value.lazy="newMessage" @pressEnter="sendMessage" placeholder="Type a message..."/>
          <a-button @click="sendMessage">Send</a-button>
        </div>
      </a-layout-sider>
    </a-layout>
  </a-layout>
</template>

<script>
import { Layout, Button, Input, Switch } from 'ant-design-vue';
import io from 'socket.io-client';
import axios from "axios";

export default {
  components: {
    'a-layout': Layout,
    'a-layout-header': Layout.Header,
    'a-layout-content': Layout.Content,
    'a-layout-sider': Layout.Sider,
    'a-button': Button,
    'a-input': Input,
    'a-switch': Switch,
  },
  data() {
    return {
      tittle: 'SUSTeh CS303 Online Meeting App',
      messages: [],
      newMessage: '',
      cameraOn: true,
      microphoneOn: false,
      socket: null,
    };
  },
  methods: {
    sendMessage() {
      if (this.newMessage.trim()) {
        this.socket.emit('message', { user: 'You', message: this.newMessage });
        this.newMessage = '';
      }
    },
    toggleCamera() {
      axios.post('http://127.0.0.1:5000/api/update-audio-status');
    },
    toggleMicrophone() {
      axios.post('http://127.0.0.1:5000/api/update-camera-status');
    },
    async exitMeeting() {
      try {
        const response = await axios.post('http://127.0.0.1:5000/api/quit');
        if (response.data.status === 'success') {
          console.log('退出成功:', response.data);
          this.$router.push('/dashboard');
        } else {
          console.error('退出失败:', response.data);
          alert('退出失败，妮可不让你退出哦');
        }
      } catch (error) {
        console.error('退出失败:', error);
        alert('退出失败，妮可不让你退出哦');
      }
    },
    connectToSocket() {
      this.socket = io('http://127.0.0.1:5000');
      this.socket.on('connect', () => {
        console.log('WebSocket connected');
      });
      this.socket.on('video_frame', (data) => {
        const videoElement = this.$refs.video;
        if (videoElement) {
          videoElement.src = URL.createObjectURL(new Blob([data.frame], { type: 'image/jpeg' }));
        }
      });
      this.socket.on('message', (msg) => {
        this.messages.push(msg);
      });
    },
  },
  mounted() {
    this.connectToSocket();
  },
  beforeDestroy() {
    if (this.socket) {
      this.socket.disconnect();
    }
  },
};
</script>

<style scoped>
.meeting-container {
  height: 60vh;
  display: flex;
}

.video-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.video-container {
  position: relative;
  padding-top: 56.25%; /* 16:9 aspect ratio */
  background: black;
  display: flex;
  justify-content: center;
  align-items: center;
}

.video-container video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.controls {
  display: flex;
  justify-content: space-around;
  padding: 10px;
  border-top: 1px solid #ccc;
}

.chat-section {
  width: 400px;
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 10px;
  background: rgb(255, 255, 255); /* Add white background */
  border: 1px solid #ccc; /* Optional: Add border for better visibility */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Optional: Add shadow for better visibility */
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 10px;
  background: white; /* Ensure messages area has white background */
  padding: 10px; /* Optional: Add padding for better readability */
  border: 1px solid #ccc; /* Optional: Add border for better visibility */
  border-radius: 4px; /* Optional: Add border radius for better aesthetics */
}

.chat-input {
  display: flex;
  gap: 2px;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #ccc;
  position: fixed;
  bottom: 10px;
}

.exit-button {
  background-color: red;
  border-color: red;
  color: white;
}

.exit-button:hover {
  background-color: darkred;
  border-color: darkred;
}
</style>