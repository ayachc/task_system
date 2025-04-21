<template>
  <b-alert 
    :show="!!error" 
    dismissible 
    fade
    :variant="variant"
    @dismissed="onDismiss"
  >
    <h5 v-if="title">
      <i class="bi bi-exclamation-triangle-fill mr-2"></i>
      {{ title }}
    </h5>
    <div v-if="typeof error === 'string'">{{ error }}</div>
    <div v-else-if="error && error.message">{{ error.message }}</div>
    <div v-else>发生未知错误</div>
  </b-alert>
</template>

<script>
export default {
  name: 'ErrorAlert',
  props: {
    error: {
      type: [String, Object],
      default: null
    },
    title: {
      type: String,
      default: '错误'
    },
    variant: {
      type: String,
      default: 'danger'
    }
  },
  methods: {
    onDismiss() {
      this.$emit('dismissed')
    }
  }
}
</script>
