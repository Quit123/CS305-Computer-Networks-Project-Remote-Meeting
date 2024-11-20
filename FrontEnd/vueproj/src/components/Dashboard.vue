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

        <!-- 邀请成员 -->
        <a-form-item
            label="邀请成员："
            :label-col="{ span: 5 }"
            :wrapper-col="{ span: 19 }"
        >
          <a-select
              mode="tags"
              placeholder="输入邮箱并回车添加"
              v-model:value="meeting.members"
              :token-separators="[',']"
          />
        </a-form-item>

       <!-- 启用密码 -->
       <a-form-item
           label="启用密码："
           :label-col="{ span: 5 }"
           :wrapper-col="{ span: 19 }"
       >
         <a-switch
             v-model:checked="meeting.enablePassword"
             @change="handlePasswordSwitchChange"
         />
       </a-form-item>

       <!-- 密码设置 -->
       <a-form-item
           v-if="meeting.enablePassword"
           label="设置密码："
           :label-col="{ span: 5 }"
           :wrapper-col="{ span: 19 }"
       >
         <a-input
             type="password"
             maxlength="6"
             placeholder="6位数字密码"
             v-model:value="meeting.password"
         />
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
          <a-button type="primary" block @click="checkMeetingPassword">
            加入会议
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 输入密码模态框 -->
    <a-modal
        v-model:visible="isPasswordModalVisible"
        title="输入会议密码"
        :footer="null"
        centered
        @cancel="resetPasswordForm"
        ok-text="确认"
        cancel-text="取消"
    >
      <a-form>
        <!-- 密码 -->
        <a-form-item
            label="密码："
            :label-col="{ span: 5 }"
            :wrapper-col="{ span: 19 }"
            :rules="[{ required: true, message: '请输入会议密码!' }]"
        >
          <a-input
              type="password"
              maxlength="6"
              placeholder="6位数字密码"
              v-model:value="meetingPassword"
          />
        </a-form-item>

        <!-- 提交按钮 -->
        <a-form-item :wrapper-col="{ span: 19, offset: 5 }">
          <a-button type="primary" block @click="joinMeetingWithPassword">
            确认
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 统计信息与日历 -->
    <div class="dashboard-extra">
      <a-card title="统计信息" class="hover-card">
        <p>本月创建会议: 10</p>
        <p>本月加入会议: 15</p>
      </a-card>
      <a-calendar class="dashboard-calendar" />
    </div>
  </div>
</template>

<script>
import {message} from "ant-design-vue";
import 'ant-design-vue/es/message/style/css'

export default {
  data() {
    return {
      isCreateMeetingVisible: false,
      isJoinMeetingVisible: false,
      isPasswordModalVisible: false,
      joinMeetingId: "",
      meetingPassword: "",
      meeting: {
        title: "",
        members: [],
        enablePassword: false,
        password: "",
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
    createMeeting() {
      if (!this.meeting.title) {
        console.log(this.meeting.title)
        return message.error("请填写会议主题！");
      }
      if (this.meeting.enablePassword && this.meeting.password.length !== 6) {
        console.log(this.meeting.password)
        return message.error("密码必须为6位数字！");
      }

      console.log("创建会议数据：", this.meeting);
      message.success("会议创建成功！");
      this.resetForm();
      this.joinMeeting();
    },
    handlePasswordSwitchChange(value) {
      if (!value) {
        this.meeting.password = ""; // 禁用密码时清空密码
      }
    },
    resetForm() {
      this.meeting = {
        title: "",
        members: [],
        enablePassword: false,
        password: "",
      };
      this.isCreateMeetingVisible = false;
    },
    showJoinMeeting() {
      this.isJoinMeetingVisible = true;
    },
    checkMeetingPassword() {
      if (!this.joinMeetingId) {
        return message.error("请填写会议号！");
      }

      // 模拟后台检测会议是否有密码
      const hasPassword = true; // 假设返回结果

      if (hasPassword) {
        this.isPasswordModalVisible = true;
      } else {
        this.joinMeeting();
        this.resetJoinForm();
      }
    },
    joinMeetingWithPassword() {
      if (this.meetingPassword.length !== 6) {
        return message.error("密码必须为6位数字！");
      }

      // 模拟加入会议
      message.success("加入会议成功！");
      this.resetPasswordForm();
      this.resetJoinForm();
    },
    joinMeeting() {
      // 模拟加入会议
      message.success("加入会议成功！");
      this.resetJoinForm();
    },
    resetJoinForm() {
      this.joinMeetingId = "";
      this.isJoinMeetingVisible = false;
    },
    resetPasswordForm() {
      this.meetingPassword = "";
      this.isPasswordModalVisible = false;
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
