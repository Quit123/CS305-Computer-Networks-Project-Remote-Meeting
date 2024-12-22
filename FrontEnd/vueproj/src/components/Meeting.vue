<template>
  <a-layout>
    <a-layout-header>
      <h1 style="color: white; text-align: center">{{ this.tittle }}</h1>
    </a-layout-header>
    <a-layout class="meeting-container">
      <a-layout-content class="video-section">
        <div class="video-grid">
          <div v-for="(video, index) in videos" :key="index" class="video-container">
            <canvas :ref="'video_' + video.user_id" width="640" height="360"/>
          </div>
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
import { Button, Input, Layout, Switch } from 'ant-design-vue';
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
      cameraOn: false,
      microphoneOn: true,
      socket: null,
      videos: [],
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
      axios.post('http://127.0.0.1:5000/api/update-camera-status');
    },
    toggleMicrophone() {
      axios.post('http://127.0.0.1:5000/api/update-audio-status');
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
        this.socket.emit('video_stream', { user_id: 'your_user_id' });
      });

      this.socket.on('video_frame', (data) => {
        const videoElements = this.$refs['video_' + data.user_id];  // 获取 canvas 元素数组

        if (videoElements && Array.isArray(videoElements)) {
          videoElements.forEach((videoElement) => {
            // 确保 videoElement 是 canvas 元素
            if (videoElement.getContext) {
              const ctx = videoElement.getContext('2d');
              const videoBlob = new Blob([data.frame], { type: 'image/jpeg' });
              const img = new Image();

              // 确保每次加载完成后释放 URL 对象，避免内存泄漏
              img.onload = () => {
                console.log('Video frame loaded successfully');
                ctx.drawImage(img, 0, 0, videoElement.width, videoElement.height);
                URL.revokeObjectURL(img.src);  // 释放内存
              };
              img.src = URL.createObjectURL(videoBlob);  // 创建图像 URL
            } else {
              console.error('The element is not a valid canvas');
            }
          });
        } else {
          console.warn(`Canvas for user ${data.user_id} not found.`);
          this.videos.push({ user_id: data.user_id });
        }
      });

      this.socket.on('message', (msg) => {
        this.messages.push(msg);
      });
    }

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

.video-section {
  display: flow-root;
  grid-template-columns: repeat(auto-fill, minmax(640px, 1fr)); /* 自动根据容器宽度填充视频 */
  gap: 10px; /* 控制视频间距 */
  justify-content: center;
  align-items: center;
}

.video-container canvas {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
}

.video-container {
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  position: relative;
}

.video-container canvas {
  position: absolute;
  width: 100%;
  height: 100%;
}

</style>
