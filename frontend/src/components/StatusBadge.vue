<template>
  <b-badge :class="badgeClass">{{ statusText }}</b-badge>
</template>

<script>
export default {
  name: 'StatusBadge',
  props: {
    status: {
      type: String,
      required: true
    }
  },
  computed: {
    badgeClass() {
      return `status-${this.status}`
    },
    statusText() {
      const statusMap = {
        'waiting': '等待中',
        'blocked': '被阻塞',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'canceled': '已取消'
      }
      return statusMap[this.status] || this.status
    }
  }
}
</script>

<style scoped>
/* 状态样式已在App.vue中全局定义 */
</style>
