/**
 * useChat — WebSocket + HTTP 消息发送
 */
import { ref, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import { api } from '../utils/api'
import { ChatWebSocket } from '../utils/websocket'
import { normalizeThinkingSteps, normalizeThinkingStep } from './useThinking'
import { normalizeEvaluation } from './useEvaluation'
import { useConversations } from './useConversations'

export function useChat(userId) {
  const nMessage = useMessage()
  const { conversations, currentConvId, loadConversations, loadMessages: loadConvMessages } = useConversations()

  const messages = ref([])
  const isThinking = ref(false)
  const thinkingSteps = ref([])
  const messageAreaRef = ref(null)

  let ws = null

  // ── 滚动 ──
  function isNearBottom() {
    const el = messageAreaRef.value
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < 50
  }

  function scrollToBottom(force = false) {
    nextTick(() => {
      const el = messageAreaRef.value
      if (!el) return
      if (force || isNearBottom()) {
        el.scrollTop = el.scrollHeight
      }
    })
  }

  // ── 消息加载 ──
  async function loadMessages(convId) {
    try {
      const res = await api.get(`/api/conversations/${convId}`)
      messages.value = (res.data.messages || []).map(normalizeMessage)
      await nextTick()
      scrollToBottom(true)
    } catch { /* ignore */ }
  }

  function normalizeMessage(message) {
    return {
      ...message,
      sources: Array.isArray(message.sources) ? message.sources : [],
      agent_steps: normalizeThinkingSteps(message.agent_steps),
      evaluation: normalizeEvaluation(message.evaluation),
    }
  }

  // ── WebSocket ──
  function connectWebSocket() {
    ws = new ChatWebSocket(userId)
    ws.on('thinking', (data) => {
      const step = normalizeThinkingStep(data)
      thinkingSteps.value.push(step)
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.agent_steps = [...thinkingSteps.value]
      }
      scrollToBottom()
    })
    ws.on('token', (data) => {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.content += data.content
      }
      scrollToBottom()
    })
    ws.on('meta', (data) => {
      if (data.conversation_id && !currentConvId.value) {
        currentConvId.value = data.conversation_id
        loadConversations()
      }
    })
    ws.on('done', (data) => {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.sources = data.sources
        last.agent_steps = normalizeThinkingSteps(data.agent_steps || thinkingSteps.value)
        last.evaluation = normalizeEvaluation(data.evaluation)
      }
      isThinking.value = false
      thinkingSteps.value = []
      scrollToBottom()
    })
    ws.on('error', (data) => {
      nMessage.error(data.message)
      isThinking.value = false
      thinkingSteps.value = []
    })
    ws.connect()
  }

  function disconnectWebSocket() {
    if (ws) ws.close()
    ws = null
  }

  // ── 消息发送 ──
  async function sendMessage(text, agentType, selectedFileIds) {
    const msg = text?.trim()
    if (!msg || isThinking.value) return

    messages.value.push({ role: 'user', content: msg })
    messages.value.push({ role: 'assistant', content: '', sources: [], agent_steps: [], evaluation: null })
    isThinking.value = true
    thinkingSteps.value = []
    scrollToBottom(true)

    const payload = {
      conversation_id: currentConvId.value,
      message: msg,
      agent_type: agentType,
      selected_document_ids: agentType === 'edu' ? [...selectedFileIds] : undefined,
    }

    const sentByWs = ws?.send(payload)
    if (!sentByWs) {
      await sendMessageByHttp(payload)
    }
  }

  async function sendMessageByHttp(payload) {
    try {
      const res = await api.post('/api/chat/ask', payload)
      currentConvId.value = res.data.conversation_id
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.content = res.data.message.content
        last.sources = res.data.message.sources || []
        last.agent_steps = normalizeThinkingSteps(res.data.message.agent_steps || res.data.agent_steps || [])
        last.evaluation = normalizeEvaluation(res.data.message.evaluation || res.data.evaluation)
      }
      await loadConversations()
    } catch (e) {
      nMessage.error(e.response?.data?.detail || '消息发送失败')
      messages.value.pop()
    } finally {
      isThinking.value = false
      thinkingSteps.value = []
      scrollToBottom()
    }
  }

  return {
    messages, isThinking, thinkingSteps, messageAreaRef,
    loadMessages, sendMessage,
    connectWebSocket, disconnectWebSocket,
    scrollToBottom,
  }
}
