<template>
  <div class="template-list">
    <h3 class="mb-4">脚本模板管理</h3>
    
    <!-- 操作栏 -->
    <div class="d-flex justify-content-between mb-3">
      <b-form-input
        v-model="searchKeyword"
        placeholder="搜索模板名称"
        class="w-25 mr-2"
        @input="handleSearch"
      ></b-form-input>
      
      <b-button 
        variant="primary" 
        @click="showCreateModal"
      >
        <b-icon icon="plus"></b-icon> 新建模板
      </b-button>
    </div>
    
    <!-- 加载中提示 -->
    <div v-if="loading" class="text-center py-5">
      <b-spinner variant="primary" label="加载中..."></b-spinner>
      <p class="mt-2">加载模板数据...</p>
    </div>
    
    <!-- 错误提示 -->
    <b-alert v-if="error" show variant="danger" dismissible>
      {{ error }}
    </b-alert>
    
    <!-- 无数据提示 -->
    <b-alert v-if="!loading && templates.length === 0" show variant="info">
      暂无脚本模板。点击"新建模板"按钮创建第一个脚本模板。
    </b-alert>
    
    <!-- 模板列表 -->
    <div v-else>
      <b-card-group columns>
        <b-card
          v-for="template in templates"
          :key="template.id"
          class="mb-3 template-card"
          no-body
        >
          <b-card-header class="d-flex justify-content-between align-items-center py-2">
            <h5 class="mb-0">{{ template.name }}</h5>
            <div>
              <b-button 
                variant="outline-primary" 
                size="sm"
                @click="showEditModal(template)"
                class="mr-1"
              >
                <b-icon icon="pencil"></b-icon>
              </b-button>
              <b-button 
                variant="outline-danger" 
                size="sm"
                @click="confirmDelete(template.id)"
              >
                <b-icon icon="trash"></b-icon>
              </b-button>
            </div>
          </b-card-header>
          
          <b-card-body>
            <div class="script-content">
              <pre><code>{{ template.content }}</code></pre>
            </div>
            <div class="text-muted mt-2">
              <small>
                <b-icon icon="clock-history"></b-icon>
                创建时间: {{ formatDate(template.created_time) }}
              </small>
              <small v-if="template.updated_time" class="ml-2">
                <b-icon icon="pencil"></b-icon>
                更新时间: {{ formatDate(template.updated_time) }}
              </small>
            </div>
          </b-card-body>
        </b-card>
      </b-card-group>
    </div>
    
    <!-- 创建/编辑模板弹窗 -->
    <b-modal
      v-model="showModal"
      :title="isEditing ? '编辑模板' : '创建模板'"
      size="lg"
      @hidden="resetForm"
      @ok="handleSubmit"
      ok-title="保存"
      cancel-title="取消"
    >
      <b-form>
        <b-form-group
          label="模板名称"
          label-for="template-name"
          :state="nameState"
          :invalid-feedback="nameInvalidFeedback"
        >
          <b-form-input
            id="template-name"
            v-model="form.name"
            required
            placeholder="请输入模板名称"
            :state="nameState"
          ></b-form-input>
        </b-form-group>
        
        <b-form-group
          label="脚本内容"
          label-for="script-content"
          :state="contentState"
          :invalid-feedback="contentInvalidFeedback"
        >
          <b-form-textarea
            id="script-content"
            v-model="form.content"
            rows="12"
            no-resize
            required
            placeholder="#!/bin/bash"
            class="code-textarea"
            :state="contentState"
          ></b-form-textarea>
        </b-form-group>
      </b-form>
    </b-modal>
    
    <!-- 删除确认弹窗 -->
    <b-modal
      id="delete-confirm-modal"
      title="确认删除"
      ok-variant="danger"
      ok-title="删除"
      cancel-title="取消"
      @ok="handleDelete"
    >
      <p>确定要删除该模板吗？此操作不可恢复。</p>
    </b-modal>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import moment from 'moment'

export default {
  name: 'TemplateList',
  
  data() {
    return {
      searchKeyword: '',
      showModal: false,
      isEditing: false,
      validated: false,
      deleteTemplateId: null,
      form: {
        id: null,
        name: '',
        content: ''
      }
    }
  },
  
  computed: {
    ...mapState('templates', ['loading', 'error']),
    ...mapGetters('templates', ['allTemplates']),
    
    templates() {
      let result = this.allTemplates
      
      // 如果有搜索关键词，进行过滤
      if (this.searchKeyword) {
        const keyword = this.searchKeyword.toLowerCase()
        result = result.filter(template => 
          template.name.toLowerCase().includes(keyword) || 
          template.content.toLowerCase().includes(keyword)
        )
      }
      
      return result
    },
    
    // 表单验证状态
    nameState() {
      if (!this.validated) return null
      return this.form.name.trim().length > 0
    },
    
    contentState() {
      if (!this.validated) return null
      return this.form.content.trim().length > 0
    },
    
    nameInvalidFeedback() {
      return '请输入模板名称'
    },
    
    contentInvalidFeedback() {
      return '请输入脚本内容'
    }
  },
  
  methods: {
    ...mapActions('templates', [
      'fetchTemplates',
      'createTemplate',
      'updateTemplate',
      'deleteTemplate'
    ]),
    
    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return ''
      return moment(dateString).format('YYYY-MM-DD HH:mm:ss')
    },
    
    // 处理搜索
    handleSearch() {
      // 本地搜索，无需调用API
    },
    
    // 显示创建模板弹窗
    showCreateModal() {
      this.isEditing = false
      this.form = {
        id: null,
        name: '',
        content: '#!/bin/bash\n\n'
      }
      this.showModal = true
    },
    
    // 显示编辑模板弹窗
    showEditModal(template) {
      this.isEditing = true
      this.form = {
        id: template.id,
        name: template.name,
        content: template.content
      }
      this.showModal = true
    },
    
    // 重置表单
    resetForm() {
      this.form = {
        id: null,
        name: '',
        content: ''
      }
      this.validated = false
    },
    
    // 确认删除
    confirmDelete(templateId) {
      this.deleteTemplateId = templateId
      this.$bvModal.show('delete-confirm-modal')
    },
    
    // 处理表单提交
    async handleSubmit(event) {
      event.preventDefault()
      this.validated = true
      
      // 表单验证
      if (!this.nameState || !this.contentState) {
        return
      }
      
      try {
        if (this.isEditing) {
          // 更新模板
          await this.updateTemplate({
            templateId: this.form.id,
            templateData: {
              name: this.form.name,
              content: this.form.content
            }
          })
          
          this.$bvToast.toast('模板更新成功', {
            title: '成功',
            variant: 'success',
            solid: true
          })
        } else {
          // 创建模板
          await this.createTemplate({
            name: this.form.name,
            content: this.form.content
          })
          
          this.$bvToast.toast('模板创建成功', {
            title: '成功',
            variant: 'success',
            solid: true
          })
        }
        
        // 关闭弹窗
        this.showModal = false
        
      } catch (error) {
        this.$bvToast.toast(error.message || '操作失败，请重试', {
          title: '错误',
          variant: 'danger',
          solid: true
        })
      }
    },
    
    // 删除模板
    async handleDelete() {
      if (!this.deleteTemplateId) return
      
      try {
        await this.deleteTemplate(this.deleteTemplateId)
        
        this.$bvToast.toast('模板删除成功', {
          title: '成功',
          variant: 'success',
          solid: true
        })
        
        this.deleteTemplateId = null
      } catch (error) {
        this.$bvToast.toast(error.message || '删除失败，请重试', {
          title: '错误',
          variant: 'danger',
          solid: true
        })
      }
    }
  },
  
  async created() {
    // 监听创建模板事件
    this.$root.$on('show-create-template-modal', this.showCreateModal);
    
    try {
      await this.fetchTemplates()
    } catch (error) {
      console.error('获取模板列表失败:', error)
    }
  },
  
  beforeDestroy() {
    // 移除事件监听
    this.$root.$off('show-create-template-modal', this.showCreateModal);
  }
}
</script>

<style scoped>
.template-card {
  transition: all 0.2s;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.script-content {
  max-height: 200px;
  overflow-y: auto;
  background-color: #f8f9fa;
  border-radius: 4px;
  padding: 10px;
}

.script-content pre {
  margin: 0;
  white-space: pre-wrap;
}

.code-textarea {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9rem;
}
</style>
