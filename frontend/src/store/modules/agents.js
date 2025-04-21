import { agentApi } from '@/services/api'

// 初始状态
const state = {
  agents: [],
  agentTypes: ['main', 'sub'],
  loading: false,
  error: null
}

// 获取状态
const getters = {
  allAgents: state => state.agents,
  mainAgents: state => state.agents.filter(agent => agent.agent_type === 'main'),
  subAgents: state => state.agents.filter(agent => agent.agent_type === 'sub'),
  
  // 按主Agent ID获取子Agent
  subAgentsByMainId: state => mainAgentId => {
    return state.agents.filter(
      agent => agent.agent_type === 'sub' && agent.main_agent_id === mainAgentId
    )
  },
  
  // 获取Agent的资源使用情况
  agentResourceUsage: state => agentId => {
    const agent = state.agents.find(a => a.id === agentId)
    if (!agent) return null
    
    return {
      cpuUsage: agent.cpu_usage || 0,
      memoryUsage: agent.memory_usage || 0,
      gpuUsage: agent.gpu_usage || []
    }
  },
  
  // 按ID获取Agent
  getAgentById: state => agentId => {
    return state.agents.find(agent => agent.id === agentId)
  }
}

// 修改状态
const mutations = {
  SET_AGENTS(state, agents) {
    state.agents = agents
  },
  
  SET_LOADING(state, isLoading) {
    state.loading = isLoading
  },
  
  SET_ERROR(state, error) {
    state.error = error
  },
  
  UPDATE_AGENT_STATUS(state, { agentId, status, resourceData }) {
    const agentIndex = state.agents.findIndex(a => a.id === agentId)
    if (agentIndex !== -1) {
      const agent = { ...state.agents[agentIndex] }
      
      if (status) {
        agent.status = status
      }
      
      if (resourceData) {
        agent.cpu_usage = resourceData.cpu_usage || agent.cpu_usage
        agent.memory_usage = resourceData.memory_usage || agent.memory_usage
        agent.gpu_usage = resourceData.gpu_usage || agent.gpu_usage
      }
      
      state.agents.splice(agentIndex, 1, agent)
    }
  },
  
  ADD_AGENT(state, agent) {
    state.agents.push(agent)
  },
  
  REMOVE_AGENT(state, agentId) {
    const agentIndex = state.agents.findIndex(a => a.id === agentId)
    if (agentIndex !== -1) {
      state.agents.splice(agentIndex, 1)
    }
  }
}

// 异步操作
const actions = {
  // 获取所有Agent
  async fetchAgents({ commit }, params = {}) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const agents = await agentApi.getAgents(params)
      commit('SET_AGENTS', agents)
      return agents
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error('获取Agent列表失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 获取单个Agent详情
  async fetchAgent({ commit }, agentId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const agent = await agentApi.getAgent(agentId)
      // 更新缓存中的Agent
      commit('UPDATE_AGENT_STATUS', { 
        agentId: agent.id, 
        status: agent.status,
        resourceData: {
          cpu_usage: agent.cpu_usage,
          memory_usage: agent.memory_usage,
          gpu_usage: agent.gpu_usage
        }
      })
      return agent
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error(`获取Agent详情失败 (ID=${agentId}):`, error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 创建主Agent
  async createMainAgent({ commit }, agentData) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const agent = await agentApi.createMainAgent(agentData)
      commit('ADD_AGENT', agent)
      return agent
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error('创建主Agent失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 取消Agent
  async cancelAgent({ commit }, agentId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      await agentApi.cancelAgent(agentId)
      commit('UPDATE_AGENT_STATUS', { agentId, status: 'canceled' })
      return true
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error(`取消Agent失败 (ID=${agentId}):`, error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 轮询更新Agent状态
  async pollAgentStatus({ dispatch }) {
    try {
      await dispatch('fetchAgents')
      
      // 5秒后再次轮询
      setTimeout(() => {
        dispatch('pollAgentStatus')
      }, 5000)
    } catch (error) {
      console.error('Agent状态轮询失败:', error)
      
      // 发生错误时，10秒后再次尝试
      setTimeout(() => {
        dispatch('pollAgentStatus')
      }, 10000)
    }
  },
  
  // 检查所有Agent状态
  async checkAgentsStatus({ dispatch }) {
    try {
      await agentApi.checkAgentsStatus()
      // 更新Agent列表
      dispatch('fetchAgents')
    } catch (error) {
      console.error('检查Agent状态失败:', error)
      throw error
    }
  },
  
  // 移除Agent（适用于子Agent）
  async removeAgent({ commit }, agentId) {
    try {
      await agentApi.cancelAgent(agentId)
      commit('REMOVE_AGENT', agentId)
    } catch (error) {
      console.error(`移除Agent失败 (ID=${agentId}):`, error)
      throw error
    }
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
