<template>
  <div class="agent-list">
    <h3 class="mb-4">Agent管理</h3>
    
    <!-- 刷新和检查状态按钮 -->
    <div class="d-flex justify-content-end mb-3">
      <b-button 
        variant="outline-secondary" 
        class="mr-2" 
        @click="handleCheckAgentsStatus"
        :disabled="loading"
      >
        <b-icon icon="arrow-repeat" class="mr-1"></b-icon>
        检查Agent状态
      </b-button>
      <b-button 
        variant="outline-primary" 
        @click="refreshAgents"
        :disabled="loading"
      >
        <b-icon icon="arrow-clockwise" class="mr-1"></b-icon>
        刷新列表
      </b-button>
    </div>
    
    <!-- 加载中提示 -->
    <div v-if="loading" class="text-center py-5">
      <b-spinner variant="primary" label="加载中..."></b-spinner>
      <p class="mt-2">加载Agent信息...</p>
    </div>
    
    <!-- 错误提示 -->
    <b-alert v-if="error" show variant="danger" dismissible>
      {{ error }}
    </b-alert>
    
    <!-- 无Agent提示 -->
    <b-alert v-if="!loading && mainAgents.length === 0" show variant="info">
      暂无Agent信息。您可以创建一个主Agent来开始任务调度系统。
      <div class="mt-2">
        <b-button variant="primary" size="sm" @click="showCreateAgentModal">
          <b-icon icon="plus"></b-icon> 创建主Agent
        </b-button>
      </div>
    </b-alert>
    
    <!-- Agent列表 -->
    <div v-else class="agent-tree">
      <!-- 主Agent列表 -->
      <div v-for="agent in mainAgents" :key="agent.id" class="mb-4">
        <!-- 主Agent卡片 -->
        <b-card 
          :class="['main-agent-card', { 'offline': agent.status === 'offline' }]"
          no-body
        >
          <b-card-header class="d-flex justify-content-between align-items-center">
            <div>
              <b-badge variant="primary" class="mr-2">主</b-badge>
              <strong>{{ agent.name }}</strong>
              <span class="text-muted ml-2">(ID: {{ agent.id }})</span>
            </div>
            <div>
              <b-badge 
                :variant="getStatusVariant(agent.status)" 
                class="mr-2"
              >
                {{ getStatusText(agent.status) }}
              </b-badge>
              <small class="text-muted">
                <b-icon icon="clock"></b-icon>
                运行时长: {{ formatDuration(agent.running_time) }}
              </small>
              <b-button 
                v-if="agent.status !== 'offline' && agent.status !== 'canceled'"
                variant="outline-danger" 
                size="sm" 
                class="ml-2"
                @click="handleCancelAgent(agent.id)"
              >
                取消
              </b-button>
            </div>
          </b-card-header>
          
          <b-card-body>
            <!-- CPU资源展示 -->
            <div class="resource-section mb-3">
              <h6 class="mb-2">CPU资源</h6>
              <div class="d-flex align-items-center">
                <strong class="mr-2">使用率:</strong>
                <b-progress 
                  :value="agent.cpu_usage || 0" 
                  :max="100" 
                  class="flex-grow-1"
                  :variant="getResourceVariant(agent.cpu_usage || 0)"
                  show-progress
                  height="1.5rem"
                >
                  <span>{{ agent.cpu_usage || 0 }}%</span>
                </b-progress>
              </div>
              <div class="mt-2">
                <strong>核心数:</strong> 
                {{ agent.cpu_cores || 0 }} 核 
                (可用: {{ agent.available_cpu_cores || 0 }} 核)
              </div>
            </div>
            
            <!-- GPU资源展示 -->
            <div class="resource-section" v-if="agent.gpu_ids && agent.gpu_ids.length > 0">
              <h6 class="mb-2">GPU资源</h6>
              <div v-for="(gpu, index) in agent.gpu_usage || []" :key="index" class="mb-2">
                <strong>GPU {{ agent.gpu_ids[index] || index }}:</strong>
                <div class="d-flex mt-1">
                  <div class="mr-3 text-nowrap">
                    <small>使用率:</small>
                  </div>
                  <b-progress 
                    :value="gpu.usage || 0" 
                    :max="100" 
                    class="flex-grow-1 mr-3"
                    :variant="getResourceVariant(gpu.usage || 0)"
                    show-progress
                  >
                    <span>{{ gpu.usage || 0 }}%</span>
                  </b-progress>
                </div>
                <div class="d-flex mt-1">
                  <div class="mr-3 text-nowrap">
                    <small>显存:</small>
                  </div>
                  <b-progress 
                    :value="gpu.memory_used || 0" 
                    :max="gpu.memory_total || 1" 
                    class="flex-grow-1 mr-3"
                    variant="success"
                    show-progress
                  >
                    <span>{{ gpu.memory_used || 0 }} / {{ gpu.memory_total || 0 }} MB</span>
                  </b-progress>
                </div>
              </div>
              <div v-if="!agent.gpu_usage || agent.gpu_usage.length === 0" class="text-muted">
                无GPU使用数据
              </div>
            </div>
          </b-card-body>
        </b-card>
        
        <!-- 子Agent列表 -->
        <div class="sub-agents ml-5 mt-2">
          <div 
            v-for="subAgent in getSubAgentsByMainId(agent.id)" 
            :key="subAgent.id" 
            class="mb-2"
          >
            <b-card 
              :class="['sub-agent-card', { 'offline': subAgent.status === 'offline' }]"
              no-body
            >
              <b-card-header class="d-flex justify-content-between align-items-center py-2">
                <div>
                  <b-badge variant="info" class="mr-2">子</b-badge>
                  <strong>{{ subAgent.name }}</strong>
                  <span class="text-muted ml-2">(ID: {{ subAgent.id }})</span>
                </div>
                <div>
                  <b-badge 
                    :variant="getStatusVariant(subAgent.status)" 
                    class="mr-2"
                  >
                    {{ getStatusText(subAgent.status) }}
                  </b-badge>
                  <small v-if="subAgent.task_id" class="text-muted mr-2">
                    <b-icon icon="card-list"></b-icon>
                    任务ID: <b-link :to="`/tasks/${subAgent.task_id}`">{{ subAgent.task_id }}</b-link>
                  </small>
                  <small class="text-muted">
                    <b-icon icon="clock"></b-icon>
                    运行时长: {{ formatDuration(subAgent.running_time) }}
                  </small>
                  <b-button 
                    v-if="subAgent.status !== 'offline' && subAgent.status !== 'canceled'"
                    variant="outline-danger" 
                    size="sm" 
                    class="ml-2"
                    @click="handleCancelAgent(subAgent.id)"
                  >
                    取消
                  </b-button>
                </div>
              </b-card-header>
              
              <b-card-body class="py-2">
                <!-- GPU使用情况 -->
                <div v-if="subAgent.gpu_ids && subAgent.gpu_ids.length > 0">
                  <div v-for="(gpu, index) in subAgent.gpu_usage || []" :key="index" class="mb-1">
                    <div class="d-flex align-items-center">
                      <small class="text-nowrap mr-2">GPU {{ subAgent.gpu_ids[index] || index }}:</small>
                      <b-progress 
                        :value="gpu.usage || 0" 
                        :max="100" 
                        class="flex-grow-1"
                        :variant="getResourceVariant(gpu.usage || 0)"
                        height="0.5rem"
                      ></b-progress>
                      <small class="ml-2">{{ gpu.usage || 0 }}%</small>
                    </div>
                  </div>
                </div>
                
                <!-- CPU使用情况 -->
                <div class="d-flex align-items-center mt-1">
                  <small class="text-nowrap mr-2">CPU使用率:</small>
                  <b-progress 
                    :value="subAgent.cpu_usage || 0" 
                    :max="100" 
                    class="flex-grow-1"
                    :variant="getResourceVariant(subAgent.cpu_usage || 0)"
                    height="0.5rem"
                  ></b-progress>
                  <small class="ml-2">{{ subAgent.cpu_usage || 0 }}%</small>
                </div>
              </b-card-body>
            </b-card>
          </div>
          
          <div v-if="getSubAgentsByMainId(agent.id).length === 0" class="text-muted ml-2 mt-2">
            <small>暂无子Agent</small>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 创建主Agent弹窗 -->
    <b-modal
      id="create-agent-modal"
      title="创建主Agent"
      ok-title="创建"
      cancel-title="取消"
      @ok="handleCreateMainAgent"
      :ok-disabled="!newAgentName || !newAgentCpuCores"
    >
      <b-form-group
        label="Agent名称"
        label-for="agent-name"
      >
        <b-form-input
          id="agent-name"
          v-model="newAgentName"
          required
          placeholder="请输入Agent名称"
        ></b-form-input>
      </b-form-group>
      
      <b-form-group
        label="CPU核心数"
        label-for="cpu-cores"
      >
        <b-form-input
          id="cpu-cores"
          v-model.number="newAgentCpuCores"
          type="number"
          min="1"
          required
          placeholder="分配的CPU核心数"
        ></b-form-input>
      </b-form-group>
      
      <b-form-group
        label="GPU ID列表 (可选)"
        label-for="gpu-ids"
        description="多个GPU ID使用逗号分隔"
      >
        <b-form-input
          id="gpu-ids"
          v-model="newAgentGpuIds"
          placeholder="例如: 0,1,2"
        ></b-form-input>
      </b-form-group>
    </b-modal>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import moment from 'moment'

export default {
  name: 'AgentList',
  
  data() {
    return {
      newAgentName: '',
      newAgentCpuCores: 1,
      newAgentGpuIds: '',
      pollingEnabled: true
    }
  },
  
  computed: {
    ...mapState('agents', ['loading', 'error']),
    ...mapGetters('agents', ['mainAgents', 'subAgents']),
    
    // 通过函数获取指定主Agent的子Agent
    getSubAgentsByMainId() {
      return (mainAgentId) => {
        return this.subAgents.filter(agent => agent.main_agent_id === mainAgentId)
      }
    }
  },
  
  methods: {
    ...mapActions('agents', [
      'fetchAgents', 
      'createMainAgent', 
      'cancelAgent',
      'checkAgentsStatus'
    ]),
    
    // 刷新Agent列表
    async refreshAgents() {
      try {
        await this.fetchAgents()
      } catch (error) {
        this.$bvToast.toast('获取Agent列表失败', {
          title: '错误',
          variant: 'danger',
          solid: true
        })
      }
    },
    
    // 创建主Agent
    async handleCreateMainAgent() {
      if (!this.newAgentName || !this.newAgentCpuCores) {
        return
      }
      
      // 解析GPU ID
      const gpuIds = this.newAgentGpuIds
        ? this.newAgentGpuIds.split(',').map(id => id.trim())
        : []
      
      try {
        await this.createMainAgent({
          name: this.newAgentName,
          cpu_cores: this.newAgentCpuCores,
          gpu_ids: gpuIds
        })
        
        this.$bvToast.toast('主Agent创建成功', {
          title: '成功',
          variant: 'success',
          solid: true
        })
        
        // 重置表单
        this.newAgentName = ''
        this.newAgentCpuCores = 1
        this.newAgentGpuIds = ''
        
        // 关闭弹窗
        this.$bvModal.hide('create-agent-modal')
      } catch (error) {
        this.$bvToast.toast('创建主Agent失败', {
          title: '错误',
          variant: 'danger',
          solid: true
        })
      }
    },
    
    // 取消Agent
    async handleCancelAgent(agentId) {
      try {
        await this.$bvModal.msgBoxConfirm('确定要取消此Agent吗？这将停止其所有任务。', {
          title: '确认取消',
          okVariant: 'danger',
          okTitle: '确认',
          cancelTitle: '取消'
        })
        
        await this.cancelAgent(agentId)
        
        this.$bvToast.toast('Agent已取消', {
          title: '成功',
          variant: 'success',
          solid: true
        })
      } catch (error) {
        if (error === false) return // 用户取消操作
        
        this.$bvToast.toast('取消Agent失败', {
          title: '错误',
          variant: 'danger',
          solid: true
        })
      }
    },
    
    // 检查所有Agent状态
    async handleCheckAgentsStatus() {
      try {
        await this.checkAgentsStatus()
        
        this.$bvToast.toast('Agent状态已更新', {
          title: '成功',
          variant: 'success',
          solid: true
        })
      } catch (error) {
        this.$bvToast.toast('检查Agent状态失败', {
          title: '错误',
          variant: 'danger',
          solid: true
        })
      }
    },
    
    // 显示创建Agent弹窗
    showCreateAgentModal() {
      this.$bvModal.show('create-agent-modal')
    },
    
    // 格式化状态为文本
    getStatusText(status) {
      const statusMap = {
        'online': '在线',
        'offline': '离线',
        'busy': '忙碌',
        'idle': '空闲',
        'starting': '启动中',
        'canceled': '已取消'
      }
      return statusMap[status] || status
    },
    
    // 获取状态对应的样式
    getStatusVariant(status) {
      const variantMap = {
        'online': 'success',
        'offline': 'secondary',
        'busy': 'warning',
        'idle': 'info',
        'starting': 'primary',
        'canceled': 'danger'
      }
      return variantMap[status] || 'secondary'
    },
    
    // 获取资源使用率对应的样式
    getResourceVariant(usage) {
      if (usage >= 90) return 'danger'
      if (usage >= 70) return 'warning'
      return 'success'
    },
    
    // 格式化运行时长
    formatDuration(seconds) {
      if (!seconds) return '0秒'
      
      const duration = moment.duration(seconds, 'seconds')
      const days = duration.days()
      const hours = duration.hours()
      const minutes = duration.minutes()
      const secs = duration.seconds()
      
      let result = ''
      if (days > 0) result += `${days}天 `
      if (hours > 0) result += `${hours}小时 `
      if (minutes > 0) result += `${minutes}分钟 `
      if (secs > 0 && days === 0 && hours === 0) result += `${secs}秒`
      
      return result.trim()
    }
  },
  
  created() {
    // 获取Agent列表
    this.refreshAgents()
    
    // 启动轮询
    this.pollingTimeout = setTimeout(() => {
      this.refreshAgents()
    }, 5000)
  },
  
  beforeDestroy() {
    // 清除轮询
    if (this.pollingTimeout) {
      clearTimeout(this.pollingTimeout)
    }
    this.pollingEnabled = false
  }
}
</script>

<style scoped>
.agent-tree {
  margin-top: 20px;
}

.main-agent-card {
  border-left: 4px solid #007bff;
}

.sub-agent-card {
  border-left: 3px solid #17a2b8;
}

.offline {
  opacity: 0.7;
  border-left-color: #6c757d;
}

.resource-section {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
}
</style>
