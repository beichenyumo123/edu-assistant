<template>
  <header class="chat-header">
    <n-radio-group :value="agentType" @update:value="$emit('switch-agent', $event)" size="large">
      <n-radio-button value="edu" label="📖 教育助手">
        <span>📖 教育助手</span>
      </n-radio-button>
      <n-radio-button value="baoyan" label="🎓 保研助手">
        <span>🎓 保研助手</span>
      </n-radio-button>
    </n-radio-group>
    <n-button text @click="$emit('open-knowledge')">
      <n-icon size="20"><folder-open-outline /></n-icon>
      知识库
    </n-button>
  </header>
</template>

<script setup>
import { FolderOpenOutline } from '@vicons/ionicons5'

defineProps({ agentType: { type: String, default: 'edu' } })
defineEmits(['switch-agent', 'open-knowledge'])
</script>

<style scoped>
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e8e2d6;
  background: #f7f3df;
}
</style>
