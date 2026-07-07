<template>
  <ChatLayout
    ref="layoutRef"
    :conversations="conversations"
    :current-conv-id="currentConvId"
    :messages="messages"
    :is-thinking="isThinking"
    :agent-type="agentType"
    :files="files"
    :ready-files="readyFiles"
    :selected-file-ids="selectedFileIds"
    :selected-ready-files="selectedReadyFiles"
    v-model:show-file-drawer="showFileDrawer"
    :uploading="uploading"
    :tool-loading="toolLoading"
    :tool-result="toolResult"
    :is-file-selected="isFileSelected"
    @logout="handleLogout"
    @switch-agent="switchAgent"
    @open-knowledge="openKnowledgeBase"
    @send="(text) => sendMessage(text)"
    @upload="(opts) => handleUpload(opts)"
    @select-all-files="selectAllReadyFiles"
    @clear-files="clearSelectedFiles"
    @toggle-file="(id, checked) => toggleFileSelection(id, checked)"
    @summarize="(f) => summarizeFile(f)"
    @extract-knowledge="(f) => extractKnowledge(f)"
    @delete-file="(id) => deleteFile(id)"
    @copy-result="copyToolResult"
    @ask-knowledge="(p) => askKnowledge(p)"
    @download-markdown="downloadKnowledgeMarkdown"
    @new-chat="handleNewChat"
    @select-conversation="(conv) => onSelectConversation(conv)"
    @delete-conversation="(id) => deleteConversation(id)"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useConversations } from '../composables/useConversations'
import { useChat } from '../composables/useChat'
import { useFiles } from '../composables/useFiles'
import ChatLayout from '../components/chat/ChatLayout.vue'
import 'highlight.js/styles/github.css'

const router = useRouter()
const authStore = useAuthStore()

const agentType = ref('edu')
const layoutRef = ref(null)

// ── Composables ──
const { conversations, currentConvId, loadConversations, handleNewChat, deleteConversation } = useConversations()
const chat = useChat(authStore.user?.id)
const { messages, isThinking, loadMessages, sendMessage: sendChatMessage, connectWebSocket, disconnectWebSocket } = chat
const {
  files, selectedFileIds, showFileDrawer, uploading, toolLoading, toolResult,
  readyFiles, selectedReadyFiles,
  loadFiles, isFileSelected, toggleFileSelection,
  selectAllReadyFiles, clearSelectedFiles, handleUpload,
  summarizeFile: summarizeFileImpl, extractKnowledge: extractKnowledgeImpl,
  copyToolResult, downloadKnowledgeMarkdown,
} = useFiles()

const messageAreaRef = chat.messageAreaRef

// ── 生命周期 ──
onMounted(async () => {
  await authStore.fetchUser()
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  loadConversations()
  loadFiles()
  connectWebSocket()
})

// ── 对话选择 ──
function onSelectConversation(conv) {
  conversations.value // trigger reactivity
  currentConvId.value = conv.id
  loadMessages(conv.id)
}

// ── Agent 切换 ──
function switchAgent(type) {
  agentType.value = type
  handleNewChat()
  messages.value = []
}

// ── 消息发送 ──
async function sendMessage(text) {
  await sendChatMessage(text, agentType.value, selectedFileIds.value)
}

// ── 知识库 ──
async function openKnowledgeBase() {
  await loadFiles()
  showFileDrawer.value = true
}

async function summarizeFile(file) { await summarizeFileImpl(file) }
async function extractKnowledge(file) { await extractKnowledgeImpl(file) }
async function deleteFile(fileId) {
  await deleteFileImpl(fileId)
}

function askKnowledge(point) {
  showFileDrawer.value = false
  sendMessage(`请围绕"${point.title}"展开讲解，并结合资料说明：${point.description}`)
}

// ── 登出 ──
function handleLogout() {
  disconnectWebSocket()
  authStore.logout()
  router.push('/login')
}
</script>
