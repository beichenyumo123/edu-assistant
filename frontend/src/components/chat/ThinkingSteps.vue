<template>
  <div v-if="steps.length > 0" class="msg-thinking">
    <n-collapse>
      <n-collapse-item :title="`Agent 思考过程 · ${duration}`">
        <div v-for="(step, si) in steps" :key="si" class="thinking-step">
          <n-icon size="14" color="#6fba2c"><checkmark-circle-outline /></n-icon>
          <n-tag size="tiny" :bordered="false" type="success">{{ tool(step) }}</n-tag>
          <span class="thinking-text">{{ text(step) }}</span>
          <span v-if="stepDuration(step)" class="thinking-duration">{{ stepDuration(step) }}</span>
        </div>
        <div v-if="isActive" class="thinking-running">
          <n-spin size="small" />
          <span>回答生成中...</span>
        </div>
      </n-collapse-item>
    </n-collapse>
  </div>
  <div v-else-if="isActive" class="thinking-running">
    <n-spin size="small" />
    <span>Agent 思考中...</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { CheckmarkCircleOutline } from '@vicons/ionicons5'
import {
  normalizeThinkingSteps,
  getStepText, getStepTool, formatStepDuration, formatMessageDuration,
} from '../../composables/useThinking'

const props = defineProps({
  steps: { type: [Array, String], default: () => [] },
  isActive: { type: Boolean, default: false },
})

const normalized = computed(() => normalizeThinkingSteps(props.steps))
const steps = computed(() => normalized.value)

const duration = computed(() => {
  if (steps.value.length === 0) return ''
  return formatMessageDuration({ agent_steps: steps.value })
})

function text(step) { return getStepText(step) }
function tool(step) { return getStepTool(step) }
function stepDuration(step) { return formatStepDuration(step) }
</script>

<style scoped>
.msg-thinking {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #e8e2d6;
  font-size: 12px;
}

.thinking-step {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 24px;
  font-size: 12px;
  color: #725d42;
  padding: 3px 0;
}

.thinking-text { flex: 1; min-width: 0; word-break: break-word; }
.thinking-duration { color: #9f927d; font-variant-numeric: tabular-nums; white-space: nowrap; }

.thinking-running {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: #19c8b9;
  font-size: 12px;
}
</style>
