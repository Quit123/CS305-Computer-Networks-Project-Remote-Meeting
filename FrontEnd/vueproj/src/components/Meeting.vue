<template>
  <div class="meeting">
    <div class="header">{{ meetingTitle }}</div>
    <div class="content">
      <div class="video-section">
        <a-button class="pagination-button left" icon="left" @click="prevPage" :disabled="currentPage === 1">
          <img src="@/assets/left.ico" alt="left" />
        </a-button>
        <div class="video-grid">
          <a-row :gutter="16">
            <a-col v-for="(video, index) in paginatedVideos" :key="index" :span="8">
              <div class="video-container">
                <video :src="video.stream" autoplay></video>
                <div class="username">{{ video.username }}</div>
              </div>
            </a-col>
          </a-row>
        </div>
        <a-button class="pagination-button right" icon="right" @click="nextPage" :disabled="currentPage === totalPages">
          <img src="@/assets/right.ico" alt="right" />
        </a-button>
      </div>
      <div class="chat-section">
        <a-button class="pagination-button right" icon="right" @click="nextPage" :disabled="currentPage === totalPages">
          <img src="@/assets/right.ico" alt="right" />
        </a-button>
        <ChatBox />
      </div>
    </div>
    <div class="controls">
      <a-switch
          checked-children="摄像头开"
          un-checked-children="摄像头关"
          @change="toggleCamera"
          :checked="cameraOn"
      />
      <a-switch
          checked-children="麦克风开"
          un-checked-children="麦克风关"
          @change="toggleMicrophone"
          :checked="microphoneOn"
      />
      <a-button type="primary" @click="shareScreen">共享屏幕</a-button>
      <a-button type="danger" @click="leaveMeeting">退出会议</a-button>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import ChatBox from "@/components/ChatBox.vue";

export default {
  components: {
    ChatBox,
  },
  data() {
    return {
      meetingTitle: '会议标题',
      videos: [],
      currentPage: 1,
      cameraOn: true,
      microphoneOn: true,
    };
  },
  computed: {
    paginatedVideos() {
      const start = (this.currentPage - 1) * 9;
      return this.videos.slice(start, start + 9);
    },
    totalPages() {
      return Math.ceil(this.videos.length / 9);
    },
  },
  methods: {
    toggleCamera() {
      this.cameraOn = !this.cameraOn;
    },
    toggleMicrophone() {
      this.microphoneOn = !this.microphoneOn;
    },
    shareScreen() {
      this.cameraOn = false;
    },
    leaveMeeting() {
      // Handle leaving the meeting
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
    async fetchVideos() {
      try {
        const response = await axios.get('http://127.0.0.1:5000/api/videos');
        this.videos = response.data;
      } catch (error) {
        console.error('Failed to fetch videos:', error);
      }
    },
  },
  mounted() {
    this.fetchVideos();
  },
};
</script>

<style scoped>
.meeting {
  background-color: #000;
  padding: 8px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.header {
  text-align: center;
  color: #fff;
  margin-bottom: 8px;
  font-size: 1.5em;
}

.content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex: 1;
}

.video-section {
  flex: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.video-grid {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.video-container {
  position: relative;
  width: 100%;
  height: 200px;
  background-color: #333;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 2px solid #ccc;
}

.video-container video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.username {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  background-color: rgba(0, 0, 0, 0.5);
  padding: 2px 8px;
  border-radius: 4px;
}

.pagination-button {
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pagination-button.left {
  position: absolute;
  top: 350px;
  left: 16px;
}

.pagination-button.right {
  position: absolute;
  top: 350px;
  right: 400px;
}

.chat-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 300px;
}

.controls {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 8px;
  background-color: #111;
}

.controls .ant-switch {
  margin: 0 8px;
}

.controls .ant-btn-primary {
  background-color: #1890ff;
  border-color: #1890ff;
}

.controls .ant-btn-danger {
  background-color: #ff4d4f;
  border-color: #ff4d4f;
}
</style>