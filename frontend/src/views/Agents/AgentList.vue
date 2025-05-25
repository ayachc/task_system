<template>
  <div class="agent-list-container">
    <h1 class="page-title">agent列表</h1>
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="4" animated />
    </div>
    
    <div v-else-if="agents.length === 0" class="empty-state">
      <i class="el-icon-warning-outline"></i>
      <p>没有找到agent</p>
    </div>
    
    <div v-else class="agent-grid">
      <agent-card 
        v-for="agent in mainAgents" 
        :key="agent.id" 
        :agent="agent"
        :sub-agents="getSubAgents(agent.id)"
      />
    </div>
  </div>
</template>

<script>
import { agentApi } from '@/services/api'
import AgentCard from './components/AgentCard.vue'

export default {
  name: 'AgentList',
  components: {
    AgentCard
  },
  data() {
    return {
      agents: [],
      loading: true,
      refreshInterval: null
    }
  },
  computed: {
    mainAgents() {
      return this.agents.filter(agent => agent.type === 'main')
    }
  },
  created() {
    this.fetchAgents()
    // Set up auto-refresh every 10 seconds
    this.refreshInterval = setInterval(() => {
      this.fetchAgents()
    }, 10000)
  },
  beforeDestroy() {
    // Clear the interval when component is destroyed
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },
  methods: {
    async fetchAgents() {
      try {
        this.loading = true
        const agents = await agentApi.getAgents()
        this.agents = agents
      } catch (error) {
        console.error('Failed to fetch agents:', error)
        this.$message.error('Failed to load agents')
      } finally {
        this.loading = false
      }
    },
    getSubAgents(mainAgentId) {
      return this.agents.filter(agent => 
        agent.type === 'sub' && agent.main_agent_id === mainAgentId
      )
    }
  }
}
</script>

<style scoped>
.agent-list-container {
  padding: 20px;
}

.page-title {
  margin-bottom: 24px;
  font-weight: 500;
  color: #303133;
}

.loading-container {
  margin: 40px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 60px 0;
  color: #909399;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

@media (max-width: 1200px) {
  .agent-grid {
    grid-template-columns: 1fr;
  }
}
</style>
