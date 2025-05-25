import { taskApi } from '@/services/api'

// 初始状态
const state = {
  tasks: [],
  task: null,
  pagination: {
    page: 1,
    perPage: 10,
    total: 0,
    pages: 0
  },
  filters: {
    status: '',
    name: '',
    template_type: ''
  },
  taskLog: ''
}

// 获取状态
const getters = {
  taskList: state => state.tasks,
  taskDetail: state => state.task,
  pagination: state => state.pagination,
  filters: state => state.filters,
  taskLog: state => state.taskLog
}

// 修改状态
const mutations = {
  SET_TASKS(state, { tasks, total, page, per_page, pages }) {
    state.tasks = tasks
    state.pagination.total = total
    state.pagination.page = page
    state.pagination.perPage = per_page
    state.pagination.pages = pages
  },
  SET_TASK(state, task) {
    state.task = task
  },
  SET_PAGE(state, page) {
    state.pagination.page = page
  },
  SET_FILTERS(state, filters) {
    state.filters = { ...state.filters, ...filters }
  },
  UPDATE_TASK_STATUS(state, { taskId, newStatus }) {
    const taskIndex = state.tasks.findIndex(t => t.id === taskId)
    if (taskIndex !== -1) {
      state.tasks[taskIndex].status = newStatus
    }
    if (state.task && state.task.id === taskId) {
      state.task.status = newStatus
    }
  },
  SET_TASK_LOG(state, log) {
    state.taskLog = log
  }
}

// 异步操作
const actions = {
  // 获取任务列表
  async fetchTasks({ commit, state }) {
    try {
      commit('SET_LOADING', true, { root: true })
      
      const { page, perPage } = state.pagination
      const filters = state.filters
      
      // 构建查询参数
      const params = {
        page,
        per_page: perPage
      }
      
      // 添加过滤条件
      if (filters.status) params.status = filters.status
      if (filters.name) params.name = filters.name
      if (filters.template_type) params.template_type = filters.template_type
      
      const response = await taskApi.getTasks(params)
      
      commit('SET_TASKS', {
        tasks: response.tasks,
        total: response.total,
        page: response.page,
        per_page: response.per_page,
        pages: response.pages
      })
      
      return response
    } catch (error) {
      console.error('获取任务列表失败:', error)
      commit('SET_ERROR', error.message || '获取任务列表失败，请稍后重试', { root: true })
      throw error
    } finally {
      commit('SET_LOADING', false, { root: true })
    }
  },
  
  // 获取单个任务详情
  async fetchTask({ commit }, taskId) {
    try {
      commit('SET_LOADING', true, { root: true })
      
      const response = await taskApi.getTask(taskId)
      commit('SET_TASK', response)
      
      return response
    } catch (error) {
      console.error(`获取任务${taskId}详情失败:`, error)
      commit('SET_ERROR', error.message || '获取任务详情失败，请稍后重试', { root: true })
      throw error
    } finally {
      commit('SET_LOADING', false, { root: true })
    }
  },
  
  // 创建新任务
  async createTask({ commit }, taskData) {
    try {
      commit('SET_LOADING', true, { root: true })
      
      const response = await taskApi.createTask(taskData)
      return response
    } catch (error) {
      console.error('创建任务失败:', error)
      commit('SET_ERROR', error.message || '创建任务失败，请检查输入并重试', { root: true })
      throw error
    } finally {
      commit('SET_LOADING', false, { root: true })
    }
  },
  
  // 取消任务
  async cancelTask({ commit }, taskId) {
    try {
      commit('SET_LOADING', true, { root: true })
      
      await taskApi.cancelTask(taskId)
      commit('UPDATE_TASK_STATUS', { taskId, newStatus: 'canceled' })
      
      return true
    } catch (error) {
      console.error(`取消任务${taskId}失败:`, error)
      commit('SET_ERROR', error.message || '取消任务失败，请稍后重试', { root: true })
      throw error
    } finally {
      commit('SET_LOADING', false, { root: true })
    }
  },
  
  // 获取任务日志
  async fetchTaskLog({ commit }, { taskId, startLine, maxLines }) {
    try {
      const params = {}
      if (startLine !== undefined) params.start_line = startLine
      if (maxLines !== undefined) params.max_lines = maxLines
      
      const response = await taskApi.getTaskLog(taskId, params)
      
      commit('SET_TASK_LOG', response.content || '')
      return response
    } catch (error) {
      console.error(`获取任务${taskId}日志失败:`, error)
      // 不设置全局错误，避免影响页面其他部分
      throw error
    }
  },
  
  // 更新分页
  setPage({ commit, dispatch }, page) {
    commit('SET_PAGE', page)
    return dispatch('fetchTasks')
  },
  
  // 设置过滤条件
  setFilters({ commit, dispatch }, filters) {
    commit('SET_FILTERS', filters)
    commit('SET_PAGE', 1) // 重置到第一页
    return dispatch('fetchTasks')
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
