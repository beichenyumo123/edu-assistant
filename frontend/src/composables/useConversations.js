/**
 * useConversations — 对话列表管理（模块级单例）
 */
import { ref } from 'vue'
import { api } from '../utils/api'

// 模块级单例状态
const conversations = ref([])
const currentConvId = ref(null)

export function useConversations() {
  async function loadConversations() {
    try {
      const res = await api.get('/api/conversations')
      conversations.value = res.data.conversations || []
    } catch { /* ignore */ }
  }

  async function loadMessages(convId) {
    try {
      const res = await api.get(`/api/conversations/${convId}`)
      return (res.data.messages || [])
    } catch { return [] }
  }

  function selectConversation(conv) {
    currentConvId.value = conv.id
  }

  function handleNewChat() {
    currentConvId.value = null
  }

  async function deleteConversation(convId) {
    try {
      await api.delete(`/api/conversations/${convId}`)
      if (currentConvId.value === convId) {
        currentConvId.value = null
      }
      loadConversations()
    } catch { /* ignore */ }
  }

  return {
    conversations,
    currentConvId,
    loadConversations,
    loadMessages,
    selectConversation,
    handleNewChat,
    deleteConversation,
  }
}
