<template>
  <div class="agent-card" :class="{'offline': agent.status === 'offline'}">
    <div class="agent-header">
      <div class="agent-title">
        <h3>{{ agent.name }}</h3>
        <el-tag size="small" :type="getStatusType(agent.status)">{{ getStatusText(agent.status) }}</el-tag>
      </div>
      <div class="agent-meta">
        <span class="agent-id">ID: <span class="info-value">{{ agent.id }}</span></span>
        <span class="agent-type">类型: <span class="info-value">{{ agent.type === 'main' ? '主agent' : '子agent' }}</span></span>
      </div>
    </div>
    
    <div class="agent-time-info">
      <div class="time-item">
        <i class="el-icon-time"></i>
        <span>创建时间: <span class="info-value">{{ formatDateTime(agent.created_time) }}</span></span>
      </div>
      <div class="time-item">
        <i class="el-icon-refresh"></i>
        <span>最近心跳: <span class="info-value">{{ formatDateTime(agent.last_heartbeat_time) }}</span></span>
      </div>
    </div>
    
    <div class="resource-section">
      <div class="resource-item">
        <div class="resource-title">CPU</div>
        <div class="resource-content">
          <span class="cores"><span class="info-value">{{ agent.cpu_cores || 0 }}</span> 核心</span>
          <span class="usage"><span class="info-value">{{ Math.round(agent.cpu_usage || 0) }}%</span></span>
        </div>
      </div>
      
      <div class="resource-item">
        <div class="resource-title">内存</div>
        <resource-bar 
          :used="agent.memory_used || 0"
          :total="agent.memory_total || 1"
          :show-text="true"
          format="bytes"
        />
      </div>
    </div>
    
    <div class="gpu-section" v-if="parsedGpuInfo && parsedGpuInfo.length > 0">
      <h4>GPU 资源</h4>
      <div class="gpu-grid">
        <gpu-card 
          v-for="(gpu, index) in parsedGpuInfo" 
          :key="index" 
          :gpu="gpu" 
        />
      </div>
    </div>
    
    <div class="sub-agents-section">
      <h4>子agent {{ subAgents && subAgents.length > 0 ? `(${subAgents.length})` : '' }}</h4>
      <div v-if="subAgents && subAgents.length > 0" class="sub-agents-grid">
        <sub-agent-card 
          v-for="subAgent in subAgents" 
          :key="subAgent.id" 
          :agent="subAgent" 
        />
      </div>
      <div v-else class="no-sub-agents">
        <i class="el-icon-info"></i>
        <p>暂无子agent</p>
      </div>
    </div>
  </div>
</template>

<script>
// Custom date formatter used instead of date-fns
import ResourceBar from './ResourceBar.vue'
import GpuCard from './GpuCard.vue'
import SubAgentCard from './SubAgentCard.vue'

export default {
  name: 'AgentCard',
  components: {
    ResourceBar,
    GpuCard,
    SubAgentCard
  },
  props: {
    agent: {
      type: Object,
      required: true
    },
    subAgents: {
      type: Array,
      default: () => []
    }
  },
  computed: {
    parsedGpuInfo() {
      try {
        // Check if gpu_info is already an array
        if (Array.isArray(this.agent.gpu_info)) {
          return this.agent.gpu_info;
        }
        // If it's a string, try to parse it as JSON
        if (typeof this.agent.gpu_info === 'string' && this.agent.gpu_info.trim()) {
          return JSON.parse(this.agent.gpu_info);
        }
        // Return empty array if not valid
        return [];
      } catch (e) {
        console.error('Error parsing GPU info:', e);
        return [];
      }
    }
  },
  methods: {
    formatDateTime(dateTime) {
      if (!dateTime) return 'N/A'
      
      try {
        const date = new Date(dateTime)
        const now = new Date()
        const diffMs = now - date
        const diffSec = Math.floor(diffMs / 1000)
        const diffMin = Math.floor(diffSec / 60)
        const diffHour = Math.floor(diffMin / 60)
        const diffDay = Math.floor(diffHour / 24)

        if (diffSec < 60) return '刚刚'
        if (diffMin < 60) return `${diffMin} 分钟前`
        if (diffHour < 24) return `${diffHour} 小时前`
        if (diffDay < 30) return `${diffDay} 天前`

        // Format as YYYY-MM-DD if older
        return date.toISOString().split('T')[0]
      } catch (e) {
        return 'Invalid date'
      }
    },
    getStatusType(status) {
      const statusMap = {
        'online': 'success',
        'offline': 'info',
        'end': 'danger'
      }
      return statusMap[status] || 'info'
    },
    getStatusText(status) {
      const statusMap = {
        'online': '在线',
        'offline': '离线',
        'end': '已结束'
      }
      return statusMap[status] || status
    }
  }
}
</script>

<style scoped>
.agent-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  transition: all 0.3s ease;
  font-size: 16px;
}

.info-value {
  display: inline-block;
  background-color: #f0f2f5;
  border-radius: 4px;
  padding: 2px 8px;
  font-weight: 500;
}

.agent-card.offline {
  opacity: 0.7;
}

.agent-header {
  margin-bottom: 16px;
}

.agent-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.agent-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.agent-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #606266;
}

.agent-time-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  font-size: 13px;
  color: #606266;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.resource-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.resource-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.resource-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.gpu-section, .sub-agents-section {
  margin-top: 24px;
}

.gpu-section h4, .sub-agents-section h4 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.gpu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.sub-agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.no-sub-agents {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  background-color: #f5f7fa;
  border-radius: 6px;
  color: #909399;
}

.no-sub-agents i {
  font-size: 24px;
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .agent-time-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .gpu-grid, .sub-agents-grid {
    grid-template-columns: 1fr;
  }
}
</style>
