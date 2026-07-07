<template>
  <div class="msg-content" v-html="renderedContent" />
</template>

<script setup>
import { computed } from 'vue'
import { md } from '../../utils/markdown'

const props = defineProps({
  content: { type: String, default: '' },
  role: { type: String, default: 'user' },
})

const renderedContent = computed(() => {
  if (!props.content) return ''
  if (props.role === 'assistant') return md.render(props.content)
  return props.content.replace(/\n/g, '<br>')
})
</script>

<style scoped>
.msg-content {
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(h1), :deep(h2), :deep(h3) {
  margin: 8px 0 4px;
  color: #794f27;
}

:deep(a) { color: #19c8b9; }

:deep(code) {
  background: #f0e8d8;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #794f27;
}

:deep(pre) {
  background: #2b2118;
  color: #e8d5bc;
  padding: 14px;
  border-radius: 12px;
  overflow-x: auto;
}

:deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}

:deep(blockquote) {
  border-left: 3px solid #19c8b9;
  padding-left: 12px;
  color: #9f927d;
  margin: 8px 0;
}

:deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
}

:deep(th), :deep(td) {
  border: 1px solid #e8e2d6;
  padding: 6px 10px;
  text-align: left;
}

:deep(th) {
  background: #f7f3df;
  color: #794f27;
  font-weight: 700;
}
</style>
