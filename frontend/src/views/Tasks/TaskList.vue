<template>
  <div class="task-list">
    <!-- 任务过滤器 -->
    <div class="card mb-4">
      <div class="card-body">
        <h5 class="card-title">筛选条件</h5>
        <div class="row">
          <div class="col-md-3">
            <b-form-group label="状态">
              <b-form-select v-model="filterStatus" :options="statusOptions" @change="applyFilters"></b-form-select>
            </b-form-group>
          </div>
          <div class="col-md-3">
            <b-form-group label="模板类型">
              <b-form-select v-model="filterTemplateType" :options="templateTypeOptions" @change="applyFilters"></b-form-select>
            </b-form-group>
          </div>
          <div class="col-md-4">
            <b-form-group label="名称关键词">
              <b-form-input v-model="filterName" placeholder="输入任务名称关键词" @input="debounceSearch"></b-form-input>
            </b-form-group>
          </div>
          <div class="col-md-2 d-flex align-items-end">
            <b-button variant="outline-secondary" size="sm" @click="clearFilters" class="w-100">
              <i class="bi bi-x-circle mr-1"></i>清空筛选
            </b-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 任务表格 -->
    <div class="card">
      <div class="card-body p-0">
        <b-table 
          striped 
          hover 
          :items="tasks" 
          :fields="fields"
          :busy="loading"
          show-empty
          empty-text="没有找到任务，请调整筛选条件"
          responsive
          class="mb-0"
        >
          <!-- 状态列 -->
          <template #cell(status)="data">
            <b-badge :class="'status-' + data.value">{{ getStatusText(data.value) }}</b-badge>
          </template>
          
          <!-- 优先级列 -->
          <template #cell(priority)="data">
            <b-badge variant="secondary">{{ getPriorityText(data.value) }}</b-badge>
          </template>
          
          <!-- 创建时间列 -->
          <template #cell(created_time)="data">
            {{ formatDate(data.value) }}
          </template>
          
          <!-- 操作列 -->
          <template #cell(actions)="data">
            <b-button-group size="sm">
              <b-button variant="outline-primary" @click="viewTaskDetail(data.item.id)">
                <i class="bi bi-eye"></i>
              </b-button>
              <b-button 
                variant="outline-danger" 
                @click="confirmCancel(data.item)" 
                :disabled="!['waiting', 'blocked', 'running'].includes(data.item.status)"
              >
                <i class="bi bi-x-circle"></i>
              </b-button>
            </b-button-group>
          </template>
          
          <!-- 加载中提示 -->
          <template #table-busy>
            <div class="text-center my-2">
              <b-spinner class="align-middle"></b-spinner>
              <strong> 加载中...</strong>
            </div>
          </template>
        </b-table>
      </div>
      
      <!-- 分页 -->
      <div class="card-footer d-flex justify-content-between align-items-center">
        <small class="text-muted">共 {{ pagination.total }} 条记录</small>
        <b-pagination
          v-model="currentPage"
          :total-rows="pagination.total"
          :per-page="pagination.perPage"
          :limit="5"
          align="right"
          size="sm"
          class="my-0"
          @change="changePage"
        ></b-pagination>
      </div>
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
      <p>您确认要取消任务 <strong>{{ selectedTask ? selectedTask.name : '' }}</strong> 吗？</p>
      <p class="text-danger">此操作不可撤销！已取消的任务将不会被执行。</p>
    </b-modal>
    
    <!-- 全局错误提示 -->
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
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import moment from 'moment'

export default {
  name: 'TaskList',
  
  data() {
    return {
      fields: [
        { key: 'id', label: 'ID', sortable: true },
        { key: 'name', label: '任务名称', sortable: true },
        { key: 'template_type', label: '模板类型', sortable: true },
        { key: 'priority', label: '优先级', sortable: true },
        { key: 'status', label: '状态', sortable: true },
        { key: 'created_time', label: '创建时间', sortable: true },
        { key: 'actions', label: '操作' }
      ],
      selectedTask: null,
      currentPage: 1,
      debounceTimer: null,
      filterStatus: '',
      filterName: '',
      filterTemplateType: '',
      statusOptions: [
        { value: '', text: '全部状态' },
        { value: 'waiting', text: '等待中' },
        { value: 'blocked', text: '被阻塞' },
        { value: 'running', text: '运行中' },
        { value: 'completed', text: '已完成' },
        { value: 'failed', text: '失败' },
        { value: 'canceled', text: '已取消' }
      ],
      templateTypeOptions: [
        { value: '', text: '全部类型' }
        // 其他模板类型将在created生命周期中从后端获取
      ]
    }
  },
  
  computed: {
    ...mapState({
      tasks: state => state.tasks.tasks,
      pagination: state => state.tasks.pagination,
      loading: state => state.loading,
      error: state => state.error
    }),
    ...mapGetters('templates', ['templateTypes'])
  },
  
  methods: {
    ...mapActions('tasks', [
      'fetchTasks',
      'setPage',
      'setFilters',
      'cancelTask'
    ]),
    ...mapActions('templates', ['fetchTemplates']),
    ...mapActions(['clearError']),
    
    // 格式化日期
    formatDate(dateStr) {
      return moment(dateStr).format('YYYY-MM-DD HH:mm:ss')
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
    
    // 查看任务详情
    viewTaskDetail(taskId) {
      this.$router.push(`/tasks/${taskId}`)
    },
    
    // 确认取消任务
    confirmCancel(task) {
      this.selectedTask = task
      this.$bvModal.show('cancel-modal')
    },
    
    // 执行取消任务
    async cancelTask() {
      if (!this.selectedTask) return
      
      try {
        await this.cancelTask(this.selectedTask.id)
        this.$bvToast.toast('任务已成功取消', {
          title: '操作成功',
          variant: 'success',
          solid: true
        })
      } catch (error) {
        // 错误已经在action中处理
      }
    },
    
    // 更改页码
    changePage(page) {
      this.currentPage = page
      this.setPage(page)
    },
    
    // 应用筛选条件
    applyFilters() {
      this.setFilters({
        status: this.filterStatus,
        name: this.filterName,
        template_type: this.filterTemplateType
      })
    },
    
    // 延迟搜索（防抖）
    debounceSearch() {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => {
        this.applyFilters()
      }, 500)
    },
    
    // 清空筛选条件
    clearFilters() {
      this.filterStatus = ''
      this.filterName = ''
      this.filterTemplateType = ''
      this.applyFilters()
    },
    
    // 初始化模板类型选项
    initTemplateTypeOptions() {
      if (this.templateTypes && this.templateTypes.length > 0) {
        // 从vuex中获取模板类型并创建选项
        this.templateTypeOptions = [
          { value: '', text: '全部类型' },
          ...this.templateTypes.map(type => ({ value: type, text: type }))
        ]
      }
    }
  },
  
  async created() {
    try {
      // 获取模板列表以填充模板类型选项
      await this.fetchTemplates()
      this.initTemplateTypeOptions()
      
      // 获取任务列表
      this.currentPage = this.pagination.page
      await this.fetchTasks()
    } catch (error) {
      console.error('初始化任务列表失败:', error)
    }
  },
  
  watch: {
    // 监听模板类型变化，更新下拉选项
    templateTypes: {
      handler: 'initTemplateTypeOptions',
      immediate: true
    }
  }
}
</script>

<style scoped>
.card-body {
  padding: 1.25rem;
}

.pagination {
  margin-bottom: 0;
}

/* 状态标签样式已在App.vue中定义 */
</style>
