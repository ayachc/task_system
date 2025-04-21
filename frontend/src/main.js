import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// 引入BootstrapVue
import { BootstrapVue, IconsPlugin } from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

// 使用插件
Vue.use(BootstrapVue)
Vue.use(IconsPlugin)

// 全局错误处理
Vue.config.errorHandler = function (err, vm, info) {
  console.error('Vue错误:', err)
  console.error('错误信息:', info)
}

Vue.config.productionTip = false

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
