<template>
  <div class="login-page">
    <div class="login-container">
      <a-card bordered={false} class="login-card">
        <div class="login-header">
          <h1>登录到你的账户</h1>
        </div>
        <a-form
            layout="vertical"
            @submit.prevent="handleLogin"
        >
          <!-- 输入账号 -->
          <a-form-item label="邮箱">
            <a-input
                v-model:value="username"
                size="large"
                placeholder="请输入邮箱"
                class="custom-input"
            />
          </a-form-item>
          <!-- 输入密码 -->
          <a-form-item label="密码">
            <a-input-password
                v-model:value="password"
                size="large"
                placeholder="请输入密码"
                class="custom-input"
            />
          </a-form-item>
          <!-- 登录按钮 -->
          <a-form-item>
            <a-button
                type="primary"
                size="large"
                block
                @click="handleLogin"
                class="custom-button"
            >
              登录
            </a-button>
          </a-form-item>
        </a-form>
        <!-- 注册链接 -->
        <div class="register-link">
          <span>还没有账号？</span>
          <a @click="handleRegister">点击注册</a>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      username: '',
      password: '',
    };
  },
  methods: {
    async handleLogin() {
      try {
        const response = await axios.post('http://127.0.0.1:5000/api/login' ,{
          username: this.username,
          password: this.password,
        });
        console.log('登录成功:', response.data);
        this.$router.push('/dashboard');
      } catch (error) {
        console.error('登录失败:', error);
        alert('登录失败，请检查您的用户名和密码。');
      }
    },
    handleRegister() {
      this.$router.push('/register');
    },
  },
};
</script>

<style scoped>
/* 背景样式 */
.login-page {
  background: url('https://source.unsplash.com/1920x1080/?network,technology') no-repeat center center/cover;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 卡片容器样式 */
.login-container {
  width: 360px;
}

/* 卡片样式 */
.login-card {
  backdrop-filter: blur(8px);
  background: rgba(255, 255, 255, 0.9);
  padding: 24px 32px;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 标题样式 */
.login-header h1 {
  margin: 0 0 24px 0;
  text-align: center;
  font-size: 22px;
  color: #333;
}

/* 输入框样式 */
.custom-input {
  border-radius: 8px;
  height: 45px;
}

/* 按钮样式 */
.custom-button {
  border-radius: 8px;
  background-color: #1890ff;
  color: white;
  font-weight: bold;
  height: 45px;
  font-size: 16px;
  border: none;
}

.custom-button:hover {
  background-color: #1677d9;
  color: white;
}

/* 注册链接样式 */
.register-link {
  margin-top: 16px;
  text-align: center;
  font-size: 14px;
  color: #666;
}

.register-link a {
  color: #1890ff;
  font-weight: bold;
  text-decoration: none;
  cursor: pointer;
}

.register-link a:hover {
  text-decoration: underline;
}

.custom-input {
  border-radius: 8px;
  height: 50px; /* 调整输入框高度 */
  padding: 0 16px; /* 调整输入框内的左右内边距 */
}

/* 登录按钮样式调整 */
.custom-button {
  height: 50px; /* 与输入框高度保持一致 */
}

/* 布局调整：使表单项目垂直居中 */
.a-form-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 调整表单项之间的间距 */
.a-form-item:not(:last-child) {
  margin-bottom: 16px; /* 在每个表单项之间增加间距 */
}

/* 如果需要调整整个卡片内容的水平间距 */
.login-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 32px; /* 增加卡片内部的间距 */
}
</style>
