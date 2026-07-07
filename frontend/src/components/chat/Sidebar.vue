<template>
  <aside class="sidebar">
    <div class="sidebar-header" @click="$emit('new-chat')">
      <Title size="small" color="app-teal">📚 EduAssistant</Title>
    </div>

    <div class="sidebar-actions">
      <n-button type="primary" ghost class="new-chat-btn" @click="$emit('new-chat')">
        <n-icon><add-outline /></n-icon> 新对话
      </n-button>
    </div>

    <div class="conv-list">
      <ConversationItem
        v-for="conv in conversations"
        :key="conv.id"
        :title="conv.title"
        :active="conv.id === currentConvId"
        @select="$emit('select-conversation', conv)"
        @delete="$emit('delete-conversation', conv.id)"
      />
      <n-empty v-if="conversations.length === 0" description="暂无对话" style="margin-top: 40px" />
    </div>

    <div class="sidebar-footer">
      <n-button text @click="$emit('logout')">
        <n-icon><log-out-outline /></n-icon> 退出
      </n-button>
    </div>
  </aside>
</template>

<script setup>
import { Title } from 'animal-island-vue'
import { AddOutline, LogOutOutline } from '@vicons/ionicons5'
import ConversationItem from './ConversationItem.vue'

defineProps({
  conversations: { type: Array, default: () => [] },
  currentConvId: { type: [Number, String], default: null },
})
defineEmits(['new-chat', 'select-conversation', 'delete-conversation', 'logout'])
</script>

<style scoped>
.sidebar {
  width: 280px;
  min-width: 280px;
  background: #f8f8f0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e8e2d6;
}

.sidebar-header {
  padding: 24px 18px 20px;
  cursor: pointer;
}

.sidebar-actions { padding: 0 18px 16px; }

.new-chat-btn {
  width: 100%;
  height: 42px;
  border-radius: 24px;
  font-size: 16px;
  justify-content: center;
}

.conv-list { flex: 1; overflow-y: auto; padding: 2px 12px 12px; }

.sidebar-footer {
  padding: 14px 18px;
  border-top: 1px solid #e8e2d6;
  background: #f8f8f0;
}
</style>
