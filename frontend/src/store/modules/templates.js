import axios from 'axios'
import { templateApi } from '@/services/api'

// 初始状态
const state = {
  templates: [],
  template: null,
  loading: false,
  error: null
}

// 获取状态
const getters = {
  allTemplates: state => state.templates,
  getTemplateById: state => id => state.templates.find(t => t.id === id),
  templateTypes: state => [...new Set(state.templates.map(t => t.template_type))]
}

// 修改状态
const mutations = {
  SET_TEMPLATES(state, templates) {
    state.templates = templates
  },
  SET_TEMPLATE(state, template) {
    state.template = template
  },
  ADD_TEMPLATE(state, template) {
    state.templates.push(template)
  },
  UPDATE_TEMPLATE(state, updatedTemplate) {
    const index = state.templates.findIndex(t => t.id === updatedTemplate.id)
    if (index !== -1) {
      state.templates.splice(index, 1, updatedTemplate)
    }
  },
  DELETE_TEMPLATE(state, templateId) {
    state.templates = state.templates.filter(t => t.id !== templateId)
  },
  SET_LOADING(state, isLoading) {
    state.loading = isLoading
  },
  SET_ERROR(state, error) {
    state.error = error
  }
}

// 异步操作
const actions = {
  // 获取模板列表
  async fetchTemplates({ commit }, params = {}) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const templates = await templateApi.getTemplates(params)
      commit('SET_TEMPLATES', templates)
      return templates
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error('获取模板列表失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 获取单个模板
  async fetchTemplate({ commit }, templateId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const template = await templateApi.getTemplate(templateId)
      commit('SET_TEMPLATE', template)
      return template
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error(`获取模板失败 (ID=${templateId}):`, error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 创建新模板
  async createTemplate({ commit }, templateData) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const template = await templateApi.createTemplate(templateData)
      commit('ADD_TEMPLATE', template)
      return template
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error('创建模板失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 更新模板
  async updateTemplate({ commit }, { templateId, templateData }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const updatedTemplate = await templateApi.updateTemplate(templateId, templateData)
      commit('UPDATE_TEMPLATE', updatedTemplate)
      return updatedTemplate
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error(`更新模板失败 (ID=${templateId}):`, error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 删除模板
  async deleteTemplate({ commit }, templateId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      await templateApi.deleteTemplate(templateId)
      commit('DELETE_TEMPLATE', templateId)
      return true
    } catch (error) {
      commit('SET_ERROR', error.message)
      console.error(`删除模板失败 (ID=${templateId}):`, error)
      throw error
    } finally {
      commit('SET_LOADING', false)
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
