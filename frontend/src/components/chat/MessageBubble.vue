<template>
  <div class="msg-row" :class="message.role">
    <div class="msg-avatar">{{ message.role === 'user' ? '👤' : '🤖' }}</div>
    <div class="msg-bubble">
      <MessageContent :content="message.content" :role="message.role" />
      <ThinkingSteps
        v-if="message.role === 'assistant'"
        :steps="message.agent_steps"
        :is-active="isActive"
      />
      <EvaluationMetrics
        v-if="message.role === 'assistant'"
        :evaluation="message.evaluation"
      />
      <MessageSources
        v-if="message.role === 'assistant'"
        :sources="message.sources || []"
      />
    </div>
  </div>
</template>

<script setup>
import MessageContent from './MessageContent.vue'
import ThinkingSteps from './ThinkingSteps.vue'
import EvaluationMetrics from './EvaluationMetrics.vue'
import MessageSources from './MessageSources.vue'

defineProps({
  message: { type: Object, required: true },
  isActive: { type: Boolean, default: false },
})
</script>

<style scoped>
.msg-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 800px;
}

.msg-row.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  background: #f0e8d8;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.6;
  max-width: 85%;
}

.msg-row.user .msg-bubble {
  background: #19c8b9;
  color: #fff9e3;
}

.msg-row.assistant .msg-bubble {
  background: #f7f3df;
  color: #725d42;
}
</style>
