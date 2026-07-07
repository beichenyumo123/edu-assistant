<template>
  <div v-if="evaluation" class="msg-evaluation">
    <n-collapse>
      <n-collapse-item title="RAG 评价指标">
        <div class="metric-grid">
          <div v-for="item in summary" :key="item.label" class="metric-item">
            <span class="metric-label">{{ item.label }}</span>
            <strong :class="item.className">{{ item.value }}</strong>
          </div>
        </div>
        <div class="metric-detail">
          <span>检索块: {{ evaluation.retrieval?.retrieved_chunks ?? 0 }}</span>
          <span>命中: {{ evaluation.retrieval?.retrieval_hit ? '是' : '否' }}</span>
          <span>关键结论: {{ evaluation.generation?.supported_claim_count ?? 0 }}/{{ evaluation.generation?.claim_count ?? 0 }}</span>
          <span>无效引用: {{ evaluation.generation?.invalid_citation_count ?? 0 }}</span>
        </div>
        <div v-if="evaluation.notes?.length" class="metric-notes">
          <div v-for="(note, ni) in evaluation.notes" :key="ni">{{ note }}</div>
        </div>
      </n-collapse-item>
    </n-collapse>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { normalizeEvaluation, getEvaluationSummary } from '../../composables/useEvaluation'

const props = defineProps({
  evaluation: { type: [Object, String], default: null },
})

const normalized = computed(() => normalizeEvaluation(props.evaluation))
const summary = computed(() => getEvaluationSummary(normalized.value))
</script>

<style scoped>
.msg-evaluation { margin-top: 8px; font-size: 12px; }

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
  gap: 8px;
}

.metric-item {
  padding: 8px;
  border: 1px solid #e8e2d6;
  border-radius: 8px;
  background: #f7f3df;
}

.metric-label { display: block; margin-bottom: 4px; color: #9f927d; }
.metric-good { color: #6fba2c; }
.metric-warn { color: #f5c31c; }
.metric-bad { color: #e05a5a; }

.metric-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 10px;
  color: #725d42;
}

.metric-notes { margin-top: 8px; color: #9f927d; line-height: 1.5; }
</style>
