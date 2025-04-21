import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加认证令牌等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 检查响应是否成功
    const data = response.data
    if (data.success === false) {
      // 服务端返回了错误
      return Promise.reject(new Error(data.message || '操作失败'))
    }
    // 返回实际数据
    return data.data || data
  },
  error => {
    // 处理错误响应
    let errorMessage = '请求失败，请稍后再试'
    
    if (error.response) {
      // 服务器返回了错误状态码
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          errorMessage = data.message || '请求参数错误'
          break
        case 404:
          errorMessage = '请求的资源不存在'
          break
        case 500:
          errorMessage = '服务器内部错误'
          break
        default:
          errorMessage = `请求错误 (${status})`
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      errorMessage = '无法连接到服务器，请检查网络'
    } else if (error.message) {
      // 来自拦截器的错误消息
      errorMessage = error.message
    }
    
    console.error('API错误:', errorMessage)
    return Promise.reject(new Error(errorMessage))
  }
)

// 任务相关API
export const taskApi = {
  // 获取任务列表
  getTasks: (params = {}) => api.get('/task/', { params }),
  
  // 获取单个任务
  getTask: (taskId) => api.get(`/task/${taskId}`),
  
  // 创建任务
  createTask: (taskData) => api.post('/task/', taskData),
  
  // 更新任务
  updateTask: (taskId, taskData) => api.put(`/task/${taskId}`, taskData),
  
  // 取消任务
  cancelTask: (taskId) => api.post(`/task/${taskId}/cancel`),
  
  // 获取任务日志
  getTaskLog: (taskId, params = {}) => api.get(`/task/${taskId}/log`, { params }),
  
  // 添加任务日志 (适用于手动添加日志)
  appendTaskLog: (taskId, content) => api.post(`/task/${taskId}/log`, { content })
}

// Agent相关API
export const agentApi = {
  // 获取所有Agent
  getAgents: (params = {}) => api.get('/agent/', { params }),
  
  // 获取单个Agent
  getAgent: (agentId) => api.get(`/agent/${agentId}`),
  
  // 创建主Agent
  createMainAgent: (agentData) => api.post('/agent/main', agentData),
  
  // 创建子Agent
  createSubAgent: (agentData) => api.post('/agent/sub', agentData),
  
  // 取消Agent
  cancelAgent: (agentId) => api.post(`/agent/${agentId}/cancel`),
  
  // 发送心跳
  sendHeartbeat: (agentId, data) => api.post(`/agent/${agentId}/heartbeat`, data),
  
  // 检查所有Agent状态
  checkAgentsStatus: () => api.post('/agent/check-status')
}

// 模板相关API
export const templateApi = {
  // 获取所有模板
  getTemplates: (params = {}) => api.get('/template/', { params }),
  
  // 获取单个模板
  getTemplate: (templateId) => api.get(`/template/${templateId}`),
  
  // 创建模板
  createTemplate: (templateData) => api.post('/template/', templateData),
  
  // 更新模板
  updateTemplate: (templateId, templateData) => api.put(`/template/${templateId}`, templateData),
  
  // 删除模板
  deleteTemplate: (templateId) => api.delete(`/template/${templateId}`)
}

export default api
