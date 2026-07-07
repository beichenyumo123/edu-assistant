<template>
  <div class="conv-item" :class="{ active }" @click="$emit('select')">
    <n-icon size="16"><chatbubbles-outline /></n-icon>
    <span class="conv-title">{{ title }}</span>
    <n-popconfirm @positive-click="$emit('delete')">
      <template #trigger>
        <n-button text size="tiny" class="delete-btn" @click.stop>
          <n-icon><trash-outline /></n-icon>
        </n-button>
      </template>
      确定删除此对话？
    </n-popconfirm>
  </div>
</template>

<script setup>
import { ChatbubblesOutline, TrashOutline } from '@vicons/ionicons5'

defineProps({ title: { type: String, default: '' }, active: { type: Boolean, default: false } })
defineEmits(['select', 'delete'])
</script>

<style scoped>
.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 9px 12px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 15px;
  margin-bottom: 8px;
  color: #725d42;
  transition: background 0.15s, color 0.15s;
}

.conv-item:hover { background: rgba(25, 200, 185, 0.08); }
.conv-item.active { background: #e6f9f6; color: #19c8b9; }

.conv-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.delete-btn { opacity: 0; }
.conv-item:hover .delete-btn { opacity: 1; }
</style>
