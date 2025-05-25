<template>
  <div class="resource-bar" :class="{ 'small': size === 'small' }">
    <div class="progress-container" :class="{ 'empty-progress': percentage === 0 }">
      <el-progress 
        :percentage="percentage" 
        :stroke-width="size === 'small' ? 10 : 14"
        :color="getColorByPercentage(percentage)"
        :show-text="false"
      />
    </div>
    <div v-if="showText" class="resource-text">
      <span class="info-value">{{ formatValue(used) }}</span> / <span class="info-value">{{ formatValue(total) }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ResourceBar',
  props: {
    used: {
      type: Number,
      required: true
    },
    total: {
      type: Number,
      required: true,
      validator: value => value > 0
    },
    showText: {
      type: Boolean,
      default: true
    },
    format: {
      type: String,
      default: 'percentage',
      validator: value => ['percentage', 'bytes'].includes(value)
    },
    size: {
      type: String,
      default: 'normal',
      validator: value => ['small', 'normal'].includes(value)
    }
  },
  computed: {
    percentage() {
      return Math.min(Math.round((this.used / this.total) * 100), 100)
    }
  },
  methods: {
    getColorByPercentage(percentage) {
      if (percentage < 60) return '#67c23a'
      if (percentage < 80) return '#e6a23c'
      return '#f56c6c'
    },
    formatValue(value) {
      if (this.format === 'percentage') {
        return `${value}%`
      } else if (this.format === 'bytes') {
        return this.formatBytes(value)
      }
      return value
    },
    formatBytes(bytes) {
      if (bytes === 0) return '0 B'
      
      const units = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      
      // Don't go beyond TB
      const idx = Math.min(i, units.length - 1)
      
      return `${(bytes / Math.pow(1024, idx)).toFixed(2)} ${units[idx]}`
    }
  }
}
</script>

<style scoped>
.resource-bar {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 16px;
}

.resource-bar.small {
  gap: 4px;
}

.progress-container {
  position: relative;
}

.empty-progress {
  border: 1px solid #dcdfe6;
  border-radius: 100px;
}

.resource-text {
  display: flex;
  justify-content: flex-end;
  font-size: 14px;
  color: #606266;
}

.resource-bar.small .resource-text {
  font-size: 13px;
}

.info-value {
  display: inline-block;
  background-color: #f0f2f5;
  border-radius: 4px;
  padding: 0 6px;
  font-weight: 500;
}
</style>
