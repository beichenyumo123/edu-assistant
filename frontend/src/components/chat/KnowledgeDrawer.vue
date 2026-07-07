<template>
  <n-drawer v-model:show="showModel" :width="400" placement="right">
    <n-drawer-content title="📁 我的知识库">
      <n-upload multiple :max="5" accept=".pdf,.docx,.txt,.md"
        :custom-request="(opts) => $emit('upload', opts)" :disabled="uploading">
        <n-button :loading="uploading">
          <n-icon><cloud-upload-outline /></n-icon> 上传文件
        </n-button>
      </n-upload>
      <n-divider />
      <div v-if="files.length === 0">
        <n-empty description="还没有上传过文件" />
      </div>
      <template v-else>
        <div class="file-select-toolbar">
          <n-text depth="3">已选 {{ selectedReadyFiles.length }} / {{ readyFiles.length }}</n-text>
          <n-space size="small">
            <n-button size="tiny" text @click="$emit('select-all')">全选</n-button>
            <n-button size="tiny" text @click="$emit('clear-selection')">清空</n-button>
          </n-space>
        </div>
      </template>
      <n-list v-if="files.length > 0">
        <n-list-item v-for="f in files" :key="f.id">
          <template #prefix>
            <div class="file-prefix">
              <n-checkbox :checked="isFileSelected(f.id)" :disabled="f.status !== 'ready'"
                @update:checked="(checked) => $emit('toggle-file', f.id, checked)" />
              <n-tag :type="statusType(f.status)" size="small">{{ statusText(f.status) }}</n-tag>
            </div>
          </template>
          <n-thing :title="f.original_name" :description="`${formatSize(f.file_size)} · ${f.chunk_count}块 · ${f.created_at?.substring(0, 10)}`" />
          <template #suffix>
            <n-space vertical size="small">
              <n-button size="tiny" ghost type="primary"
                :loading="toolLoading === `summary-${f.id}`" @click="$emit('summarize', f)">摘要</n-button>
              <n-button size="tiny" ghost type="info"
                :loading="toolLoading === `knowledge-${f.id}`" @click="$emit('extract-knowledge', f)">知识点</n-button>
              <n-button text type="error" @click="$emit('delete-file', f.id)">
                <n-icon><trash-outline /></n-icon>
              </n-button>
            </n-space>
          </template>
        </n-list-item>
      </n-list>
      <n-divider />
      <KnowledgeResultCard
        :tool-result="toolResult"
        @copy="$emit('copy-result')"
        @ask="$emit('ask-knowledge', $event)"
        @download-markdown="$emit('download-markdown')"
      />
    </n-drawer-content>
  </n-drawer>
</template>

<script setup>
import { computed } from 'vue'
import { CloudUploadOutline, TrashOutline } from '@vicons/ionicons5'
import KnowledgeResultCard from './KnowledgeResultCard.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  files: { type: Array, default: () => [] },
  readyFiles: { type: Array, default: () => [] },
  selectedReadyFiles: { type: Array, default: () => [] },
  uploading: { type: Boolean, default: false },
  toolLoading: { type: String, default: '' },
  toolResult: { type: Object, default: null },
  isFileSelected: { type: Function, default: () => false },
})

const emit = defineEmits([
  'update:open',
  'upload', 'select-all', 'clear-selection', 'toggle-file',
  'summarize', 'extract-knowledge', 'delete-file',
  'copy-result', 'ask-knowledge', 'download-markdown',
])

const showModel = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val),
})

function statusType(status) {
  return status === 'ready' ? 'success' : status === 'error' ? 'error' : 'warning'
}

function statusText(status) {
  return status === 'ready' ? '已就绪' : status === 'error' ? '失败' : '处理中'
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}
</script>

<style scoped>
.file-select-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.file-prefix { display: flex; align-items: center; gap: 8px; }
</style>
