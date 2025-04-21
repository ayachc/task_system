<template>
  <div class="loading-container" :class="{ 'overlay': overlay }">
    <div class="spinner-container">
      <b-spinner :variant="variant" :small="small"></b-spinner>
      <span v-if="text" class="ml-2">{{ text }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoadingSpinner',
  props: {
    overlay: {
      type: Boolean,
      default: false
    },
    text: {
      type: String,
      default: '加载中...'
    },
    variant: {
      type: String,
      default: 'primary'
    },
    small: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
}

.loading-container.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  z-index: 1000;
}

.spinner-container {
  display: flex;
  align-items: center;
}
</style>
