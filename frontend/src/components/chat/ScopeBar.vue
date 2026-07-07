<template>
  <div class="scope-bar">
    <n-tag size="small" :type="selectedReadyFiles.length ? 'info' : 'warning'">
      检索范围：{{ label }}
    </n-tag>
    <span v-for="file in preview" :key="file.id" class="scope-file">{{ file.original_name }}</span>
    <span v-if="extraCount > 0" class="scope-extra">+{{ extraCount }}</span>
    <n-button text size="tiny" @click="$emit('open-knowledge')">选择资料</n-button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  readyFiles: { type: Array, default: () => [] },
  selectedFileIds: { type: Array, default: () => [] },
})
defineEmits(['open-knowledge'])

const selectedReadyFiles = computed(() =>
  props.readyFiles.filter((f) => props.selectedFileIds.includes(f.id))
)
const preview = computed(() => selectedReadyFiles.value.slice(0, 2))
const extraCount = computed(() => Math.max(0, selectedReadyFiles.value.length - preview.value.length))
const label = computed(() => {
  if (props.readyFiles.length === 0) return '暂无可用资料'
  if (selectedReadyFiles.value.length === 0) return '未选择资料'
  if (selectedReadyFiles.value.length === props.readyFiles.length) return `全部资料 (${props.readyFiles.length})`
  return `已选 ${selectedReadyFiles.value.length} 份`
})
</script>

<style scoped>
.scope-bar {
  display: flex; align-items: center; gap: 8px;
  min-height: 28px; margin-bottom: 8px;
  color: #725d42; font-size: 12px; overflow: hidden;
}
.scope-file { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.scope-extra { color: #9f927d; white-space: nowrap; }
</style>
