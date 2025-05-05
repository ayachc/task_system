<template>
  <div class="agent-list">
    <h3 class="mb-4">Agent管理</h3>
    
    <!-- 刷新按钮和新建主Agent按钮 -->
    <div class="d-flex justify-content-between mb-3">
      <b-button 
        variant="primary" 
        size="sm"
        @click="showCreateAgentModal"
      >
        <b-icon icon="plus"></b-icon> 创建主Agent
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
    </b-alert>
    
    <!-- Agent列表 -->
    <div v-else class="agent-tree">
      <!-- 主Agent列表 -->
      <div v-for="agent in mainAgents" :key="agent.id" class="mb-5">
        <!-- 主Agent卡片 -->
        <b-card 
          :class="['main-agent-card', { 'offline': agent.status === 'offline' }]"
          no-body
        >
          <b-card-header class="d-flex justify-content-between align-items-center py-2">
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
              <small class="text-muted mr-2">
                <b-icon icon="clock-history"></b-icon>
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
          
          <b-card-body class="py-3">
            <!-- 基本信息展示区域 -->
            <div class="agent-info-grid mb-3">
              <div class="info-item">
                <small class="text-muted">创建时间：</small>
                <div>{{ formatTime(agent.created_time) }}</div>
              </div>
              <div class="info-item">
                <small class="text-muted">上次心跳：</small>
                <div>{{ formatTime(agent.last_heartbeat_time) }}</div>
              </div>
              <div class="info-item">
                <small class="text-muted">CPU核心数：</small>
                <div>{{ agent.cpu_cores || 0 }} 核 (可用: {{ agent.available_cpu_cores || 0 }} 核)</div>
              </div>
              <div class="info-item">
                <small class="text-muted">CPU使用率：</small>
                <div class="d-flex align-items-center">
                  <b-progress 
                    :value="agent.cpu_usage || 0" 
                    :max="100" 
                    class="flex-grow-1 mr-2"
                    :variant="getResourceVariant(agent.cpu_usage || 0)"
                    height="0.7rem"
                  ></b-progress>
                  <span class="text-nowrap">{{ agent.cpu_usage || 0 }}%</span>
                </div>
              </div>
              <div class="info-item">
                <small class="text-muted">内存使用率：</small>
                <div class="d-flex align-items-center">
                  <b-progress 
                    :value="agent.memory_usage || 0" 
                    :max="100" 
                    class="flex-grow-1 mr-2"
                    :variant="getResourceVariant(agent.memory_usage || 0)"
                    height="0.7rem"
                  ></b-progress>
                  <span class="text-nowrap">{{ agent.memory_usage || 0 }}%</span>
                </div>
              </div>
              <div class="info-item" v-if="agent.monitor_file">
                <small class="text-muted">监控文件：</small>
                <div>{{ agent.monitor_file }}</div>
              </div>
            </div>
            
            <!-- GPU资源展示 -->
            <div class="resource-section" v-if="agent.gpu_info && agent.gpu_info.length > 0">
              <h6 class="mb-2">GPU资源</h6>
              <b-row class="gpu-grid">
                <b-col md="6" lg="4" v-for="(gpu, index) in agent.gpu_info" :key="index" class="mb-2">
                  <div class="gpu-card p-2">
                    <div class="d-flex justify-content-between">
                      <strong>GPU {{ gpu.gpu_id }}</strong>
                      <b-badge 
                        :variant="gpu.is_available ? 'success' : 'secondary'"
                      >
                        {{ gpu.is_available ? '可用' : '使用中' }}
                      </b-badge>
                    </div>
                    <div class="mt-2">
                      <small class="d-block mb-1">使用率:</small>
                      <b-progress 
                        :value="gpu.usage || 0" 
                        :max="100" 
                        :variant="getResourceVariant(gpu.usage || 0)"
                        class="mb-2"
                        height="0.6rem"
                      >
                        <span>{{ gpu.usage || 0 }}%</span>
                      </b-progress>
                    </div>
                    <div>
                      <small class="d-block mb-1">显存:</small>
                      <b-progress 
                        :value="gpu.memory_used || 0" 
                        :max="gpu.memory_total || 1" 
                        variant="info"
                        class="mb-1"
                        height="0.6rem"
                      ></b-progress>
                      <div class="d-flex justify-content-between">
                        <small>{{ formatMemory(gpu.memory_used) }}</small>
                        <small>{{ formatMemory(gpu.memory_total) }}</small>
                      </div>
                    </div>
                  </div>
                </b-col>
              </b-row>
            </div>
          </b-card-body>
        </b-card>
        
        <!-- 子Agent列表 -->
        <div class="sub-agents ml-4 mt-3">
          <div 
            v-for="subAgent in getSubAgentsByMainId(agent.id)" 
            :key="subAgent.id" 
            class="mb-3"
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
                  <small class="text-muted mr-2">
                    <b-icon icon="clock-history"></b-icon>
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
              
              <b-card-body class="py-3">
                <!-- 基本信息展示区域 -->
                <div class="agent-info-grid">
                  <div class="info-item">
                    <small class="text-muted">创建时间：</small>
                    <div>{{ formatTime(subAgent.created_time) }}</div>
                  </div>
                  <div class="info-item">
                    <small class="text-muted">上次心跳：</small>
                    <div>{{ formatTime(subAgent.last_heartbeat_time) }}</div>
                  </div>
                  <div class="info-item">
                    <small class="text-muted">CPU核心数：</small>
                    <div>{{ subAgent.cpu_cores || 0 }} 核</div>
                  </div>
                  <div class="info-item">
                    <small class="text-muted">CPU使用率：</small>
                    <div class="d-flex align-items-center">
                      <b-progress 
                        :value="subAgent.cpu_usage || 0" 
                        :max="100" 
                        class="flex-grow-1 mr-2"
                        :variant="getResourceVariant(subAgent.cpu_usage || 0)"
                        height="0.7rem"
                      ></b-progress>
                      <span class="text-nowrap">{{ subAgent.cpu_usage || 0 }}%</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <small class="text-muted">内存使用率：</small>
                    <div class="d-flex align-items-center">
                      <b-progress 
                        :value="subAgent.memory_usage || 0" 
                        :max="100" 
                        class="flex-grow-1 mr-2"
                        :variant="getResourceVariant(subAgent.memory_usage || 0)"
                        height="0.7rem"
                      ></b-progress>
                      <span class="text-nowrap">{{ subAgent.memory_usage || 0 }}%</span>
                    </div>
                  </div>
                  <div class="info-item" v-if="subAgent.monitor_file">
                    <small class="text-muted">监控文件：</small>
                    <div>{{ subAgent.monitor_file }}</div>
                  </div>
                </div>
                
                <!-- GPU资源展示 -->
                <div class="resource-section mt-3" v-if="subAgent.gpu_info && subAgent.gpu_info.length > 0">
                  <h6 class="mb-2">GPU资源</h6>
                  <b-row class="gpu-grid">
                    <b-col md="6" lg="4" v-for="(gpu, index) in subAgent.gpu_info" :key="index" class="mb-2">
                      <div class="gpu-card p-2">
                        <div class="d-flex justify-content-between">
                          <strong>GPU {{ gpu.gpu_id }}</strong>
                        </div>
                        <div class="mt-2">
                          <small class="d-block mb-1">使用率:</small>
                          <b-progress 
                            :value="gpu.usage || 0" 
                            :max="100" 
                            :variant="getResourceVariant(gpu.usage || 0)"
                            class="mb-2"
                            height="0.6rem"
                          >
                            <span>{{ gpu.usage || 0 }}%</span>
                          </b-progress>
                        </div>
                        <div>
                          <small class="d-block mb-1">显存:</small>
                          <b-progress 
                            :value="gpu.memory_used || 0" 
                            :max="gpu.memory_total || 1" 
                            variant="info"
                            class="mb-1"
                            height="0.6rem"
                          ></b-progress>
                          <div class="d-flex justify-content-between">
                            <small>{{ formatMemory(gpu.memory_used) }}</small>
                            <small>{{ formatMemory(gpu.memory_total) }}</small>
                          </div>
                        </div>
                      </div>
                    </b-col>
                  </b-row>
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
      
      <b-form-group
        label="监控文件路径 (可选)"
        label-for="monitor-file"
      >
        <b-form-input
          id="monitor-file"
          v-model="newAgentMonitorFile"
          placeholder="例如: /path/to/monitor.log"
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
      newAgentMonitorFile: '',
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
      'cancelAgent'
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
          gpu_ids: gpuIds,
          monitor_file: this.newAgentMonitorFile || null
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
        this.newAgentMonitorFile = ''
        
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
    },
    
    // 格式化日期时间
    formatTime(timestamp) {
      if (!timestamp) return '未知'
      return moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
    },
    
    // 格式化内存大小
    formatMemory(bytes) {
      if (!bytes) return '0 MB'
      if (bytes < 1024) return `${bytes} MB`
      return `${(bytes / 1024).toFixed(1)} GB`
    },
    
    // 启动Agent状态轮询
    startPolling() {
      const poll = () => {
        if (!this.pollingEnabled) return
        
        this.refreshAgents()
          .finally(() => {
            this.pollingTimeout = setTimeout(poll, 5000)
          })
      }
      
      this.pollingTimeout = setTimeout(poll, 5000)
    }
  },
  
  created() {
    // 获取Agent列表
    this.refreshAgents()
    
    // 启动轮询
    this.startPolling()
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
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.sub-agent-card {
  border-left: 3px solid #17a2b8;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
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

.agent-info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

@media (max-width: 992px) {
  .agent-info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .agent-info-grid {
    grid-template-columns: 1fr;
  }
}

.info-item {
  margin-bottom: 5px;
}

.gpu-card {
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #eee;
  height: 100%;
}

.gpu-grid {
  margin: 0 -5px;
}

.gpu-grid .col {
  padding: 0 5px;
}
</style>
