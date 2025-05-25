<template>
  <div class="gpu-card" :class="{ 'small': size === 'small' }">
    <div class="gpu-header">
      <div class="gpu-title">
        <h5>GPU <span class="info-value">{{ gpu.gpu_id }}</span></h5>
        <el-tag size="mini" :type="gpu.is_available ? 'success' : 'danger'">
          {{ gpu.is_available ? '可用' : '使用中' }}
        </el-tag>
      </div>
    </div>
    
    <div class="gpu-usage">
      <span class="usage-label">使用率:</span>
      <span class="usage-value"><span class="info-value">{{ Math.round(gpu.usage || 0) }}%</span></span>
    </div>
    
    <div class="memory-section">
      <resource-bar 
        :used="gpu.memory_used || 0"
        :total="gpu.memory_total || 1"
        :show-text="true"
        format="bytes"
        :size="size"
      />
    </div>
  </div>
</template>

<script>
import ResourceBar from './ResourceBar.vue'

export default {
  name: 'GpuCard',
  components: {
    ResourceBar
  },
  props: {
    gpu: {
      type: Object,
      required: true
    },
    size: {
      type: String,
      default: 'normal',
      validator: value => ['small', 'normal'].includes(value)
    }
  }
}
</script>

<style scoped>
.gpu-card {
  background-color: #f0f2f5;
  border-radius: 6px;
  padding: 12px;
  transition: all 0.3s ease;
  font-size: 16px;
}

.info-value {
  display: inline-block;
  background-color: #e4e7ed;
  border-radius: 4px;
  padding: 2px 6px;
  font-weight: 500;
}

.gpu-card.small {
  padding: 8px;
}

.gpu-header {
  margin-bottom: 10px;
}

.gpu-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.gpu-title h5 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.gpu-card.small .gpu-title h5 {
  font-size: 13px;
}

.gpu-usage {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
}

.gpu-card.small .gpu-usage {
  font-size: 12px;
  margin-bottom: 6px;
}

.usage-label {
  color: #606266;
}

.usage-value {
  font-weight: 500;
}

.memory-section {
  margin-top: 6px;
}
</style>
