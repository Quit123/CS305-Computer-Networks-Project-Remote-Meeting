import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Login.vue';
import Dashboard from '../components/Dashboard.vue';
import Meeting from '../components/Meeting.vue';
import Register from '../components/Register.vue';

const routes = [
    { path: '/', component: Login },
    { path: '/dashboard', component: Dashboard },
    { path: '/meeting', component: Meeting },
    { path: '/register' ,component: Register},
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;