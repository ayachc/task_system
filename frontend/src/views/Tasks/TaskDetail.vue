<template>
  <div class="task-detail">
    <!-- 加载中提示 -->
    <div v-if="loading" class="text-center my-5">
      <b-spinner variant="primary"></b-spinner>
      <p class="mt-2">加载任务详情...</p>
    </div>
    
    <div v-else-if="!task" class="alert alert-danger">
      任务不存在或已被删除
    </div>
    
    <div v-else>
      <!-- 错误提示 -->
      <b-alert v-if="task.status === 'failed'" show variant="danger" class="mb-4">
        <h5><i class="bi bi-exclamation-triangle-fill mr-2"></i>任务执行失败</h5>
        请查看日志了解详细错误信息
      </b-alert>
      
      <!-- 任务信息卡片 -->
      <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">任务信息</h5>
          <b-badge :class="'status-' + task.status">{{ getStatusText(task.status) }}</b-badge>
        </div>
        
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <dl class="row mb-0">
                <dt class="col-sm-4">ID</dt>
                <dd class="col-sm-8">{{ task.id }}</dd>
                
                <dt class="col-sm-4">名称</dt>
                <dd class="col-sm-8">{{ task.name }}</dd>
                
                <dt class="col-sm-4">模板类型</dt>
                <dd class="col-sm-8">{{ task.template_type }}</dd>
                
                <dt class="col-sm-4">优先级</dt>
                <dd class="col-sm-8">
                  <b-badge variant="secondary">{{ getPriorityText(task.priority) }}</b-badge>
                </dd>
                
                <dt class="col-sm-4">状态</dt>
                <dd class="col-sm-8">
                  <b-badge :class="'status-' + task.status">
                    {{ getStatusText(task.status) }}
                  </b-badge>
                </dd>
              </dl>
            </div>
            
            <div class="col-md-6">
              <dl class="row mb-0">
                <dt class="col-sm-4">创建时间</dt>
                <dd class="col-sm-8">{{ formatDate(task.created_time) }}</dd>
                
                <dt class="col-sm-4">开始时间</dt>
                <dd class="col-sm-8">{{ task.start_time ? formatDate(task.start_time) : '尚未开始' }}</dd>
                
                <dt class="col-sm-4">结束时间</dt>
                <dd class="col-sm-8">{{ task.end_time ? formatDate(task.end_time) : '尚未结束' }}</dd>
                
                <dt class="col-sm-4">执行耗时</dt>
                <dd class="col-sm-8">{{ task.execution_time ? formatDuration(task.execution_time) : '尚未完成' }}</dd>
                
                <dt class="col-sm-4">执行Agent</dt>
                <dd class="col-sm-8">{{ task.agent_id || '尚未分配' }}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 资源需求卡片 -->
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">资源需求</h5>
        </div>
        
        <div class="card-body">
          <div class="row">
            <div class="col-md-4">
              <div class="d-flex align-items-center">
                <div class="mr-2 resource-icon">
                  <i class="bi bi-cpu"></i>
                </div>
                <div>
                  <div class="text-muted small">CPU核心数</div>
                  <div class="font-weight-bold">{{ task.cpu_cores || 1 }}</div>
                </div>
              </div>
            </div>
            
            <div class="col-md-4">
              <div class="d-flex align-items-center">
                <div class="mr-2 resource-icon">
                  <i class="bi bi-gpu-card"></i>
                </div>
                <div>
                  <div class="text-muted small">GPU数量</div>
                  <div class="font-weight-bold">{{ task.gpu_count || 0 }}</div>
                </div>
              </div>
            </div>
            
            <div class="col-md-4">
              <div class="d-flex align-items-center">
                <div class="mr-2 resource-icon">
                  <i class="bi bi-memory"></i>
                </div>
                <div>
                  <div class="text-muted small">GPU显存(GB/卡)</div>
                  <div class="font-weight-bold">{{ task.gpu_memory || 0 }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 依赖任务 -->
      <div v-if="task.depends_on && task.depends_on.length > 0" class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">依赖任务</h5>
        </div>
        
        <div class="card-body">
          <div class="list-group">
            <div v-for="dependId in task.depends_on" :key="dependId" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
              <span>任务 #{{ dependId }}</span>
              <b-button size="sm" variant="outline-primary" @click="viewTaskDetail(dependId)">查看</b-button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 脚本内容 -->
      <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">脚本内容</h5>
          <b-button size="sm" variant="outline-secondary" v-b-toggle.script-collapse>
            <i class="bi bi-code-slash mr-1"></i> 显示/隐藏
          </b-button>
        </div>
        
        <b-collapse id="script-collapse" visible>
          <div class="card-body p-0">
            <pre class="script-content">{{ task.script_content }}</pre>
          </div>
        </b-collapse>
      </div>
      
      <!-- 执行日志 -->
      <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">执行日志</h5>
          <div>
            <b-button size="sm" variant="outline-secondary" class="mr-2" @click="refreshLog">
              <i class="bi bi-arrow-clockwise mr-1"></i> 刷新
            </b-button>
            <b-form-checkbox v-model="autoRefresh" switch class="d-inline-block ml-2">
              自动刷新
            </b-form-checkbox>
          </div>
        </div>
        
        <div class="card-body p-0">
          <div class="log-container" ref="logContainer">
            <pre class="log-content m-0 p-3" v-if="taskLog">{{ taskLog }}</pre>
            <div v-else class="text-center py-4 text-muted">
              <p>暂无日志信息</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="mt-4 d-flex justify-content-between">
        <b-button variant="secondary" @click="$router.push('/tasks')">返回任务列表</b-button>
        
        <b-button 
          v-if="['waiting', 'blocked', 'running'].includes(task.status)"
          variant="danger" 
          @click="confirmCancel"
        >
          取消任务
        </b-button>
      </div>
      
      <!-- 取消任务确认框 -->
      <b-modal 
        id="cancel-modal" 
        title="取消任务" 
        ok-title="确认取消" 
        ok-variant="danger"
        cancel-title="返回"
        @ok="cancelTask"
      >
        <p>您确认要取消任务 <strong>{{ task ? task.name : '' }}</strong> 吗？</p>
        <p class="text-danger">此操作不可撤销！</p>
      </b-modal>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import moment from 'moment'

export default {
  name: 'TaskDetail',
  
  props: {
    id: {
      type: [String, Number],
      required: true
    }
  },
  
  data() {
    return {
      taskLog: '',
      autoRefresh: true,
      refreshInterval: null
    }
  },
  
  computed: {
    ...mapState({
      task: state => state.tasks.task,
      loading: state => state.loading,
      error: state => state.error
    })
  },
  
  methods: {
    ...mapActions('tasks', [
      'fetchTask',
      'fetchTaskLog',
      'cancelTask'
    ]),
    ...mapActions(['clearError']),
    
    // 格式化日期
    formatDate(dateStr) {
      if (!dateStr) return ''
      return moment(dateStr).format('YYYY-MM-DD HH:mm:ss')
    },
    
    // 格式化持续时间（秒转为易读格式）
    formatDuration(seconds) {
      if (!seconds) return '0秒'
      
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const remainingSeconds = seconds % 60
      
      let result = ''
      if (hours > 0) result += `${hours}小时 `
      if (minutes > 0) result += `${minutes}分钟 `
      if (remainingSeconds > 0 || !result) result += `${remainingSeconds}秒`
      
      return result
    },
    
    // 获取状态文本
    getStatusText(status) {
      const statusMap = {
        'waiting': '等待中',
        'blocked': '被阻塞',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'canceled': '已取消'
      }
      return statusMap[status] || status
    },
    
    // 获取优先级文本
    getPriorityText(priority) {
      const priorityMap = {
        1: '最高',
        2: '高',
        3: '中',
        4: '低',
        5: '最低'
      }
      return priorityMap[priority] || priority
    },
    
    // 跳转到其他任务详情
    viewTaskDetail(taskId) {
      this.$router.push(`/tasks/${taskId}`)
    },
    
    // 确认取消任务
    confirmCancel() {
      this.$bvModal.show('cancel-modal')
    },
    
    // 刷新日志
    async refreshLog() {
      try {
        const response = await this.fetchTaskLog({
          taskId: this.id
        })
        this.taskLog = response.log || ''
        
        // 自动滚动到日志底部
        this.$nextTick(() => {
          if (this.$refs.logContainer) {
            this.$refs.logContainer.scrollTop = this.$refs.logContainer.scrollHeight
          }
        })
      } catch (error) {
        console.error('获取任务日志失败:', error)
      }
    },
    
    // 更新任务状态和日志
    async updateTaskData() {
      await this.fetchTask(this.id)
      await this.refreshLog()
    },
    
    // 执行任务取消
    async cancelTask() {
      try {
        await this.cancelTask(this.id)
        
        this.$bvToast.toast('任务已成功取消', {
          title: '操作成功',
          variant: 'success',
          solid: true
        })
        
        // 更新任务状态
        await this.updateTaskData()
      } catch (error) {
        // 错误已经在action中处理
      }
    },
    
    // 开始自动刷新
    startAutoRefresh() {
      this.stopAutoRefresh() // 先清除现有定时器
      
      if (this.autoRefresh && this.task && ['running', 'waiting', 'blocked'].includes(this.task.status)) {
        this.refreshInterval = setInterval(() => {
          this.updateTaskData()
        }, 5000) // 每5秒刷新一次
      }
    },
    
    // 停止自动刷新
    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
    }
  },
  
  async created() {
    // 初始加载任务数据
    await this.updateTaskData()
    
    // 设置自动刷新
    this.startAutoRefresh()
  },
  
  beforeDestroy() {
    // 清除定时器
    this.stopAutoRefresh()
  },
  
  watch: {
    // 监听ID变化，重新加载数据
    id: {
      handler: 'updateTaskData',
      immediate: true
    },
    
    // 监听自动刷新开关
    autoRefresh(newVal) {
      if (newVal) {
        this.startAutoRefresh()
      } else {
        this.stopAutoRefresh()
      }
    },
    
    // 监听任务状态，自动停止刷新
    'task.status'(newStatus) {
      if (!['running', 'waiting', 'blocked'].includes(newStatus)) {
        this.autoRefresh = false
      }
    }
  }
}
</script>

<style scoped>
.resource-icon {
  font-size: 1.5rem;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 123, 255, 0.1);
  border-radius: 50%;
  color: #007bff;
}

.log-container {
  max-height: 500px;
  overflow-y: auto;
  background-color: #212529;
  color: #f8f9fa;
}

.script-content {
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 0.875rem;
  max-height: 300px;
  overflow-y: auto;
}

.log-content {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85rem;
  white-space: pre-wrap;
}
</style>
