import { createApp } from 'vue';
import App from './App.vue';
import Antd from 'ant-design-vue';
import router from './router';
import axios from 'axios';

axios.defaults.baseURL = 'http://127.0.0.1:5000';
const app = createApp(App);
app.use(router);
app.use(Antd);
app.mount('#app');