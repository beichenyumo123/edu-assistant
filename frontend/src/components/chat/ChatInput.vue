<template>
  <div class="input-area">
    <ScopeBar
      v-if="agentType === 'edu'"
      :ready-files="readyFiles"
      :selected-file-ids="selectedFileIds"
      @open-knowledge="$emit('open-knowledge')"
    />
    <n-input-group>
      <n-input
        v-model:value="text"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 4 }"
        :placeholder="placeholder"
        :disabled="disabled"
        @keydown="handleKeydown"
        clearable
      />
      <n-button type="primary" :disabled="!text.trim() || disabled" @click="handleSend">
        <n-icon><send-outline /></n-icon>
      </n-button>
    </n-input-group>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { SendOutline } from '@vicons/ionicons5'
import ScopeBar from './ScopeBar.vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  agentType: { type: String, default: 'edu' },
  readyFiles: { type: Array, default: () => [] },
  selectedFileIds: { type: Array, default: () => [] },
})

const emit = defineEmits(['send', 'open-knowledge'])

const text = ref('')
const placeholder = '输入你的问题... (Enter发送，Shift+Enter换行)'

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleSend() {
  if (!text.value.trim() || props.disabled) return
  emit('send', text.value)
  text.value = ''
}
</script>

<style scoped>
.input-area {
  padding: 12px 20px 20px;
  border-top: 1px solid #e8e2d6;
  background: #f7f3df;
}
</style>
