import Vue from 'vue'
import VueRouter from 'vue-router'

// 懒加载路由组件
const TaskList = () => import('../views/Tasks/TaskList.vue')
const TaskNew = () => import('../views/Tasks/TaskNew.vue')
const TaskDetail = () => import('../views/Tasks/TaskDetail.vue')
const AgentList = () => import('../views/Agents/AgentList.vue')
const TemplateList = () => import('../views/Templates/TemplateList.vue')

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    redirect: '/tasks'
  },
  {
    path: '/tasks',
    name: 'TaskList',
    component: TaskList
  },
  {
    path: '/tasks/new',
    name: 'TaskNew',
    component: TaskNew
  },
  {
    path: '/tasks/:id',
    name: 'TaskDetail',
    component: TaskDetail,
    props: true
  },
  {
    path: '/agents',
    name: 'AgentList',
    component: AgentList
  },
  {
    path: '/templates',
    name: 'TemplateList',
    component: TemplateList
  },
  {
    path: '*',
    redirect: '/tasks'
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
  linkActiveClass: 'active'
})

export default router
