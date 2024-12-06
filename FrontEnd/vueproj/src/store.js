// store.js
import { createStore } from 'vuex';

export default createStore({
    state: {
        username: '',
    },
    mutations: {
        setUsername(state, username) {
            console.log('setting username to ' + username);
            state.username = username;
        },
    },
    actions: {
        updateUsername({ commit }, username) {
            console.log('updating username to ' + username);
            commit('setUsername', username);
        },
    },
    getters: {
        getUsername(){
            console.log('getting username' + this.username);
            return this.username;
        }
    },
});