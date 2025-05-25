<template>
  <div class="sub-agent-card" :class="{'offline': agent.status === 'offline'}">
    <div class="sub-agent-header">
      <div class="sub-agent-title">
        <h4>{{ agent.name }}</h4>
        <el-tag size="mini" :type="getStatusType(agent.status)">{{ getStatusText(agent.status) }}</el-tag>
      </div>
      <div class="sub-agent-meta">
        <span class="sub-agent-id">ID: <span class="info-value">{{ truncateId(agent.id) }}</span></span>
        <span v-if="agent.task_id" class="task-id">任务: <span class="info-value">{{ truncateId(agent.task_id) }}</span></span>
      </div>
    </div>
    
    <div class="sub-agent-time-info">
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
        <div class="resource-content cpu-info">
          <span class="cores"><span class="info-value">{{ agent.cpu_cores || 0 }}</span> 核心</span>
          <span class="usage"><span class="info-value">{{ Math.round(agent.cpu_usage || 0) }}%</span></span>
        </div>
      </div>
      
      <div class="resource-item">
        <resource-bar 
          :used="agent.memory_used || 0"
          :total="agent.memory_total || 1"
          :show-text="true"
          format="bytes"
          size="small"
        />
      </div>
    </div>
    
    <div class="gpu-section" v-if="parsedGpuInfo && parsedGpuInfo.length > 0">
      <div class="gpu-grid">
        <gpu-card 
          v-for="(gpu, index) in parsedGpuInfo" 
          :key="index" 
          :gpu="gpu"
          size="small"
        />
      </div>
    </div>
  </div>
</template>

<script>
// Custom date formatter used instead of date-fns
import ResourceBar from './ResourceBar.vue'
import GpuCard from './GpuCard.vue'

export default {
  name: 'SubAgentCard',
  components: {
    ResourceBar,
    GpuCard
  },
  props: {
    agent: {
      type: Object,
      required: true
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
    truncateId(id) {
      if (!id) return 'N/A'
      return id.length > 8 ? id.substring(0, 8) + '...' : id
    },
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
.sub-agent-card {
  background-color: #f5f7fa;
  border-radius: 6px;
  padding: 14px;
  transition: all 0.3s ease;
  font-size: 16px;
}

.info-value {
  display: inline-block;
  background-color: #ebeef5;
  border-radius: 4px;
  padding: 2px 6px;
  font-weight: 500;
}

.sub-agent-card.offline {
  opacity: 0.7;
}

.sub-agent-header {
  margin-bottom: 12px;
}

.sub-agent-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.sub-agent-title h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 500;
}

.sub-agent-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #606266;
}

.sub-agent-time-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #606266;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.resource-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.resource-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cpu-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.gpu-section {
  margin-top: 12px;
}

.gpu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}
</style>
