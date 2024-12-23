<template>
  <div class="dashboard">
    <div class="user-info">
      <h2>欢迎使用妮可大会议平台嗷!</h2>
      <p>今天是 {{ currentDate }}</p>
    </div>

    <!-- 动态网格功能区 -->
    <a-row gutter="16" class="dashboard-grid">
      <a-col span="8">
        <a-card title="创建会议" class="hover-card" @mouseenter="hoverEnter" @mouseleave="hoverLeave">
          <p>选择创建会议类型。</p>
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
        <a-card title="查看会议列表" class="hover-card">
          <p>查看当前可以加入的会议。</p>
          <a-button type="primary" block @click="showMeetingList" class="hover-button">查看会议列表</a-button>
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

        <!-- 会议类型选择 -->
        <a-form-item
            label="会议类型："
            :label-col="{ span: 5 }"
            :wrapper-col="{ span: 19 }"
        >
          <a-radio-group v-model:value="meeting.type">
            <a-radio value="simple">简单会议</a-radio>
            <a-radio value="multi">多人会议</a-radio>
          </a-radio-group>
        </a-form-item>

        <!-- 提交按钮 -->
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
    <a-modal
      v-model:visible="isMeetingListVisible"
      title="会议列表"
      :footer="null"
      centered
      @cancel="isMeetingListVisible = false"
    >
      <a-table :data-source="meetingList" :columns="columns" row-key="id" />
    </a-modal>

  </div>
</template>

<script>
import {message} from "ant-design-vue";
import 'ant-design-vue/es/message/style/css'
import axios from "axios";
import {mapGetters} from "vuex";

export default {
  computed: {
    ...mapGetters(['getUsername']),
  },
  data() {
    return {
      isCreateMeetingVisible: false,
      isJoinMeetingVisible: false,
      isJoinSimpleMeetingVisible: false,
      isMeetingListVisible: false,
      joinMeetingId: "",
      simpleMeetings: [],
      meeting: {
        title: "",
        type: "",
      },
      meetingList: [],
      user_id: this.getUsername,
      currentDate: new Date().toLocaleDateString(),
      columns: [
        {
          title: '会议名称',
          dataIndex: 'title',
          key: 'title',
        },
        {
          title: '发起者',
          dataIndex: 'creator',
          key: 'creator',
        },
        {
          title: '会议号',
          dataIndex: 'id',
          key: 'id',
        },
      ],
    };
},
  methods: {
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
      this.isCreateMeetingVisible = true;
    },
    async createMeeting() {
      if (!this.meeting.title) {
        return message.error("请填写会议主题！");
      }

      if (this.meeting.type === 'simple') {
        try {
          const response = await axios.post('http://127.0.0.1:5000/api/create_P2P', {
            title: this.meeting.title,
          });
          if (response.data.status === 'success') {
            message.success("简单会议创建成功！");
            this.resetForm();
            this.joinMeetingId = response.data.message;
            await this.joinMeeting();
          } else {
            message.error("简单会议创建失败：" + response.data.message);
          }
        } catch (error) {
          message.error("简单会议创建失败：" + error.message);
        }
      }

      if (this.meeting.type === 'multi') {
        try {
          const response = await axios.post('http://127.0.0.1:5000/api/create', {
            title: this.meeting.title,
          });
          if (response.data.status === 'success') {
            message.success("多人会议创建成功！");
            this.resetForm();
            this.joinMeetingId = response.data.message;
            await this.joinMeeting();
          } else {
            message.error("多人会议创建失败：" + response.data.message);
          }
        } catch (error) {
          message.error("多人会议创建失败：" + error.message);
        }
      }
      else {
        message.error("请选择会议类型！");
      }
    },
    resetForm() {
      this.meeting = {
        title: "",
        type: "",
      };
      this.isCreateMeetingVisible = false;
    },
    showJoinMeeting() {
      this.isJoinMeetingVisible = true;
    },

    async showMeetingList() {
      try {
        const response = await axios.get('http://127.0.0.1:5000/api/check-list');
        if (response.data.status === 'success') {
          this.meetingList = response.data.meetings;
          this.isMeetingListVisible = true;
        } else {
          message.error("获取会议列表失败：" + response.data.message);
        }
      } catch (error) {
        message.error("获取会议列表失败：" + error.message);
      }
    },

    async joinMeeting() {
      if (!this.joinMeetingId) {
        return message.error("请输入会议号！");
      }
      const response = await axios.post('http://127.0.0.1:5000/api/join', {con_id: this.joinMeetingId});
      if (response.data.status === 'success') {
        message.success("加入会议成功");
        this.$router.push('/meeting');
      } else {
        message.error("加入会议失败：" + response.data.message);
      }
    },
    resetJoinForm() {
      this.joinMeetingId = "";
      this.isJoinMeetingVisible = false;
      this.isJoinSimpleMeetingVisible = false;
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
</style>