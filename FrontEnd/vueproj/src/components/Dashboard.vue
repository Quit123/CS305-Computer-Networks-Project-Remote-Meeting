<template>
  <div class="dashboard">
    <!-- 用户信息 -->
    <div class="user-info">
      <img class="avatar" :src="user.avatar" alt="用户头像" />
      <h2>欢迎回来, {{ user.name }}!</h2>
      <p>今天是 {{ currentDate }}</p>
    </div>

    <!-- 动态网格功能区 -->
    <a-row gutter="16" class="dashboard-grid">
      <a-col span="8">
        <a-card title="创建会议" class="hover-card" @mouseenter="hoverEnter" @mouseleave="hoverLeave">
          <p>快速创建一个新会议。</p>
          <a-button type="primary" block @click="showCreateMeeting" class="hover-button">创建会议</a-button>
        </a-card>
      </a-col>
      <a-col span="8">
        <a-card title="加入会议" class="hover-card">
          <p>通过会议号加入会议。</p>
          <a-button type="primary" block @click="showJoinMeeting" class="hover-button">加入会议</a-button>
        </a-card>
      </a-col>
      <a-col span="8">
        <a-card title="最近会议" class="hover-card">
          <p>查看最近参加的会议。</p>
          <a-button type="default" block @click="viewRecent" class="hover-button">查看会议</a-button>
        </a-card>
      </a-col>
    </a-row>

    <!-- 创建会议模态框 -->
    <a-modal
        v-model:visible="isCreateMeetingVisible"
        title="创建会议"
        :footer="null"
        centered
        @cancel="resetForm"
        ok-text="创建"
        cancel-text="取消"
    >
     <a-form>
        <!-- 主题 -->
        <a-form-item
            label="主题："
            :label-col="{ span: 5 }"
            :wrapper-col="{ span: 19 }"
            :rules="[{ required: true, message: '请输入会议主题!' }]"
        >
          <a-input v-model:value="meeting.title" placeholder="请输入会议主题" />
        </a-form-item>

<!--        &lt;!&ndash; 提交按钮 &ndash;&gt;-->
        <a-form-item :wrapper-col="{ span: 19, offset: 5 }">
          <a-button type="primary" block @click="createMeeting">
            创建会议
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 加入会议模态框 -->
    <a-modal
        v-model:visible="isJoinMeetingVisible"
        title="加入会议"
        :footer="null"
        centered
        @cancel="resetJoinForm"
        ok-text="加入"
        cancel-text="取消"
    >
      <a-form>
        <!-- 会议号 -->
        <a-form-item
            label="会议号："
            :label-col="{ span: 5 }"
            :wrapper-col="{ span: 19 }"
            :rules="[{ required: true, message: '请输入会议号!' }]"
        >
          <a-input v-model:value="joinMeetingId" placeholder="请输入会议号" />
        </a-form-item>

        <!-- 提交按钮 -->
        <a-form-item :wrapper-col="{ span: 19, offset: 5 }">
          <a-button type="primary" block @click="joinMeeting">
            加入会议
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>

  </div>
</template>

<script>
import {message} from "ant-design-vue";
import 'ant-design-vue/es/message/style/css'
import axios from "axios";

export default {
  data() {
    return {
      isCreateMeetingVisible: false,
      isJoinMeetingVisible: false,
      joinMeetingId: "",
      meeting: {
        title: "",
      },
      user: {
        name: '张三',
        avatar: 'https://via.placeholder.com/100',
      },
      currentDate: new Date().toLocaleDateString(),
    };
  },
  methods: {
    viewRecent() {
      console.log('查看最近会议');
    },
    hoverEnter(event) {
      const card = event.currentTarget;
      card.style.transform = "scale(1.05)";
      card.style.boxShadow = "0 10px 20px rgba(0,0,0,0.2)";
    },
    hoverLeave(event) {
      const card = event.currentTarget;
      card.style.transform = "scale(1)";
      card.style.boxShadow = "none";
    },
    showCreateMeeting() {
      console.log("showCreateMeeting")
      this.isCreateMeetingVisible = true;
    },
    async createMeeting() {
      if (!this.meeting.title) {
        console.log(this.meeting.title)
        return message.error("请填写会议主题！");
      }

      try {
        const response = await axios.post('http://127.0.0.1:5000/api/create', {
          title: this.meeting.title,
        });
        if (response.data.status === 'success') {
          message.success("会议创建成功！");
          this.resetForm();
          this.joinMeeting();
        } else {
          message.error("会议创建失败：" + response.data.message);
        }
      } catch (error) {
        message.error("会议创建失败：" + error.message);
      }
    },
    resetForm() {
      this.meeting = {
        title: "",
      };
      this.isCreateMeetingVisible = false;
    },
    showJoinMeeting() {
      this.isJoinMeetingVisible = true;
    },
    joinMeeting() {
      // 模拟加入会议
      message.success("加入会议成功！");
      this.resetJoinForm();
      this.$router.push('/meeting' );
    },
    resetJoinForm() {
      this.joinMeetingId = "";
      this.isJoinMeetingVisible = false;
    },
  },
};
</script>

<style scoped>
/* 用户信息样式 */
.user-info {
  text-align: center;
  margin-bottom: 24px;
}
.user-info .avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  margin-bottom: 16px;
}

/* 动态卡片样式 */
.hover-card {
  transition: all 0.3s ease;
  border-radius: 8px;
  cursor: pointer;
}
.hover-card:hover {
  transform: scale(1.05);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

/* 动态按钮样式 */
.hover-button {
  transition: background-color 0.3s ease, transform 0.2s ease;
  border-radius: 8px;
  font-size: 16px;
}

.dashboard-grid {
  margin-bottom: 24px;
}

/* 额外样式 */
.dashboard-extra {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.dashboard-calendar {
  flex: 1;
}
</style>
