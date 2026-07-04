import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../utils/api'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConvId = ref(null)
  const messages = ref([])
  const agentType = ref('edu')     // 'edu' | 'baoyan'
  const isThinking = ref(false)
  const thinkingSteps = ref([])

  async function loadConversations() {
    try {
      const res = await api.get('/api/conversations')
      conversations.value = res.data.conversations || []
    } catch {
      conversations.value = []
    }
  }

  async function loadMessages(convId) {
    try {
      const res = await api.get(`/api/conversations/${convId}`)
      messages.value = res.data.messages || []
    } catch {
      messages.value = []
    }
  }

  function switchAgent(type) {
    agentType.value = type
    currentConvId.value = null
    messages.value = []
  }

  function addMessage(msg) {
    messages.value.push(msg)
  }

  function appendToken(content) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content += content
    }
  }

  function setThinking(steps) {
    thinkingSteps.value = steps
    isThinking.value = steps.length > 0
  }

  function clearThinking() {
    thinkingSteps.value = []
    isThinking.value = false
  }

  return {
    conversations, currentConvId, messages, agentType,
    isThinking, thinkingSteps,
    loadConversations, loadMessages, switchAgent,
    addMessage, appendToken, setThinking, clearThinking,
  }
})
