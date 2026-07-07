<template>
  <div class="chat-layout">
    <!-- ===== 左侧边栏 ===== -->
    <aside class="sidebar">
      <!-- Logo -->
      <div class="sidebar-header" @click="handleNewChat">
        <span class="logo">🏢</span>
        <span class="brand">OnboardAgent</span>
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
      <!-- 顶部助手栏 -->
      <header class="chat-header">
        <div class="assistant-title">
          <span class="assistant-icon">🏢</span>
          <div>
            <strong>入职培训助手</strong>
            <span>基于已选企业资料检索回答</span>
          </div>
        </div>
        <n-button text @click="openKnowledgeBase">
          <n-icon size="20"><folder-open-outline /></n-icon>
          企业知识库
        </n-button>
      </header>

      <!-- 消息区域 -->
      <div class="message-area" ref="messageAreaRef">
        <!-- 空状态：预设问题卡片 -->
        <div v-if="messages.length === 0 && !isThinking" class="welcome">
          <h2>🏢 你好，我是入职培训助手</h2>
          <p>上传员工手册、制度流程或岗位培训资料，我会基于公司资料答疑并标注来源</p>
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
            <!-- Agent思考过程 -->
            <div v-if="msg.role === 'assistant' && getMessageSteps(msg).length > 0" class="msg-thinking">
              <n-collapse>
                <n-collapse-item :title="`Agent 思考过程 · ${formatMessageDuration(msg)}`">
                  <div v-for="(step, si) in getMessageSteps(msg)" :key="si" class="thinking-step">
                    <n-icon size="14" color="#18a058"><checkmark-circle-outline /></n-icon>
                    <n-tag size="tiny" :bordered="false" type="success">{{ getStepTool(step) }}</n-tag>
                    <span class="thinking-text">{{ getStepText(step) }}</span>
                    <span v-if="formatStepDuration(step)" class="thinking-duration">{{ formatStepDuration(step) }}</span>
                  </div>
                  <div v-if="isActiveAssistantMessage(idx)" class="thinking-running">
                    <n-spin size="small" />
                    <span>回答生成中...</span>
                  </div>
                </n-collapse-item>
              </n-collapse>
            </div>
            <div v-else-if="isActiveAssistantMessage(idx)" class="thinking-running">
              <n-spin size="small" />
              <span>Agent 思考中...</span>
            </div>
            <!-- RAG评价指标 -->
            <div v-if="msg.evaluation" class="msg-evaluation">
              <n-collapse>
                <n-collapse-item title="RAG 评价指标">
                  <div class="metric-grid">
                    <div v-for="item in getEvaluationSummary(msg.evaluation)" :key="item.label" class="metric-item">
                      <span class="metric-label">{{ item.label }}</span>
                      <strong :class="item.className">{{ item.value }}</strong>
                    </div>
                  </div>
                  <div class="metric-detail">
                    <span>检索块: {{ msg.evaluation.retrieval?.retrieved_chunks ?? 0 }}</span>
                    <span>命中: {{ msg.evaluation.retrieval?.retrieval_hit ? '是' : '否' }}</span>
                    <span>关键结论: {{ msg.evaluation.generation?.supported_claim_count ?? 0 }}/{{ msg.evaluation.generation?.claim_count ?? 0 }}</span>
                    <span>无效引用: {{ msg.evaluation.generation?.invalid_citation_count ?? 0 }}</span>
                  </div>
                  <div v-if="msg.evaluation.notes?.length" class="metric-notes">
                    <div v-for="note in msg.evaluation.notes" :key="note">{{ note }}</div>
                  </div>
                </n-collapse-item>
              </n-collapse>
            </div>
            <!-- 来源标注 -->
            <div v-if="msg.sources && msg.sources.length > 0" class="msg-sources">
              <n-collapse>
                <n-collapse-item title="📎 参考来源">
                  <div v-for="(s, si) in msg.sources" :key="si" class="source-item">
                    📄 {{ s.document_name || ('文档' + s.document_id) }} · 块{{ s.chunk_index }}
                    <span v-if="s.evidence_id"> · {{ s.evidence_id }}</span>
                    <span v-if="s.source_type"> · 类型: {{ s.source_type }}</span>
                    <span v-if="s.trust_level"> · 可信度: {{ s.trust_level }}</span>
                    <span v-if="s.retrieval_score !== undefined"> · 距离: {{ Number(s.retrieval_score).toFixed(4) }}</span>
                    : {{ s.text?.substring(0, 150) }}...
                  </div>
                </n-collapse-item>
              </n-collapse>
            </div>
          </div>
        </div>

      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="scope-bar">
          <n-tag size="small" :type="selectedReadyFiles.length ? 'info' : 'warning'">
            检索范围：{{ selectedScopeLabel }}
          </n-tag>
          <span v-for="file in selectedScopePreview" :key="file.id" class="scope-file">
            {{ file.original_name }}
          </span>
          <span v-if="selectedScopeExtraCount > 0" class="scope-extra">
            +{{ selectedScopeExtraCount }}
          </span>
          <n-button text size="tiny" @click="openKnowledgeBase">选择培训资料</n-button>
        </div>
        <n-input-group>
          <n-input v-model:value="inputText" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入入职、制度、流程或岗位培训问题... (Enter发送，Shift+Enter换行)"
            :disabled="isThinking"
            @keydown="handleKeydown"
            clearable />
          <n-button type="primary" :disabled="!inputText.trim() || isThinking" @click="sendMessage()">
            <n-icon><send-outline /></n-icon>
          </n-button>
        </n-input-group>
      </div>
    </main>

    <!-- ===== 企业知识库抽屉 ===== -->
    <n-drawer v-model:show="showFileDrawer" :width="400" placement="right">
      <n-drawer-content title="📁 企业培训资料库">
        <n-upload multiple :max="5" accept=".pdf,.docx,.txt,.md" :custom-request="handleUpload"
          :disabled="uploading">
          <n-button :loading="uploading">
            <n-icon><cloud-upload-outline /></n-icon> 上传培训资料
          </n-button>
        </n-upload>
        <n-divider />
        <div v-if="files.length === 0">
          <n-empty description="还没有上传培训资料" />
        </div>
        <template v-else>
          <div class="file-select-toolbar">
            <n-text depth="3">已选 {{ selectedReadyFiles.length }} / {{ readyFiles.length }}</n-text>
            <n-space size="small">
              <n-button size="tiny" text @click="selectAllReadyFiles">全选</n-button>
              <n-button size="tiny" text @click="clearSelectedFiles">清空</n-button>
            </n-space>
          </div>
        </template>
        <n-list v-if="files.length > 0">
          <n-list-item v-for="f in files" :key="f.id">
            <template #prefix>
              <div class="file-prefix">
                <n-checkbox :checked="isFileSelected(f.id)" :disabled="f.status !== 'ready'"
                  @update:checked="(checked) => toggleFileSelection(f.id, checked)" />
                <n-tag :type="f.status === 'ready' ? 'success' : f.status === 'error' ? 'error' : 'warning'" size="small">
                  {{ f.status === 'ready' ? '已就绪' : f.status === 'error' ? '失败' : '处理中' }}
                </n-tag>
              </div>
            </template>
            <n-thing :title="f.original_name" :description="`${formatSize(f.file_size)} · ${f.chunk_count}块 · ${f.created_at?.substring(0, 10)}`" />
            <template #suffix>
              <n-space vertical size="small">
                <n-button size="tiny" ghost type="primary" :disabled="f.status !== 'ready'" :loading="toolLoading === `summary-${f.id}`" @click="summarizeFile(f)">
                  制度速览
                </n-button>
                <n-button size="tiny" ghost type="info" :disabled="f.status !== 'ready'" :loading="toolLoading === `knowledge-${f.id}`" @click="extractKnowledge(f)">
                  知识卡片
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
            <n-space>
              <n-button v-if="toolResult.type === 'summary'" size="small" @click="copyToolResult">复制速览</n-button>
              <template v-else>
                <n-button size="small" type="primary" ghost @click="downloadKnowledgeMarkdown">
                  <n-icon><download-outline /></n-icon> 导出 Markdown
                </n-button>
                <n-text depth="3">点击知识卡片可直接追问</n-text>
              </template>
            </n-space>
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
  FolderOpenOutline, SendOutline, CloudUploadOutline, CheckmarkCircleOutline, DownloadOutline,
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
const conversations = ref([])
const currentConvId = ref(null)
const messages = ref([])
const inputText = ref('')
const isThinking = ref(false)
const thinkingSteps = ref([])
const files = ref([])
const selectedFileIds = ref([])
const showFileDrawer = ref(false)
const uploading = ref(false)
const toolLoading = ref('')
const toolResult = ref(null)
const messageAreaRef = ref(null)

let ws = null

// 预设问题
const eduPresets = [
  '入职第一周需要完成哪些事项？',
  '试用期转正评估主要看什么？',
  '请假和异常打卡应该怎么处理？',
  '差旅报销需要注意哪些要求？',
  '哪些公司数据不能外发或上传？',
  '帮我整理新人必修培训清单',
]
const presetQuestions = eduPresets
const readyFiles = computed(() => files.value.filter((file) => file.status === 'ready'))
const selectedReadyFiles = computed(() => readyFiles.value.filter((file) => selectedFileIds.value.includes(file.id)))
const selectedScopePreview = computed(() => selectedReadyFiles.value.slice(0, 2))
const selectedScopeExtraCount = computed(() => Math.max(0, selectedReadyFiles.value.length - selectedScopePreview.value.length))
const selectedScopeLabel = computed(() => {
  if (readyFiles.value.length === 0) return '暂无可用培训资料'
  if (selectedReadyFiles.value.length === 0) return '未选择培训资料'
  if (selectedReadyFiles.value.length === readyFiles.value.length) return `全部培训资料 (${readyFiles.value.length})`
  return `已选 ${selectedReadyFiles.value.length} 份`
})

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
    messages.value = (res.data.messages || []).map(normalizeMessage)
    await nextTick()
    scrollToBottom(true)
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

// ===== 消息发送 =====
async function sendMessage(text, options = {}) {
  const msg = text || inputText.value.trim()
  if (!msg || isThinking.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: msg })
  messages.value.push({ role: 'assistant', content: '', sources: [], agent_steps: [], evaluation: null })
  inputText.value = ''
  isThinking.value = true
  thinkingSteps.value = []
  scrollToBottom(true)

  const hasScopeOverride = Object.prototype.hasOwnProperty.call(options, 'selectedDocumentIds')
  const selectedDocumentIds = hasScopeOverride ? options.selectedDocumentIds : [...selectedFileIds.value]

  const payload = {
    conversation_id: currentConvId.value,
    message: msg,
    agent_type: 'edu',
    selected_document_ids: selectedDocumentIds,
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
    syncSelectedFiles()
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
    nMessage.success(`${file.name} 上传成功，已加入培训资料库`)
    await loadFiles()
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
    selectedFileIds.value = selectedFileIds.value.filter((id) => id !== fileId)
    await loadFiles()
  } catch { /* ignore */ }
}

function syncSelectedFiles() {
  const readyIds = readyFiles.value.map((file) => file.id)
  selectedFileIds.value = selectedFileIds.value.filter((id) => readyIds.includes(id))
}

function isFileSelected(fileId) {
  return selectedFileIds.value.includes(fileId)
}

function toggleFileSelection(fileId, checked) {
  if (checked) {
    if (!selectedFileIds.value.includes(fileId)) {
      selectedFileIds.value = [...selectedFileIds.value, fileId]
    }
  } else {
    selectedFileIds.value = selectedFileIds.value.filter((id) => id !== fileId)
  }
}

function selectAllReadyFiles() {
  selectedFileIds.value = readyFiles.value.map((file) => file.id)
}

function clearSelectedFiles() {
  selectedFileIds.value = []
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
      title: `${file.original_name} · 制度速览`,
      content: res.data.summary,
    }
  } catch (e) {
    nMessage.error(e.response?.data?.detail || '制度速览生成失败')
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
      title: `${file.original_name} · 培训知识卡片`,
      document_id: res.data.document_id || file.id,
      points: res.data.knowledge_points || [],
    }
  } catch (e) {
    nMessage.error(e.response?.data?.detail || '培训知识卡片提取失败')
  } finally {
    toolLoading.value = ''
  }
}

async function copyToolResult() {
  if (!toolResult.value?.content) return
  await navigator.clipboard.writeText(toolResult.value.content)
  nMessage.success('制度速览已复制')
}

function compactMarkdownText(value, maxLength = 0) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  if (maxLength > 0 && text.length > maxLength) {
    return `${text.slice(0, Math.max(0, maxLength - 3)).trim()}...`
  }
  return text
}

function asExportList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => compactMarkdownText(item, 220)).filter(Boolean)
  }
  if (typeof value === 'string' && value.trim()) {
    return value.split(/\n+|[；;]/).map((item) => compactMarkdownText(item, 220)).filter(Boolean)
  }
  return []
}

function uniqueTexts(items) {
  const seen = new Set()
  const result = []
  for (const item of items) {
    const text = compactMarkdownText(item, 320)
    const key = text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '').slice(0, 100)
    if (!text || seen.has(key)) continue
    seen.add(key)
    result.push(text)
  }
  return result
}

function getPointExcerpts(point) {
  const excerpts = []
  if (point.source_excerpt) excerpts.push(point.source_excerpt)
  if (Array.isArray(point.relevant_chunks)) {
    excerpts.push(...point.relevant_chunks.map((chunk) => chunk?.text))
  }
  return uniqueTexts(excerpts).slice(0, 2)
}

function groupKnowledgePoints(points) {
  const groups = []
  const groupMap = new Map()
  points.forEach((point, index) => {
    const category = compactMarkdownText(point.category) || '核心培训知识'
    if (!groupMap.has(category)) {
      const group = { category, points: [] }
      groupMap.set(category, group)
      groups.push(group)
    }
    groupMap.get(category).points.push({ ...point, exportIndex: index + 1 })
  })
  return groups
}

function appendBulletList(markdown, title, items) {
  if (!items.length) return markdown
  let next = `${markdown}${title}\n\n`
  for (const item of items) {
    next += `- ${item}\n`
  }
  return `${next}\n`
}

function downloadKnowledgeMarkdown() {
  if (!toolResult.value?.points?.length) return
  const points = toolResult.value.points
  const groups = groupKnowledgePoints(points)
  const now = new Date().toLocaleString('zh-CN')
  let markdown = `# ${toolResult.value.title}\n\n`
  markdown += `> 导出时间：${now}  |  共 ${points.length} 张培训知识卡片  |  ${groups.length} 个模块\n\n`
  markdown += `## 资料概览\n\n`
  markdown += `- 知识卡片数量：${points.length}\n`
  markdown += `- 模块结构：${groups.map((group) => group.category).join('、')}\n\n`

  for (const [groupIndex, group] of groups.entries()) {
    markdown += `## ${groupIndex + 1}. ${group.category}\n\n`
    for (const [pointIndex, point] of group.points.entries()) {
      const title = compactMarkdownText(point.title) || `培训知识 ${point.exportIndex}`
      const description = compactMarkdownText(point.description)
      const keyPoints = asExportList(point.key_points)
      const examples = asExportList(point.examples)
      const excerpts = getPointExcerpts(point)

      markdown += `### ${groupIndex + 1}.${pointIndex + 1} ${title}\n\n`
      if (description) {
        markdown += `${description}\n\n`
      }
      markdown = appendBulletList(markdown, `**新人需要知道：**`, keyPoints)
      markdown = appendBulletList(markdown, `**制度原文或操作口径：**`, examples)
      if (excerpts.length) {
        markdown += `**原文依据：**\n\n`
        for (const excerpt of excerpts) {
          markdown += `> ${excerpt.replace(/\n/g, '\n> ')}\n>\n`
        }
      }
      markdown += `\n`
    }
  }
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${toolResult.value.title}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  nMessage.success('Markdown 已导出')
}

function askKnowledge(point) {
  showFileDrawer.value = false
  const sourceDocumentId = toolResult.value?.document_id
  sendMessage(
    `请围绕“${point.title}”展开讲解，并结合资料说明：${point.description}`,
    sourceDocumentId ? { selectedDocumentIds: [sourceDocumentId] } : {},
  )
}

// ===== 工具 =====
function inferStepTool(text) {
  if (/(检索|文档片段|知识库|匹配)/.test(text)) return '企业知识检索'
  if (/(生成|回答)/.test(text)) return '回答生成'
  if (/分析/.test(text)) return '问题分析'
  return 'Agent'
}

function normalizeThinkingStep(step) {
  if (typeof step === 'string') {
    return {
      text: step,
      tool_name: inferStepTool(step),
      elapsed_ms: null,
    }
  }
  const text = compactMarkdownText(step?.text || step?.step || '')
  const elapsed = Number(step?.elapsed_ms)
  return {
    text,
    tool_name: compactMarkdownText(step?.tool_name) || inferStepTool(text),
    elapsed_ms: Number.isFinite(elapsed) ? elapsed : null,
  }
}

function normalizeThinkingSteps(steps) {
  if (typeof steps === 'string' && steps.trim()) {
    try {
      return normalizeThinkingSteps(JSON.parse(steps))
    } catch {
      return []
    }
  }
  if (!Array.isArray(steps)) return []
  return steps.map(normalizeThinkingStep).filter((step) => step.text)
}

function normalizeMessage(message) {
  return {
    ...message,
    sources: Array.isArray(message.sources) ? message.sources : [],
    agent_steps: normalizeThinkingSteps(message.agent_steps),
    evaluation: normalizeEvaluation(message.evaluation),
  }
}

function normalizeEvaluation(evaluation) {
  if (typeof evaluation === 'string' && evaluation.trim()) {
    try {
      return normalizeEvaluation(JSON.parse(evaluation))
    } catch {
      return null
    }
  }
  if (!evaluation || typeof evaluation !== 'object') return null
  return evaluation
}

function formatMetricPercent(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return `${Math.round(number * 100)}%`
}

function metricClass(value, reverse = false) {
  const number = Number(value)
  if (!Number.isFinite(number)) return ''
  const good = reverse ? number <= 0.25 : number >= 0.7
  const bad = reverse ? number >= 0.55 : number < 0.4
  if (good) return 'metric-good'
  if (bad) return 'metric-bad'
  return 'metric-warn'
}

function getEvaluationSummary(evaluation) {
  const safe = normalizeEvaluation(evaluation) || {}
  return [
    { label: '总分', value: formatMetricPercent(safe.overall_score), className: metricClass(safe.overall_score) },
    { label: '检索质量', value: formatMetricPercent(safe.retrieval_quality), className: metricClass(safe.retrieval_quality) },
    { label: '证据支撑', value: formatMetricPercent(safe.groundedness), className: metricClass(safe.groundedness) },
    { label: '引用覆盖', value: formatMetricPercent(safe.citation_coverage), className: metricClass(safe.citation_coverage) },
    { label: '引用正确', value: formatMetricPercent(safe.citation_validity), className: metricClass(safe.citation_validity) },
    { label: '幻觉风险', value: formatMetricPercent(safe.hallucination_risk), className: metricClass(safe.hallucination_risk, true) },
  ]
}

function getMessageSteps(message) {
  return normalizeThinkingSteps(message.agent_steps)
}

function getStepText(step) {
  return normalizeThinkingStep(step).text
}

function getStepTool(step) {
  return normalizeThinkingStep(step).tool_name
}

function formatDuration(ms) {
  if (ms === null || ms === undefined) return ''
  const value = Number(ms)
  if (!Number.isFinite(value)) return ''
  if (value < 1000) return `${Math.max(0, Math.round(value))} ms`
  if (value < 10000) return `${(value / 1000).toFixed(1)} s`
  return `${Math.round(value / 1000)} s`
}

function formatStepDuration(step) {
  return formatDuration(normalizeThinkingStep(step).elapsed_ms)
}

function formatMessageDuration(message) {
  const steps = getMessageSteps(message)
  const lastWithDuration = [...steps].reverse().find((step) => step.elapsed_ms !== null)
  if (lastWithDuration) {
    return `总耗时 ${formatDuration(lastWithDuration.elapsed_ms)}`
  }
  return `${steps.length} 步`
}

function isActiveAssistantMessage(index) {
  return isThinking.value && index === messages.value.length - 1 && messages.value[index]?.role === 'assistant'
}

function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
}

function isNearBottom() {
  const el = messageAreaRef.value
  if (!el) return true
  // 距离底部 50px 以内视为"在底部"
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

.assistant-title {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: #1f2937;
}

.assistant-icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  background: #e8f0fe;
  border-radius: 8px;
  font-size: 20px;
}

.assistant-title strong {
  display: block;
  font-size: 16px;
  line-height: 1.25;
}

.assistant-title span:last-child {
  display: block;
  margin-top: 2px;
  color: #6b7280;
  font-size: 12px;
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

.msg-evaluation {
  margin-top: 8px;
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
  gap: 8px;
}

.metric-item {
  padding: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
}

.metric-label {
  display: block;
  margin-bottom: 4px;
  color: #777;
}

.metric-good { color: #18a058; }
.metric-warn { color: #f0a020; }
.metric-bad { color: #d03050; }

.metric-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 10px;
  color: #666;
}

.metric-notes {
  margin-top: 8px;
  color: #888;
  line-height: 1.5;
}

.source-item {
  padding: 4px 0;
  color: #888;
  font-size: 12px;
}

.msg-thinking {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #e4e7ed;
  font-size: 12px;
}

.thinking-step {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 24px;
  font-size: 12px;
  color: #666;
  padding: 3px 0;
}

.thinking-text {
  flex: 1;
  min-width: 0;
  word-break: break-word;
}

.thinking-duration {
  color: #909399;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.thinking-running {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: #18a058;
  font-size: 12px;
}

/* ===== 输入区 ===== */
.input-area {
  padding: 12px 20px 20px;
  border-top: 1px solid #eee;
  background: #fafafa;
}

.scope-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
  margin-bottom: 8px;
  color: #606266;
  font-size: 12px;
  overflow: hidden;
}

.scope-file {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scope-extra {
  color: #909399;
  white-space: nowrap;
}

.file-select-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.file-prefix {
  display: flex;
  align-items: center;
  gap: 8px;
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
