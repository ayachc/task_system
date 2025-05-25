<template>
  <div id="app">
    <div class="container-fluid">
      <div class="row">
        <!-- 侧边栏导航 -->
        <nav id="sidebar" class="col-md-3 col-lg-2 d-md-block bg-light sidebar">
          <div class="sidebar-sticky pt-3">
            <h5 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
              <span>脚本执行任务管理系统</span>
            </h5>
            <ul class="nav flex-column">
              <li class="nav-item">
                <router-link to="/tasks" class="nav-link" active-class="active">
                  <i class="bi bi-list-task mr-2"></i>
                  任务管理
                </router-link>
              </li>
              <li class="nav-item">
                <router-link to="/agents" class="nav-link" active-class="active">
                  <i class="bi bi-pc-display mr-2"></i>
                  Agent管理
                </router-link>
              </li>
              <li class="nav-item">
                <router-link to="/templates" class="nav-link" active-class="active">
                  <i class="bi bi-file-earmark-code mr-2"></i>
                  脚本模板
                </router-link>
              </li>
            </ul>
            
            <div class="mt-5 px-3 text-muted small">
              <div>版本: 0.1.0</div>
              <div class="mt-2">2025 脚本执行任务管理系统</div>
            </div>
          </div>
        </nav>
        
        <!-- 主内容区域 -->
        <main role="main" class="col-md-9 ml-sm-auto col-lg-10 px-md-4">
          <!-- 页面标题区域 -->
          <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
            <h1 class="h2">{{ currentPageTitle }}</h1>
            <div class="btn-toolbar mb-2 mb-md-0">
              <div v-if="$route.path === '/tasks'">
                <router-link to="/tasks/new" class="btn btn-sm btn-primary">
                  <i class="bi bi-plus"></i> 新建任务
                </router-link>
              </div>
              <div v-if="$route.path === '/templates'">
                <b-button class="btn btn-sm btn-primary" @click="$root.$emit('show-create-template-modal')">
                  <i class="bi bi-plus"></i> 新建模板
                </b-button>
              </div>
            </div>
          </div>
          
          <!-- 路由视图 -->
          <router-view/>
        </main>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    currentPageTitle() {
      const path = this.$route.path
      if (path.startsWith('/tasks')) {
        if (path === '/tasks/new') return '新建任务'
        return '任务管理'
      } else if (path.startsWith('/agents')) {
        return 'Agent管理'
      } else if (path.startsWith('/templates')) {
        if (path === '/templates/new') return '新建模板'
        return '脚本模板'
      }
      return '首页'
    }
  }
}
</script>

<style>
/* 导入Bootstrap图标 */
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css");

body {
  font-size: 1rem;
}

.sidebar {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 100;
  padding: 48px 0 0;
  box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
}

.sidebar-sticky {
  position: relative;
  top: 0;
  height: calc(100vh - 48px);
  padding-top: .5rem;
  overflow-x: hidden;
  overflow-y: auto;
}

.sidebar .nav-link {
  font-weight: 500;
  color: #333;
}

.sidebar .nav-link.active {
  color: #007bff;
}

/* 主内容区域样式 */
main {
  padding-top: 1.5rem;
}

/* 为不同状态的任务设置颜色 */
.status-blocked {
  background-color: #6c757d !important;
  color: white;
}
.status-waiting {
  background-color: #17a2b8 !important;
  color: white;
}
.status-running {
  background-color: #28a745 !important;
  color: white;
}
.status-completed {
  background-color: #007bff !important;
  color: white;
}
.status-failed {
  background-color: #dc3545 !important;
  color: white;
}
.status-canceled {
  background-color: #ffc107 !important;
  color: black;
}
</style>
