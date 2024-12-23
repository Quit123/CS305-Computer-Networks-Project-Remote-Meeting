<template>
  <a-layout>
    <a-layout-header>
      <h1 style="color: white; text-align: center">{{ this.tittle }}</h1>
    </a-layout-header>
    <a-layout class="meeting-container">
      <a-layout-content class="video-section">
        <div class="video-grid">
          <div v-for="(video, index) in videos" :key="index" class="video-container">
            <canvas :ref="'video_' + video.user_id" width="270" height="150"/>
          </div>
        </div>
        <div class="screen-share">
          <canvas ref="screenCanvas" width="1080" height="720"/>
        </div>
        <div class="controls">
          <a-switch checked-children="Camera On" un-checked-children="Camera Off" v-model:checked="cameraOn"
                    @change="toggleCamera"/>
          <a-switch checked-children="Mic On" un-checked-children="Mic Off" v-model:checked="microphoneOn"
                    @change="toggleMicrophone"/>
          <a-button type="primary" class="exit-button" @click="exitMeeting">Exit Meeting</a-button>
          <a-button type="danger" class="cancel-button" @click="cancelMeeting">Cancel Meeting</a-button>
          <a-button
            :type="isSharingScreen ? 'danger' : 'default'"
            @click="toggleScreenShare"
            class="hover-button"
          >
            {{ isSharingScreen ? 'Close Share' : 'Share Screen' }}
          </a-button>
        </div>
      </a-layout-content>
      <a-layout-sider class="chat-section" :width="250">
        <div class="chat-messages">
          <div v-for="(message, index) in messages" :key="index" class="chat-message">
            <strong>{{ message.user }}:</strong> {{ message.message }} <span class="timestamp">{{ message.time }} </span>
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
      isSharingScreen: false,
    };
  },
  methods: {
    sendMessage() {
      if (this.newMessage.trim()) {
        this.socket.emit('message',{message: this.newMessage})
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
    async cancelMeeting() {
      try {
        const response = await axios.post('http://127.0.0.1:5000/api/cancel');
        if (response.data.status === 'success') {
          console.log('取消成功:', response.data);
          this.$router.push('/dashboard');
        } else {
          console.error('取消失败:', response.data);
          alert('取消失败，妮可不让你取消哦');
        }
      } catch (error) {
        console.error('取消失败:', error);
        alert('取消失败，妮可不让你取消哦');
      }
    },
    connectToSocket() {
      this.socket = io('http://127.0.0.1:5000');
      this.socket.on('connect', () => {
        console.log('WebSocket connected');
        this.socket.emit('video_stream', {user_id: 'your_user_id'});
      });

      this.socket.on('host_info', (data) => {
        console.log('Host info:', data);
        data.message.success("主机信息：" + data);
      });

      this.socket.on('quit_info', (data) => {
        console.log('Quit info:', data);
        data.message.success("退出信息：" + data);
        this.$router.push('/dashboard');
      });

      this.socket.on('screen_frame', (data) => {
        const screenCanvas = this.$refs.screenCanvas;  // 获取 canvas 元素

        const ctx = screenCanvas.getContext('2d');
        const screenBlob = new Blob([data.screen_frame], {type: 'image/jpeg'});
        const img = new Image();

        // 确保每次加载完成后释放 URL 对象，避免内存泄漏
        img.onload = () => {
          console.log('Screen frame loaded successfully');
          ctx.drawImage(img, 0, 0, screenCanvas.width, screenCanvas.height);
          URL.revokeObjectURL(img.src);  // 释放内存
        };
        img.src = URL.createObjectURL(screenBlob);  // 创建图像 URL
      });

      this.socket.on('video_frame', (data) => {
        const videoElements = this.$refs['video_' + data.user_id];  // 获取 video 元素

        if (videoElements && Array.isArray(videoElements)) {
          videoElements.forEach((videoElement) => {
            // 确保 videoElement 是 canvas 元素
            if (videoElement.getContext) {
              const ctx = videoElement.getContext('2d');
              const videoBlob = new Blob([data.frame], {type: 'image/jpeg'});
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
          this.videos.push({user_id: data.user_id});
        }
      });

      this.socket.on('message', (msg) => {
        this.messages.push(msg);
      });
    },
    toggleScreenShare() {
      axios.post('http://127.0.0.1:5000/api/update-screen-status');
      this.isSharingScreen = !this.isSharingScreen;
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
  height: 100vh;
  display: flex;
}

.video-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.video-grid {
  display: flex;
  justify-content: space-around;
  margin-bottom: 10px;
}

.video-container {
  width: 25%; /* 四个视频元素平分宽度 */
  height: 160px; /* 增加高度 */
}

.screen-share {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.controls {
  display: flex;
  justify-content: space-around;
  padding: 10px;
  border-top: 1px solid #ccc;
  position: fixed;
  bottom: 0;
  width: calc(100% - 250px); /* 减去聊天栏的宽度 */
  background-color: white;
  margin-right: 250px; /* 确保按钮不会被聊天栏覆盖 */
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

.timestamp {
  font-size: 0.7em; /* 调整字体大小 */
  color: lightgray; /* 调整字体颜色 */
  margin-left: 10px;
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

.cancel-button {
  background-color: red;
  border-color: red;
  color: white;
}

.cancel-button:hover {
  background-color: darkred;
  border-color: darkred;
}

.hover-button {
  /*固定尺寸*/
  width: 120px;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

</style>