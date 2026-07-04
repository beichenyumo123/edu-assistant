<template>
  <div class="chat-layout">
    <!-- ===== 左侧边栏 ===== -->
    <aside class="sidebar">
      <!-- Logo -->
      <div class="sidebar-header" @click="handleNewChat">
        <span class="logo">📚</span>
        <span class="brand">EduAssistant</span>
      </div>

      <!-- 新建对话 -->
      <div class="sidebar-actions">
        <n-button type="primary" ghost class="new-chat-btn" @click="handleNewChat">
          <n-icon><add-outline /></n-icon> 新对话
        </n-button>
      </div>

      <!-- 对话列表 -->
      <div class="conv-list">
        <div v-for="conv in conversations" :key="conv.id" class="conv-item"
          :class="{ active: conv.id === currentConvId }"
          @click="selectConversation(conv)">
          <n-icon size="16"><chatbubbles-outline /></n-icon>
          <span class="conv-title">{{ conv.title }}</span>
          <n-popconfirm @positive-click="deleteConversation(conv.id)">
            <template #trigger>
              <n-button text size="tiny" class="delete-btn" @click.stop><n-icon><trash-outline /></n-icon></n-button>
            </template>
            确定删除此对话？
          </n-popconfirm>
        </div>
        <n-empty v-if="conversations.length === 0" description="暂无对话" style="margin-top: 40px" />
      </div>

      <!-- 底部用户区 -->
      <div class="sidebar-footer">
        <n-button text @click="handleLogout">
          <n-icon><log-out-outline /></n-icon> 退出
        </n-button>
      </div>
    </aside>

    <!-- ===== 右侧主区域 ===== -->
    <main class="main-area">
      <!-- 顶部Agent切换栏 -->
      <header class="chat-header">
        <n-radio-group :value="agentType" @update:value="switchAgent" size="large">
          <n-radio-button value="edu" label="📖 教育助手">
            <span>📖 教育助手</span>
          </n-radio-button>
          <n-radio-button value="baoyan" label="🎓 保研助手">
            <span>🎓 保研助手</span>
          </n-radio-button>
        </n-radio-group>
        <n-button text @click="openKnowledgeBase">
          <n-icon size="20"><folder-open-outline /></n-icon>
          知识库
        </n-button>
      </header>

      <!-- 消息区域 -->
      <div class="message-area" ref="messageAreaRef">
        <!-- 空状态：预设问题卡片 -->
        <div v-if="messages.length === 0 && !isThinking" class="welcome">
          <h2>{{ agentType === 'edu' ? '📖 你好，我是教育助手' : '🎓 你好，我是保研助手' }}</h2>
          <p>{{ agentType === 'edu' ? '上传学习资料或直接提问，我会基于你的资料帮你学习' : '关于保研的任何问题，我都可以帮你解答' }}</p>
          <div class="preset-cards">
            <div v-for="q in presetQuestions" :key="q" class="preset-card" @click="sendMessage(q)">
              {{ q }}
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(msg, idx) in messages" :key="idx" class="msg-row" :class="msg.role">
          <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="msg-bubble">
            <div v-if="msg.role === 'assistant'" class="msg-content" v-html="renderMarkdown(msg.content)" />
            <div v-else class="msg-content">{{ msg.content }}</div>
            <!-- 来源标注 -->
            <div v-if="msg.sources && msg.sources.length > 0" class="msg-sources">
              <n-collapse>
                <n-collapse-item title="📎 参考来源">
                  <div v-for="(s, si) in msg.sources" :key="si" class="source-item">
                    📄 文档{{ s.document_id }} · 块{{ s.chunk_index }}: {{ s.text?.substring(0, 150) }}...
                  </div>
                </n-collapse-item>
              </n-collapse>
            </div>
          </div>
        </div>

        <!-- Agent思考过程 -->
        <div v-if="isThinking" class="msg-row assistant">
          <div class="msg-avatar">🤖</div>
          <div class="msg-bubble thinking-bubble">
            <div class="thinking-header">🧠 Agent 思考中...</div>
            <div v-for="(step, si) in thinkingSteps" :key="si" class="thinking-step">
              <n-icon size="14" color="#18a058"><checkmark-circle-outline /></n-icon>
              {{ step }}
            </div>
            <n-spin size="small" style="margin-top: 8px" />
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <n-input-group>
          <n-input v-model:value="inputText" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入你的问题... (Enter发送，Shift+Enter换行)"
            :disabled="isThinking"
            @keydown="handleKeydown"
            clearable />
          <n-button type="primary" :disabled="!inputText.trim() || isThinking" @click="sendMessage()">
            <n-icon><send-outline /></n-icon>
          </n-button>
        </n-input-group>
      </div>
    </main>

    <!-- ===== 知识库抽屉 ===== -->
    <n-drawer v-model:show="showFileDrawer" :width="400" placement="right">
      <n-drawer-content title="📁 我的知识库">
        <n-upload multiple :max="5" accept=".pdf,.docx,.txt,.md" :custom-request="handleUpload"
          :disabled="uploading">
          <n-button :loading="uploading">
            <n-icon><cloud-upload-outline /></n-icon> 上传文件
          </n-button>
        </n-upload>
        <n-divider />
        <div v-if="files.length === 0">
          <n-empty description="还没有上传过文件" />
        </div>
        <n-list v-else>
          <n-list-item v-for="f in files" :key="f.id">
            <template #prefix>
              <n-tag :type="f.status === 'ready' ? 'success' : f.status === 'error' ? 'error' : 'warning'" size="small">
                {{ f.status === 'ready' ? '已就绪' : f.status === 'error' ? '失败' : '处理中' }}
              </n-tag>
            </template>
            <n-thing :title="f.original_name" :description="`${formatSize(f.file_size)} · ${f.chunk_count}块 · ${f.created_at?.substring(0, 10)}`" />
            <template #suffix>
              <n-space vertical size="small">
                <n-button size="tiny" ghost type="primary" :loading="toolLoading === `summary-${f.id}`" @click="summarizeFile(f)">
                  摘要
                </n-button>
                <n-button size="tiny" ghost type="info" :loading="toolLoading === `knowledge-${f.id}`" @click="extractKnowledge(f)">
                  知识点
                </n-button>
                <n-button text type="error" @click="deleteFile(f.id)"><n-icon><trash-outline /></n-icon></n-button>
              </n-space>
            </template>
          </n-list-item>
        </n-list>

        <n-divider />
        <n-card v-if="toolResult" size="small" :title="toolResult.title">
          <div v-if="toolResult.type === 'summary'" class="tool-markdown" v-html="renderMarkdown(toolResult.content)" />
          <div v-else class="knowledge-list">
            <n-card v-for="point in toolResult.points" :key="point.title" size="small" hoverable class="knowledge-card"
              @click="askKnowledge(point)">
              <template #header>{{ point.title }}</template>
              {{ point.description }}
            </n-card>
          </div>
          <template #footer>
            <n-button v-if="toolResult.type === 'summary'" size="small" @click="copyToolResult">复制摘要</n-button>
            <n-text v-else depth="3">点击知识点可直接追问</n-text>
          </template>
        </n-card>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  AddOutline, ChatbubblesOutline, TrashOutline, LogOutOutline,
  FolderOpenOutline, SendOutline, CloudUploadOutline, CheckmarkCircleOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth'
import { api } from '../utils/api'
import { ChatWebSocket } from '../utils/websocket'
import { md } from '../utils/markdown'
import 'highlight.js/styles/github.css'

const router = useRouter()
const nMessage = useMessage()
const authStore = useAuthStore()

// ===== 状态 =====
const agentType = ref('edu')
const conversations = ref([])
const currentConvId = ref(null)
const messages = ref([])
const inputText = ref('')
const isThinking = ref(false)
const thinkingSteps = ref([])
const files = ref([])
const showFileDrawer = ref(false)
const uploading = ref(false)
const toolLoading = ref('')
const toolResult = ref(null)
const messageAreaRef = ref(null)

let ws = null

// 预设问题
const eduPresets = [
  '帮我总结这篇课文的核心内容',
  '提取这一章节的重要知识点',
  '这篇文章的结构是什么？',
  '用简单的话解释这个概念',
  '给我出几道关于这个知识点的题',
  '帮我制定一个学习计划',
]
const baoyanPresets = [
  '保研需要准备哪些材料？',
  '计算机专业有哪些好学校推荐？',
  '预推免和夏令营有什么区别？',
  '如何选择导师？',
  '保研面试一般问什么？',
  '我的条件能保什么层次的学校？',
]
const presetQuestions = computed(() => agentType.value === 'edu' ? eduPresets : baoyanPresets)

// ===== 生命周期 =====
onMounted(async () => {
  await authStore.fetchUser()
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  loadConversations()
  loadFiles()
  // 连接WebSocket
  ws = new ChatWebSocket(authStore.user?.id)
  ws.on('thinking', (data) => thinkingSteps.value.push(data.step))
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
})

// ===== 对话管理 =====
async function loadConversations() {
  try {
    const res = await api.get('/api/conversations')
    conversations.value = res.data.conversations || []
  } catch { /* ignore */ }
}

async function loadMessages(convId) {
  try {
    const res = await api.get(`/api/conversations/${convId}`)
    messages.value = res.data.messages || []
    await nextTick()
    scrollToBottom()
  } catch { /* ignore */ }
}

function selectConversation(conv) {
  currentConvId.value = conv.id
  loadMessages(conv.id)
}

function handleNewChat() {
  currentConvId.value = null
  messages.value = []
  thinkingSteps.value = []
  isThinking.value = false
}

async function deleteConversation(convId) {
  try {
    await api.delete(`/api/conversations/${convId}`)
    if (currentConvId.value === convId) {
      handleNewChat()
    }
    loadConversations()
  } catch { /* ignore */ }
}

function switchAgent(type) {
  agentType.value = type
  handleNewChat()
}

// ===== 消息发送 =====
async function sendMessage(text) {
  const msg = text || inputText.value.trim()
  if (!msg || isThinking.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: msg })
  messages.value.push({ role: 'assistant', content: '', sources: [] })
  inputText.value = ''
  isThinking.value = true
  thinkingSteps.value = []
  scrollToBottom()

  const payload = {
    conversation_id: currentConvId.value,
    message: msg,
    agent_type: agentType.value,
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
    }
    thinkingSteps.value = res.data.agent_steps || []
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

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// ===== 文件管理 =====
async function loadFiles() {
  try {
    const res = await api.get('/api/files')
    files.value = res.data.files || []
  } catch { /* ignore */ }
}

async function openKnowledgeBase() {
  await loadFiles()
  showFileDrawer.value = true
}

async function handleUpload({ file, onFinish, onError }) {
  uploading.value = true
  const formData = new FormData()
  formData.append('file', file.file)
  try {
    await api.post('/api/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    nMessage.success(`${file.name} 上传成功`)
    loadFiles()
    onFinish()
  } catch (e) {
    nMessage.error(e.response?.data?.detail || '上传失败')
    onError()
  } finally {
    uploading.value = false
  }
}

async function deleteFile(fileId) {
  try {
    await api.delete(`/api/files/${fileId}`)
    nMessage.success('文件已删除')
    loadFiles()
  } catch { /* ignore */ }
}

async function summarizeFile(file) {
  toolLoading.value = `summary-${file.id}`
  try {
    const res = await api.post('/api/tools/summarize', {
      document_id: file.id,
      length: 'medium',
    })
    toolResult.value = {
      type: 'summary',
      title: `${file.original_name} · 摘要`,
      content: res.data.summary,
    }
  } catch (e) {
    nMessage.error(e.response?.data?.detail || '摘要生成失败')
  } finally {
    toolLoading.value = ''
  }
}

async function extractKnowledge(file) {
  toolLoading.value = `knowledge-${file.id}`
  try {
    const res = await api.post('/api/tools/extract-knowledge', {
      document_id: file.id,
    })
    toolResult.value = {
      type: 'knowledge',
      title: `${file.original_name} · 知识点`,
      points: res.data.knowledge_points || [],
    }
  } catch (e) {
    nMessage.error(e.response?.data?.detail || '知识点提取失败')
  } finally {
    toolLoading.value = ''
  }
}

async function copyToolResult() {
  if (!toolResult.value?.content) return
  await navigator.clipboard.writeText(toolResult.value.content)
  nMessage.success('摘要已复制')
}

function askKnowledge(point) {
  showFileDrawer.value = false
  sendMessage(`请围绕“${point.title}”展开讲解，并结合资料说明：${point.description}`)
}

// ===== 工具 =====
function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
}

function scrollToBottom() {
  nextTick(() => {
    const el = messageAreaRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

function handleLogout() {
  authStore.logout()
  if (ws) ws.close()
  router.push('/login')
}
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
}

/* ===== 左侧边栏 ===== */
.sidebar {
  width: 280px;
  min-width: 280px;
  background: #f6f8fb;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #dfe3ea;
}

.sidebar-header {
  min-height: 88px;
  padding: 20px 22px 16px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1f2937;
}

.sidebar-header .logo {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  line-height: 1;
}

.sidebar-header .brand {
  font-size: 22px;
  letter-spacing: 0;
  white-space: nowrap;
}

.sidebar-actions {
  padding: 0 18px 16px;
}

.new-chat-btn {
  width: 100%;
  height: 42px;
  border-radius: 8px;
  font-size: 16px;
  justify-content: center;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 2px 12px 12px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  margin-bottom: 8px;
  color: #283142;
  transition: background 0.15s, color 0.15s;
}

.conv-item:hover { background: #eef2f7; }
.conv-item.active {
  background: #e8f0fe;
  color: #1557c0;
}

.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn { opacity: 0; }
.conv-item:hover .delete-btn { opacity: 1; }

.sidebar-footer {
  padding: 14px 18px;
  border-top: 1px solid #dfe3ea;
  background: #f6f8fb;
}

/* ===== 主区域 ===== */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}

/* ===== 消息区 ===== */
.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
}

.welcome h2 { font-size: 28px; color: #333; margin-bottom: 8px; }
.welcome p { color: #999; margin-bottom: 24px; }

.preset-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.preset-card {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  transition: all 0.15s;
  text-align: center;
}

.preset-card:hover {
  background: #e8f0fe;
  color: #1a73e8;
  transform: translateY(-1px);
}

/* 消息行 */
.msg-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 800px;
}

.msg-row.user { flex-direction: row-reverse; margin-left: auto; }

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  background: #f0f2f5;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  max-width: 85%;
}

.msg-row.user .msg-bubble {
  background: #1a73e8;
  color: #fff;
}

.msg-row.assistant .msg-bubble {
  background: #f5f7fa;
  color: #333;
}

.msg-content { white-space: pre-wrap; word-break: break-word; }

.msg-row.assistant .msg-content :deep(h1),
.msg-row.assistant .msg-content :deep(h2),
.msg-row.assistant .msg-content :deep(h3) {
  margin: 8px 0 4px;
}

.msg-row.assistant .msg-content :deep(code) {
  background: #e8e8e8;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 13px;
}

.msg-row.assistant .msg-content :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.msg-row.assistant .msg-content :deep(pre code) {
  background: transparent;
  color: inherit;
}

.msg-sources {
  margin-top: 8px;
  font-size: 12px;
}

.source-item {
  padding: 4px 0;
  color: #888;
  font-size: 12px;
}

/* Agent思考 */
.thinking-bubble {
  border: 1px dashed #18a058 !important;
}

.thinking-header {
  font-weight: bold;
  margin-bottom: 8px;
  color: #18a058;
}

.thinking-step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
  padding: 2px 0;
}

/* ===== 输入区 ===== */
.input-area {
  padding: 12px 20px 20px;
  border-top: 1px solid #eee;
  background: #fafafa;
}

.tool-markdown {
  max-height: 320px;
  overflow-y: auto;
  line-height: 1.7;
}

.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}

.knowledge-card {
  cursor: pointer;
}
</style>
