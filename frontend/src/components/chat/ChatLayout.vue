<template>
  <div class="chat-layout">
    <Sidebar
      :conversations="conversations"
      :current-conv-id="currentConvId"
      @new-chat="$emit('new-chat')"
      @select-conversation="(conv) => $emit('select-conversation', conv)"
      @delete-conversation="(id) => $emit('delete-conversation', id)"
      @logout="$emit('logout')"
    />

    <main class="main-area">
      <ChatHeader
        :agent-type="agentType"
        @switch-agent="$emit('switch-agent', $event)"
        @open-knowledge="$emit('open-knowledge')"
      />

      <MessageArea
        ref="messageAreaRef"
        :messages="messages"
        :is-thinking="isThinking"
        :agent-type="agentType"
        @send="(text) => $emit('send', text)"
      />

      <ChatInput
        :disabled="isThinking"
        :agent-type="agentType"
        :ready-files="readyFiles"
        :selected-file-ids="selectedFileIds"
        @send="(text) => $emit('send', text)"
        @open-knowledge="$emit('open-knowledge')"
      />
      <Footer type="tree" />
    </main>

    <KnowledgeDrawer
      v-model:open="showFileDrawerModel"
      :files="files"
      :ready-files="readyFiles"
      :selected-ready-files="selectedReadyFiles"
      :uploading="uploading"
      :tool-loading="toolLoading"
      :tool-result="toolResult"
      :is-file-selected="isFileSelected"
      @upload="(opts) => $emit('upload', opts)"
      @select-all="$emit('select-all-files')"
      @clear-selection="$emit('clear-files')"
      @toggle-file="(id, checked) => $emit('toggle-file', id, checked)"
      @summarize="(f) => $emit('summarize', f)"
      @extract-knowledge="(f) => $emit('extract-knowledge', f)"
      @delete-file="(id) => $emit('delete-file', id)"
      @copy-result="$emit('copy-result')"
      @ask-knowledge="(p) => $emit('ask-knowledge', p)"
      @download-markdown="$emit('download-markdown')"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Footer } from 'animal-island-vue'
import Sidebar from './Sidebar.vue'
import ChatHeader from './ChatHeader.vue'
import MessageArea from './MessageArea.vue'
import ChatInput from './ChatInput.vue'
import KnowledgeDrawer from './KnowledgeDrawer.vue'

const props = defineProps({
  conversations: { type: Array, default: () => [] },
  currentConvId: { type: [Number, String], default: null },
  messages: { type: Array, default: () => [] },
  isThinking: { type: Boolean, default: false },
  agentType: { type: String, default: 'edu' },
  files: { type: Array, default: () => [] },
  readyFiles: { type: Array, default: () => [] },
  selectedFileIds: { type: Array, default: () => [] },
  selectedReadyFiles: { type: Array, default: () => [] },
  showFileDrawer: { type: Boolean, default: false },
  uploading: { type: Boolean, default: false },
  toolLoading: { type: String, default: '' },
  toolResult: { type: Object, default: null },
  isFileSelected: { type: Function, default: () => false },
})

const emit = defineEmits([
  'update:showFileDrawer',
  'logout', 'switch-agent', 'open-knowledge', 'send',
  'upload', 'select-all-files', 'clear-files', 'toggle-file',
  'summarize', 'extract-knowledge', 'delete-file',
  'copy-result', 'ask-knowledge', 'download-markdown',
  'new-chat', 'select-conversation', 'delete-conversation',
])

const showFileDrawerModel = computed({
  get: () => props.showFileDrawer,
  set: (val) => emit('update:showFileDrawer', val),
})

const messageAreaRef = ref(null)

defineExpose({ messageAreaRef })
</script>

<style scoped>
.chat-layout { display: flex; height: 100vh; }
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8f8f0;
}
</style>
