<template>
  <n-card v-if="toolResult" size="small" :title="toolResult.title">
    <div v-if="toolResult.type === 'summary'" class="tool-markdown" v-html="renderMarkdown(toolResult.content)" />
    <div v-else class="knowledge-list">
      <n-card v-for="point in toolResult.points" :key="point.title" size="small" hoverable
        class="knowledge-card" @click="$emit('ask', point)">
        <template #header>{{ point.title }}</template>
        {{ point.description }}
      </n-card>
    </div>
    <template #footer>
      <n-space>
        <n-button v-if="toolResult.type === 'summary'" size="small" @click="$emit('copy')">复制摘要</n-button>
        <template v-else>
          <n-button size="small" type="primary" ghost @click="$emit('download-markdown')">
            <n-icon><download-outline /></n-icon> 导出 Markdown
          </n-button>
          <n-text depth="3">点击知识点可直接追问</n-text>
        </template>
      </n-space>
    </template>
  </n-card>
</template>

<script setup>
import { DownloadOutline } from '@vicons/ionicons5'
import { md } from '../../utils/markdown'

defineProps({ toolResult: { type: Object, default: null } })
defineEmits(['copy', 'ask', 'download-markdown'])

function renderMarkdown(text) { return text ? md.render(text) : '' }
</script>

<style scoped>
.tool-markdown { max-height: 320px; overflow-y: auto; line-height: 1.7; }
.knowledge-list { display: flex; flex-direction: column; gap: 8px; max-height: 360px; overflow-y: auto; }
.knowledge-card { cursor: pointer; }
</style>
