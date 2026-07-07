<template>
  <div v-if="sources.length > 0" class="msg-sources">
    <n-collapse>
      <n-collapse-item title="📎 参考来源">
        <div v-for="(s, si) in sources" :key="si" class="source-item">
          📄 {{ s.document_name || ('文档' + s.document_id) }} · 块{{ s.chunk_index }}
          <span v-if="s.evidence_id"> · {{ s.evidence_id }}</span>
          <span v-if="s.source_type"> · 类型: {{ s.source_type }}</span>
          <span v-if="s.trust_level"> · 可信度: {{ s.trust_level }}</span>
          <span v-if="s.retrieval_score !== undefined"> · 距离: {{ Number(s.retrieval_score).toFixed(4) }}</span>
          : {{ s.text?.substring(0, 150) }}...
        </div>
      </n-collapse-item>
    </n-collapse>
  </div>
</template>

<script setup>
defineProps({
  sources: { type: Array, default: () => [] },
})
</script>

<style scoped>
.msg-sources { margin-top: 8px; font-size: 12px; }
.source-item { padding: 4px 0; color: #9f927d; font-size: 12px; }
</style>
