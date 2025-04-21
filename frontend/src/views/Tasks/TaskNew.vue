<template>
  <div class="task-new">
    <b-form @submit.prevent="submitTask" class="mt-3">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">基本信息</h5>
        </div>
        <div class="card-body">
          <!-- 基本信息 -->
          <div class="row">
            <!-- 任务名称 -->
            <div class="col-md-6">
              <b-form-group
                label="任务名称"
                label-for="task-name"
                :state="nameState"
                :invalid-feedback="nameInvalidFeedback"
              >
                <b-form-input
                  id="task-name"
                  v-model="task.name"
                  :state="nameState"
                  required
                  placeholder="请输入任务名称"
                ></b-form-input>
              </b-form-group>
            </div>
            
            <!-- 模板类型 -->
            <div class="col-md-6">
              <b-form-group
                label="模板类型"
                label-for="template-type"
                :state="templateTypeState"
                :invalid-feedback="templateTypeInvalidFeedback"
              >
                <b-form-select
                  id="template-type"
                  v-model="task.template_type"
                  :options="templateOptions"
                  :state="templateTypeState"
                  required
                  @change="handleTemplateChange"
                ></b-form-select>
              </b-form-group>
            </div>
            
            <!-- 优先级 -->
            <div class="col-md-6">
              <b-form-group label="优先级" label-for="priority">
                <div class="d-flex align-items-center">
                  <b-form-input
                    id="priority"
                    v-model="task.priority"
                    type="range"
                    min="1"
                    max="5"
                    step="1"
                    class="mr-3"
                  ></b-form-input>
                  <span class="priority-label">{{ getPriorityText(task.priority) }}</span>
                </div>
              </b-form-group>
            </div>
            
            <!-- 依赖任务 -->
            <div class="col-md-6">
              <b-form-group
                label="依赖任务 (可选)"
                label-for="depends-on"
                description="多个任务ID用逗号分隔"
                :state="dependsOnState"
                :invalid-feedback="dependsOnInvalidFeedback"
              >
                <b-form-input
                  id="depends-on"
                  v-model="task.depends_on"
                  :state="dependsOnState"
                  placeholder="例如: 1,2,3"
                ></b-form-input>
              </b-form-group>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 资源配置 -->
      <div class="card mt-3">
        <div class="card-header">
          <h5 class="mb-0">资源配置</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <!-- CPU核心数 -->
            <div class="col-md-4">
              <b-form-group
                label="CPU核心数"
                label-for="cpu-cores"
                :state="cpuCoresState"
                :invalid-feedback="cpuCoresInvalidFeedback"
              >
                <b-form-input
                  id="cpu-cores"
                  v-model.number="task.cpu_cores"
                  type="number"
                  min="1"
                  :state="cpuCoresState"
                  placeholder="默认: 1"
                ></b-form-input>
              </b-form-group>
            </div>
            
            <!-- GPU数量 -->
            <div class="col-md-4">
              <b-form-group
                label="GPU数量"
                label-for="gpu-count"
                :state="gpuCountState"
                :invalid-feedback="gpuCountInvalidFeedback"
              >
                <b-form-input
                  id="gpu-count"
                  v-model.number="task.gpu_count"
                  type="number"
                  min="0"
                  :state="gpuCountState"
                  placeholder="默认: 0"
                ></b-form-input>
              </b-form-group>
            </div>
            
            <!-- GPU显存 -->
            <div class="col-md-4">
              <b-form-group
                label="GPU显存要求 (每卡GB)"
                label-for="gpu-memory"
                :state="gpuMemoryState"
              >
                <b-form-select
                  id="gpu-memory"
                  v-model.number="task.gpu_memory"
                  :options="gpuMemoryOptions"
                  :state="gpuMemoryState"
                ></b-form-select>
              </b-form-group>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 脚本内容 -->
      <div class="card mt-3">
        <div class="card-header">
          <h5 class="mb-0">脚本内容</h5>
        </div>
        <div class="card-body">
          <b-form-group
            label-for="script-content"
            :state="scriptContentState"
            :invalid-feedback="scriptContentInvalidFeedback"
          >
            <b-form-textarea
              id="script-content"
              v-model="task.script_content"
              rows="12"
              :state="scriptContentState"
              required
              placeholder="请输入脚本内容"
              no-resize
              class="code-textarea"
            ></b-form-textarea>
          </b-form-group>
        </div>
      </div>
      
      <!-- 错误提示 -->
      <b-alert 
        v-if="error" 
        variant="danger" 
        dismissible 
        show 
        class="mt-3"
        @dismissed="clearError"
      >
        {{ error }}
      </b-alert>
      
      <!-- 提交按钮 -->
      <div class="mt-4 d-flex justify-content-between">
        <b-button variant="secondary" @click="$router.push('/tasks')">取消</b-button>
        <b-button type="submit" variant="primary" :disabled="loading">
          <b-spinner small v-if="loading" class="mr-1"></b-spinner>
          创建任务
        </b-button>
      </div>
    </b-form>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'

export default {
  name: 'TaskNew',
  
  data() {
    return {
      task: {
        name: '',
        template_type: '',
        script_content: '',
        priority: 3,
        depends_on: '',
        cpu_cores: 1,
        gpu_count: 0,
        gpu_memory: 0
      },
      validated: false,
      gpuMemoryOptions: [
        { value: 0, text: '不使用GPU' },
        { value: 8, text: '8 GB' },
        { value: 12, text: '12 GB' },
        { value: 16, text: '16 GB' },
        { value: 24, text: '24 GB' },
        { value: 32, text: '32 GB' },
        { value: 48, text: '48 GB' },
        { value: 80, text: '80 GB' }
      ]
    }
  },
  
  computed: {
    ...mapState({
      loading: state => state.loading,
      error: state => state.error
    }),
    ...mapGetters('templates', ['allTemplates']),
    
    // 模板选项
    templateOptions() {
      const options = [
        { value: '', text: '请选择模板类型' },
        { value: 'custom', text: '自定义脚本' }
      ]
      
      // 添加可用的模板类型
      if (this.allTemplates && this.allTemplates.length > 0) {
        const templateTypes = [...new Set(this.allTemplates.map(t => t.template_type))]
        
        templateTypes.forEach(type => {
          if (type) {
            options.push({
              value: type,
              text: type
            })
          }
        })
      }
      
      return options
    },
    
    // 表单验证状态
    nameState() {
      if (!this.validated) return null
      return this.task.name.trim().length > 0
    },
    
    templateTypeState() {
      if (!this.validated) return null
      return this.task.template_type.trim().length > 0
    },
    
    scriptContentState() {
      if (!this.validated) return null
      return this.task.script_content.trim().length > 0
    },
    
    cpuCoresState() {
      if (!this.validated) return null
      return this.task.cpu_cores > 0
    },
    
    gpuCountState() {
      if (!this.validated) return null
      return this.task.gpu_count >= 0
    },
    
    gpuMemoryState() {
      if (!this.validated) return null
      return true // 永远有效，因为是下拉选择
    },
    
    dependsOnState() {
      if (!this.validated || !this.task.depends_on) return null
      const pattern = /^(\d+)(,\d+)*$/
      return pattern.test(this.task.depends_on)
    },
    
    // 错误反馈消息
    nameInvalidFeedback() {
      return '请输入任务名称'
    },
    
    templateTypeInvalidFeedback() {
      return '请选择模板类型'
    },
    
    scriptContentInvalidFeedback() {
      return '请输入脚本内容'
    },
    
    cpuCoresInvalidFeedback() {
      return 'CPU核心数必须大于0'
    },
    
    gpuCountInvalidFeedback() {
      return 'GPU数量不能为负数'
    },
    
    dependsOnInvalidFeedback() {
      return '请输入有效的任务ID，多个ID用逗号分隔'
    }
  },
  
  methods: {
    ...mapActions('tasks', ['createTask']),
    ...mapActions('templates', ['fetchTemplates']),
    ...mapActions(['clearError']),
    
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
    
    // 处理模板变更
    handleTemplateChange() {
      if (this.task.template_type && this.task.template_type !== 'custom') {
        // 查找对应的模板内容
        const template = this.allTemplates.find(t => t.template_type === this.task.template_type)
        if (template) {
          this.task.script_content = template.script_content || ''
        }
      } else if (this.task.template_type === 'custom') {
        // 自定义脚本，清空内容
        this.task.script_content = ''
      }
    },
    
    // 解析依赖任务ID
    parseDependsOn() {
      if (!this.task.depends_on) {
        return []
      }
      
      return this.task.depends_on.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
    },
    
    // 提交任务
    async submitTask() {
      this.validated = true
      
      // 验证表单
      if (
        !this.nameState ||
        !this.templateTypeState ||
        !this.scriptContentState ||
        !this.cpuCoresState ||
        !this.gpuCountState ||
        (this.task.depends_on && !this.dependsOnState)
      ) {
        this.$bvToast.toast('请修正表单中的错误', {
          title: '验证失败',
          variant: 'danger',
          solid: true
        })
        return
      }
      
      // 准备任务数据
      const taskData = {
        name: this.task.name,
        template_type: this.task.template_type,
        script_content: this.task.script_content,
        priority: parseInt(this.task.priority),
        cpu_cores: parseInt(this.task.cpu_cores),
        gpu_count: parseInt(this.task.gpu_count),
        gpu_memory: parseInt(this.task.gpu_memory),
        depends_on: this.parseDependsOn()
      }
      
      try {
        // 提交任务
        const result = await this.createTask(taskData)
        
        this.$bvToast.toast('任务创建成功', {
          title: '成功',
          variant: 'success',
          solid: true
        })
        
        // 跳转到任务详情页
        this.$router.push(`/tasks/${result.id}`)
      } catch (error) {
        // 错误已在store中处理
      }
    }
  },
  
  async created() {
    try {
      // 获取模板列表
      await this.fetchTemplates()
    } catch (error) {
      console.error('获取模板数据失败:', error)
    }
  }
}
</script>

<style scoped>
.priority-label {
  width: 2.5rem;
  text-align: center;
}

.code-textarea {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85rem;
}
</style>
