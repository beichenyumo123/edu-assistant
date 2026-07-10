<template>
  <div class="chat-layout">
    <!-- ===== 左侧边栏 ===== -->
    <aside class="sidebar">
      <!-- Logo -->
      <div class="sidebar-header" @click="handleNewChat">
        <span class="logo">OA</span>
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
        <button class="profile-btn" type="button" @click="openProfileDrawer">
          <span class="profile-avatar">{{ userInitials }}</span>
          <span class="profile-meta">
            <strong>{{ authStore.user?.username || '用户' }}</strong>
            <small>{{ profileRoleLabel }}</small>
          </span>
        </button>
        <button class="logout-btn" type="button" @click="handleLogout">
          <n-icon size="18"><log-out-outline /></n-icon>
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <!-- ===== 右侧主区域 ===== -->
    <main class="main-area">
      <!-- 顶部助手栏 -->
      <header class="chat-header">
        <div class="assistant-title">
          <span class="assistant-icon">OA</span>
          <div>
            <strong>入职培训助手</strong>
            <span>基于已选企业资料检索回答</span>
          </div>
        </div>
        <div class="header-actions">
          <n-button text @click="openMemoryDrawer">
            <n-icon size="20"><sparkles-outline /></n-icon>
            AI 记忆
          </n-button>
          <n-button text @click="openKnowledgeBase">
            <n-icon size="20"><folder-open-outline /></n-icon>
            企业知识库
          </n-button>
        </div>
      </header>

      <!-- 消息区域 -->
      <div class="message-area" ref="messageAreaRef">
        <!-- 空状态：预设问题卡片 -->
        <div v-if="messages.length === 0 && !isThinking" class="welcome">
          <div class="welcome-copy">
            <span class="welcome-kicker">Enterprise onboarding workspace</span>
            <h2>让入职问题带着资料回答</h2>
            <p>选择员工手册、制度流程或岗位培训资料后，系统会优先检索已选范围，并把可追溯来源带回回答中。</p>
          </div>
          <div class="welcome-actions">
            <n-button type="primary" round size="large" @click="openKnowledgeBase">
              <n-icon><folder-open-outline /></n-icon>
              选择培训资料
            </n-button>
          </div>
          <div class="preset-cards">
            <div v-for="q in presetQuestions" :key="q" class="preset-card" @click="sendMessage(q)">
              {{ q }}
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(msg, idx) in messages" :key="idx" class="msg-row" :class="msg.role">
          <div class="msg-avatar">{{ msg.role === 'user' ? 'ME' : 'AI' }}</div>
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
    <n-drawer v-model:show="showFileDrawer" :width="460" placement="right">
      <n-drawer-content title="企业培训资料库">
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
                <n-tag v-if="f.is_default" type="info" size="small">系统默认</n-tag>
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
                <n-button text type="error" :disabled="f.is_default" @click="deleteFile(f.id)"><n-icon><trash-outline /></n-icon></n-button>
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

    <!-- ===== AI 记忆抽屉 ===== -->
    <n-drawer v-model:show="showMemoryDrawer" :width="420" placement="right">
      <n-drawer-content title="AI 记忆">
        <n-spin :show="memoryLoading">
          <div class="memory-panel">
            <section class="memory-hero">
              <div class="memory-symbol">
                <n-icon size="22"><sparkles-outline /></n-icon>
              </div>
              <div>
                <p>Personalized Context</p>
                <h3>个性化使用画像</h3>
              </div>
            </section>

            <div class="memory-stats">
              <div class="memory-stat">
                <span>记录问题</span>
                <strong>{{ userMemory?.question_count || 0 }}</strong>
              </div>
              <div class="memory-stat">
                <span>记忆状态</span>
                <strong>{{ userMemory?.memory_enabled === false ? '已关闭' : '已开启' }}</strong>
              </div>
            </div>

            <div class="memory-section memory-settings">
              <span class="memory-label">用户可控设置</span>
              <div class="memory-setting-row">
                <div>
                  <strong>启用 AI 记忆</strong>
                  <small>开启后系统会记录稳定偏好并用于后续回答</small>
                </div>
                <n-switch v-model:value="memoryForm.memory_enabled" />
              </div>
              <n-form class="memory-form" label-placement="top">
                <n-form-item label="回答风格">
                  <n-select
                    v-model:value="memoryForm.preferred_answer_style"
                    :options="answerStyleOptions"
                    :disabled="!memoryForm.memory_enabled"
                  />
                </n-form-item>
                <n-form-item label="沟通语气">
                  <n-select
                    v-model:value="memoryForm.communication_tone"
                    :options="communicationToneOptions"
                    :disabled="!memoryForm.memory_enabled"
                  />
                </n-form-item>
                <n-button type="primary" block :loading="memorySaving" @click="saveMemorySettings">
                  保存记忆设置
                </n-button>
              </n-form>
            </div>

            <div class="memory-section">
              <span class="memory-label">基础画像</span>
              <div class="memory-profile">
                <div>
                  <small>部门</small>
                  <strong>{{ userMemory?.department || '未填写' }}</strong>
                </div>
                <div>
                  <small>岗位</small>
                  <strong>{{ userMemory?.role || '未填写' }}</strong>
                </div>
                <div>
                  <small>沟通语气</small>
                  <strong>{{ userMemory?.communication_tone || '专业清晰' }}</strong>
                </div>
              </div>
            </div>

            <div class="memory-section">
              <span class="memory-label">常问主题</span>
              <div v-if="memoryTopics.length" class="memory-tags">
                <span v-for="topic in memoryTopics" :key="topic.name" class="memory-tag">
                  {{ topic.name }} · {{ topic.count }}
                </span>
              </div>
              <n-empty v-else description="暂无主题记忆" size="small" />
            </div>

            <div class="memory-section">
              <span class="memory-label">常用资料</span>
              <div v-if="memoryDocuments.length" class="memory-docs">
                <div v-for="doc in memoryDocuments" :key="doc.name" class="memory-doc">
                  <span>{{ doc.name }}</span>
                  <small>{{ doc.count }} 次</small>
                </div>
              </div>
              <n-empty v-else description="暂无资料偏好" size="small" />
            </div>

            <div class="memory-section" v-if="userMemory?.last_question">
              <span class="memory-label">最近一次问题</span>
              <p class="memory-last-question">{{ userMemory.last_question }}</p>
            </div>

            <div class="memory-actions">
              <n-button block secondary :disabled="!userMemory?.question_count" @click="clearMemory">
                清空 AI 记忆
              </n-button>
            </div>
          </div>
        </n-spin>
      </n-drawer-content>
    </n-drawer>

    <!-- ===== 个人信息抽屉 ===== -->
    <n-drawer v-model:show="showProfileDrawer" :width="420" placement="right">
      <n-drawer-content title="个人信息">
        <div class="profile-panel">
          <section class="profile-hero">
            <div class="profile-hero-avatar">{{ userInitials }}</div>
            <div>
              <p>Account Profile</p>
              <h3>{{ authStore.user?.username || '用户' }}</h3>
              <span>{{ profileRoleLabel }}</span>
            </div>
          </section>

          <n-form class="profile-form" @submit.prevent="saveProfile">
            <n-form-item label="用户名">
              <n-input v-model:value="profileForm.username" size="large" placeholder="请输入用户名" clearable />
            </n-form-item>
            <n-form-item label="邮箱">
              <n-input v-model:value="profileForm.email" size="large" placeholder="请输入邮箱" clearable />
            </n-form-item>
            <div class="profile-form-row">
              <n-form-item label="部门">
                <n-input v-model:value="profileForm.grade" size="large" placeholder="部门" clearable />
              </n-form-item>
              <n-form-item label="岗位">
                <n-input v-model:value="profileForm.major" size="large" placeholder="岗位" clearable />
              </n-form-item>
            </div>
            <n-button type="primary" block size="large" :loading="profileSaving" @click="saveProfile">
              保存修改
            </n-button>
          </n-form>
        </div>
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
  SparklesOutline,
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
const showMemoryDrawer = ref(false)
const showProfileDrawer = ref(false)
const memoryLoading = ref(false)
const memorySaving = ref(false)
const userMemory = ref(null)
const memoryForm = ref({
  memory_enabled: true,
  preferred_answer_style: '结构化',
  communication_tone: '专业清晰',
})
const profileSaving = ref(false)
const profileForm = ref({ username: '', email: '', grade: '', major: '' })
const uploading = ref(false)
const toolLoading = ref('')
const toolResult = ref(null)
const messageAreaRef = ref(null)
const hasInitializedFileSelection = ref(false)

let ws = null

const defaultOnboardingDocName = '欣旺达-劳动人事管理全流程手册.pdf'
const answerStyleOptions = [
  { label: '结构化', value: '结构化' },
  { label: '简洁', value: '简洁' },
  { label: '详细', value: '详细' },
  { label: '步骤化', value: '步骤化' },
  { label: '表格化', value: '表格化' },
]
const communicationToneOptions = [
  { label: '专业清晰', value: '专业清晰' },
  { label: '直接高效', value: '直接高效' },
  { label: '耐心详细', value: '耐心详细' },
  { label: '结构清晰', value: '结构清晰' },
]

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
const memoryTopics = computed(() => userMemory.value?.top_topics || [])
const memoryDocuments = computed(() => userMemory.value?.document_preferences || [])
const userInitials = computed(() => {
  const name = authStore.user?.username || 'OA'
  return name.slice(0, 2).toUpperCase()
})
const profileRoleLabel = computed(() => {
  const department = authStore.user?.grade
  const role = authStore.user?.major
  if (department && role) return `${department} · ${role}`
  return department || role || '未设置部门/岗位'
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
    if (showMemoryDrawer.value) {
      loadMemory()
    }
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
    if (showMemoryDrawer.value) {
      await loadMemory()
    }
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

async function loadMemory() {
  memoryLoading.value = true
  try {
    const res = await api.get('/api/memory/me')
    userMemory.value = res.data.memory
    syncMemoryForm()
  } catch (e) {
    nMessage.error(e.response?.data?.detail || 'AI记忆加载失败')
  } finally {
    memoryLoading.value = false
  }
}

async function openMemoryDrawer() {
  showMemoryDrawer.value = true
  await loadMemory()
}

function syncMemoryForm() {
  const memory = userMemory.value || {}
  memoryForm.value = {
    memory_enabled: memory.memory_enabled !== false,
    preferred_answer_style: memory.preferred_answer_style || '结构化',
    communication_tone: memory.communication_tone || '专业清晰',
  }
}

async function saveMemorySettings() {
  memorySaving.value = true
  try {
    const res = await api.patch('/api/memory/me', {
      memory_enabled: memoryForm.value.memory_enabled,
      preferred_answer_style: memoryForm.value.preferred_answer_style,
      communication_tone: memoryForm.value.communication_tone,
    })
    userMemory.value = res.data.memory
    syncMemoryForm()
    nMessage.success('AI记忆设置已保存')
  } catch (e) {
    nMessage.error(e.response?.data?.detail || 'AI记忆设置保存失败')
  } finally {
    memorySaving.value = false
  }
}

function openProfileDrawer() {
  const user = authStore.user || {}
  profileForm.value = {
    username: user.username || '',
    email: user.email || '',
    grade: user.grade || '',
    major: user.major || '',
  }
  showProfileDrawer.value = true
}

async function saveProfile() {
  const payload = {
    username: profileForm.value.username.trim(),
    email: profileForm.value.email.trim(),
    grade: profileForm.value.grade.trim(),
    major: profileForm.value.major.trim(),
  }
  if (!payload.username || !payload.email) {
    nMessage.warning('请填写用户名和邮箱')
    return
  }
  profileSaving.value = true
  try {
    await authStore.updateProfile(payload)
    nMessage.success('个人信息已更新')
    showProfileDrawer.value = false
  } catch (e) {
    nMessage.error(e.response?.data?.detail || '个人信息更新失败')
  } finally {
    profileSaving.value = false
  }
}

async function clearMemory() {
  memoryLoading.value = true
  try {
    const res = await api.delete('/api/memory/me')
    userMemory.value = res.data.memory
    syncMemoryForm()
    nMessage.success('AI记忆已清空')
  } catch (e) {
    nMessage.error(e.response?.data?.detail || 'AI记忆清空失败')
  } finally {
    memoryLoading.value = false
  }
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
  if (!hasInitializedFileSelection.value) {
    const defaultReadyIds = readyFiles.value
      .filter((file) => file.is_default || file.is_shared)
      .map((file) => file.id)
    if (selectedFileIds.value.length === 0 && defaultReadyIds.length > 0) {
      selectedFileIds.value = defaultReadyIds
    }
    hasInitializedFileSelection.value = true
  }
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
  return md
    .render(String(text))
    .replace(/&lt;br\s*\/?&gt;/gi, '<br>')
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
  gap: 14px;
  height: 100vh;
  padding: 14px;
  overflow: hidden;
  color: #111827;
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.96) 0%, rgba(237, 242, 247, 0.96) 100%),
    #f3f5f7;
}

/* ===== 左侧边栏 ===== */
.sidebar {
  display: flex;
  flex-direction: column;
  width: 252px;
  min-width: 252px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(198, 210, 224, 0.72);
  border-radius: 24px;
  box-shadow: 0 28px 70px rgba(44, 55, 73, 0.12);
  backdrop-filter: blur(28px);
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 78px;
  padding: 18px 18px 14px;
  color: #111827;
  cursor: pointer;
}

.sidebar-header .logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  color: #fff;
  background: #111827;
  border-radius: 12px;
  box-shadow: 0 16px 34px rgba(17, 24, 39, 0.18);
  font-size: 15px;
  font-weight: 800;
  line-height: 1;
}

.sidebar-header .brand {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: 0;
  white-space: nowrap;
}

.sidebar-actions {
  padding: 0 16px 16px;
}

.new-chat-btn {
  width: 100%;
  height: 40px;
  justify-content: center;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 700;
  transition: transform 0.32s ease-in-out, box-shadow 0.32s ease-in-out, background 0.32s ease-in-out;
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 36px rgba(37, 99, 235, 0.12);
}

.conv-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 2px 10px 14px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 44px;
  padding: 10px 12px;
  margin-bottom: 8px;
  color: #344054;
  border: 1px solid transparent;
  border-radius: 14px;
  cursor: pointer;
  font-size: 15px;
  transition: transform 0.32s ease-in-out, background 0.32s ease-in-out, border-color 0.32s ease-in-out, color 0.32s ease-in-out;
}

.conv-item:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.76);
  border-color: rgba(198, 210, 224, 0.76);
}

.conv-item.active {
  color: #0f4cb5;
  background: rgba(239, 246, 255, 0.84);
  border-color: rgba(147, 197, 253, 0.72);
}

.conv-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.32s ease-in-out;
}

.conv-item:hover .delete-btn {
  opacity: 1;
}

.sidebar-footer {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid rgba(198, 210, 224, 0.58);
}

.profile-btn {
  display: flex;
  align-items: center;
  gap: 11px;
  width: 100%;
  min-height: 58px;
  padding: 8px 12px;
  color: #111827;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(198, 210, 224, 0.58);
  border-radius: 18px;
  cursor: pointer;
  text-align: left;
  transition: transform 0.32s ease-in-out, background 0.32s ease-in-out, border-color 0.32s ease-in-out, box-shadow 0.32s ease-in-out;
}

.profile-btn:hover {
  background: rgba(255, 255, 255, 0.84);
  border-color: rgba(152, 162, 179, 0.54);
  box-shadow: 0 16px 34px rgba(44, 55, 73, 0.08);
  transform: translateY(-1px);
}

.profile-avatar {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  color: #fff;
  background: #111827;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 800;
}

.profile-meta {
  min-width: 0;
}

.profile-meta strong,
.profile-meta small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-meta strong {
  color: #111827;
  font-size: 15px;
  font-weight: 800;
  line-height: 1.25;
}

.profile-meta small {
  margin-top: 3px;
  color: #667085;
  font-size: 12px;
  line-height: 1.3;
}

.logout-btn {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  width: 100%;
  min-height: 42px;
  padding: 0 14px;
  color: #667085;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(198, 210, 224, 0.48);
  border-radius: 999px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 700;
  transition: transform 0.32s ease-in-out, color 0.32s ease-in-out, background 0.32s ease-in-out, border-color 0.32s ease-in-out, box-shadow 0.32s ease-in-out;
}

.logout-btn:hover {
  color: #111827;
  background: rgba(255, 255, 255, 0.78);
  border-color: rgba(152, 162, 179, 0.54);
  box-shadow: 0 16px 34px rgba(44, 55, 73, 0.08);
  transform: translateY(-1px);
}

.logout-btn:active {
  transform: translateY(0);
}

/* ===== 主区域 ===== */
.main-area {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(198, 210, 224, 0.7);
  border-radius: 26px;
  box-shadow: 0 28px 70px rgba(44, 55, 73, 0.1);
  backdrop-filter: blur(28px);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 82px;
  padding: 18px clamp(22px, 3vw, 38px);
  background: rgba(255, 255, 255, 0.62);
  border-bottom: 1px solid rgba(198, 210, 224, 0.56);
  box-shadow: 0 1px 0 rgba(37, 99, 235, 0.08);
  backdrop-filter: blur(24px);
}

.assistant-title {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  color: #111827;
}

.assistant-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  color: #111827;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(198, 210, 224, 0.72);
  border-radius: 15px;
  font-size: 15px;
  font-weight: 800;
}

.assistant-title strong {
  display: block;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.25;
}

.assistant-title span:last-child {
  display: block;
  margin-top: 4px;
  color: #667085;
  font-size: 14px;
  line-height: 1.45;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.header-actions :deep(.n-button) {
  min-height: 40px;
  padding: 0 12px;
  border-radius: 999px;
  font-weight: 700;
  transition: background 0.32s ease-in-out, transform 0.32s ease-in-out, box-shadow 0.32s ease-in-out;
}

.header-actions :deep(.n-button:hover) {
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 14px 30px rgba(44, 55, 73, 0.08);
  transform: translateY(-1px);
}

/* ===== 消息区 ===== */
.message-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: clamp(28px, 4vw, 54px);
  scroll-behavior: smooth;
}

.welcome {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(280px, 0.78fr);
  gap: clamp(32px, 5vw, 70px);
  width: min(1080px, 100%);
  margin: 0 auto;
  padding-top: clamp(20px, 8vh, 86px);
  text-align: left;
  animation: fade-up 0.5s ease-in-out both;
}

.welcome-copy {
  max-width: 720px;
}

.welcome-kicker {
  display: inline-flex;
  margin-bottom: 22px;
  color: #667085;
  font-size: 14px;
  font-weight: 700;
}

.welcome h2 {
  max-width: 720px;
  margin: 0;
  color: #0b1220;
  font-size: clamp(44px, 6vw, 76px);
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: 0;
}

.welcome p {
  max-width: 620px;
  margin: 28px 0 0;
  color: #4b5563;
  font-size: 18px;
  font-weight: 300;
  line-height: 1.85;
}

.welcome-actions {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding-top: 20px;
}

.welcome-actions :deep(.n-button) {
  min-width: 176px;
  height: 52px;
  font-size: 16px;
  font-weight: 800;
  transition: transform 0.32s ease-in-out, box-shadow 0.32s ease-in-out;
}

.welcome-actions :deep(.n-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 22px 48px rgba(37, 99, 235, 0.18);
}

.preset-cards {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr 1fr;
  gap: 18px;
  width: min(980px, 100%);
  margin-top: 10px;
}

.preset-card {
  min-height: 118px;
  padding: 24px;
  color: #1f2937;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.82);
  border-radius: 16px;
  box-shadow: 0 24px 60px rgba(44, 55, 73, 0.08);
  cursor: pointer;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.55;
  transition: transform 0.36s ease-in-out, background 0.36s ease-in-out, border-color 0.36s ease-in-out, box-shadow 0.36s ease-in-out;
  backdrop-filter: blur(22px);
}

.preset-card:nth-child(2),
.preset-card:nth-child(5) {
  transform: translateY(18px);
}

.preset-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.86);
  border-color: rgba(37, 99, 235, 0.26);
  box-shadow: 0 30px 70px rgba(44, 55, 73, 0.12);
}

.preset-card:nth-child(2):hover,
.preset-card:nth-child(5):hover {
  transform: translateY(10px);
}

/* 消息行 */
.msg-row {
  display: flex;
  gap: 14px;
  width: min(1120px, 100%);
  margin: 0 auto 24px;
  animation: fade-up 0.34s ease-in-out both;
}

.msg-row.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  color: #475467;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(198, 210, 224, 0.68);
  border-radius: 14px;
  box-shadow: 0 14px 32px rgba(44, 55, 73, 0.06);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
}

.msg-row.user .msg-avatar {
  color: #fff;
  background: #111827;
  border-color: #111827;
}

.msg-bubble {
  width: fit-content;
  max-width: min(980px, 88%);
  padding: 18px 20px;
  border-radius: 20px;
  line-height: 1.72;
  box-shadow: 0 18px 42px rgba(44, 55, 73, 0.07);
}

.msg-row.user .msg-bubble {
  color: #fff;
  background: #111827;
}

.msg-row.assistant .msg-bubble {
  position: relative;
  overflow: hidden;
  color: #1f2937;
  padding: 28px 32px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(250, 252, 255, 0.78));
  border: 1px solid rgba(208, 217, 229, 0.74);
  border-radius: 24px;
  box-shadow:
    0 24px 70px rgba(44, 55, 73, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(22px);
}

.msg-row.assistant .msg-bubble::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.7), rgba(21, 153, 87, 0.32));
}

.msg-content {
  font-size: 15px;
  word-break: break-word;
}

.msg-row.user .msg-content {
  white-space: pre-wrap;
}

.msg-row.assistant .msg-content {
  color: #273449;
  font-size: 16px;
  line-height: 1.82;
  white-space: normal;
}

.msg-row.assistant .msg-content :deep(h1),
.msg-row.assistant .msg-content :deep(h2),
.msg-row.assistant .msg-content :deep(h3) {
  margin: 26px 0 12px;
  color: #111827;
  font-weight: 800;
  line-height: 1.28;
}

.msg-row.assistant .msg-content :deep(h1:first-child),
.msg-row.assistant .msg-content :deep(h2:first-child),
.msg-row.assistant .msg-content :deep(h3:first-child) {
  margin-top: 0;
}

.msg-row.assistant .msg-content :deep(h1) {
  font-size: 24px;
}

.msg-row.assistant .msg-content :deep(h2) {
  font-size: 22px;
}

.msg-row.assistant .msg-content :deep(h3) {
  font-size: 19px;
}

.msg-row.assistant .msg-content :deep(p),
.msg-row.assistant .msg-content :deep(li) {
  color: #344054;
}

.msg-row.assistant .msg-content :deep(p) {
  margin: 0 0 14px;
}

.msg-row.assistant .msg-content :deep(p:last-child) {
  margin-bottom: 0;
}

.msg-row.assistant .msg-content :deep(ol),
.msg-row.assistant .msg-content :deep(ul) {
  margin: 14px 0 20px;
  padding-left: 1.35em;
}

.msg-row.assistant .msg-content :deep(li) {
  margin: 8px 0;
  padding-left: 6px;
  line-height: 1.78;
}

.msg-row.assistant .msg-content :deep(li::marker) {
  color: #667085;
  font-weight: 700;
}

.msg-row.assistant .msg-content :deep(li > p) {
  margin: 0 0 6px;
}

.msg-row.assistant .msg-content :deep(strong) {
  color: #1d2939;
  font-weight: 800;
}

.msg-row.assistant .msg-content :deep(blockquote) {
  margin: 16px 0;
  padding: 12px 16px;
  color: #475467;
  background: rgba(248, 250, 252, 0.82);
  border-left: 3px solid rgba(37, 99, 235, 0.32);
  border-radius: 12px;
}

.msg-row.assistant .msg-content :deep(table) {
  display: block;
  width: 100%;
  max-width: 100%;
  margin: 20px 0 24px;
  overflow-x: auto;
  overflow-y: hidden;
  color: #273449;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(198, 210, 224, 0.74);
  border-radius: 16px;
  border-spacing: 0;
  border-collapse: separate;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78);
}

.msg-row.assistant .msg-content :deep(thead) {
  background: rgba(248, 250, 252, 0.96);
}

.msg-row.assistant .msg-content :deep(th),
.msg-row.assistant .msg-content :deep(td) {
  min-width: 148px;
  padding: 14px 16px;
  vertical-align: top;
  border-right: 1px solid rgba(198, 210, 224, 0.66);
  border-bottom: 1px solid rgba(198, 210, 224, 0.66);
  font-size: 15px;
  line-height: 1.72;
  overflow-wrap: break-word;
  word-break: normal;
}

.msg-row.assistant .msg-content :deep(th:first-child),
.msg-row.assistant .msg-content :deep(td:first-child) {
  min-width: 96px;
}

.msg-row.assistant .msg-content :deep(th:last-child),
.msg-row.assistant .msg-content :deep(td:last-child) {
  border-right: 0;
}

.msg-row.assistant .msg-content :deep(tr:last-child td) {
  border-bottom: 0;
}

.msg-row.assistant .msg-content :deep(th) {
  color: #111827;
  font-weight: 800;
  text-align: left;
  white-space: nowrap;
}

.msg-row.assistant .msg-content :deep(td strong) {
  display: inline;
}

.msg-row.assistant .msg-content :deep(code) {
  padding: 2px 6px;
  background: rgba(17, 24, 39, 0.07);
  border-radius: 6px;
  font-size: 14px;
}

.msg-row.assistant .msg-content :deep(pre) {
  padding: 16px;
  overflow-x: auto;
  color: #d1d5db;
  background: #111827;
  border-radius: 14px;
}

.msg-row.assistant .msg-content :deep(pre code) {
  color: inherit;
  background: transparent;
}

.msg-sources,
.msg-evaluation {
  margin-top: 14px;
  font-size: 14px;
}

.msg-sources :deep(.n-collapse),
.msg-evaluation :deep(.n-collapse),
.msg-thinking :deep(.n-collapse) {
  --n-title-font-size: 14px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
  gap: 10px;
}

.metric-item {
  padding: 12px;
  background: rgba(248, 250, 252, 0.82);
  border: 1px solid rgba(198, 210, 224, 0.68);
  border-radius: 14px;
}

.metric-label {
  display: block;
  margin-bottom: 8px;
  color: #667085;
  font-size: 14px;
}

.metric-item strong {
  font-size: 20px;
  font-weight: 800;
}

.metric-good { color: #159957; }
.metric-warn { color: #d97706; }
.metric-bad { color: #d92d20; }

.metric-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-top: 14px;
  color: #667085;
  font-size: 14px;
}

.metric-notes {
  margin-top: 12px;
  color: #667085;
  line-height: 1.65;
}

.source-item {
  padding: 8px 0;
  color: #667085;
  font-size: 14px;
  line-height: 1.65;
}

.msg-thinking {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(198, 210, 224, 0.58);
  font-size: 14px;
}

.thinking-step {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
  padding: 4px 0;
  color: #4b5563;
  font-size: 14px;
}

.thinking-text {
  flex: 1;
  min-width: 0;
  word-break: break-word;
}

.thinking-duration {
  color: #98a2b3;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.thinking-running {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  color: #159957;
  font-size: 14px;
}

/* ===== 输入区 ===== */
.input-area {
  padding: 18px clamp(22px, 3vw, 38px) 26px;
  background: rgba(255, 255, 255, 0.68);
  border-top: 1px solid rgba(198, 210, 224, 0.56);
  backdrop-filter: blur(24px);
}

.scope-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 32px;
  margin-bottom: 12px;
  overflow: hidden;
  color: #667085;
  font-size: 14px;
}

.scope-file {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scope-extra {
  color: #98a2b3;
  white-space: nowrap;
}

.input-area :deep(.n-input-group) {
  display: flex;
  gap: 12px;
}

.input-area :deep(.n-input) {
  border-radius: 20px;
  transition: box-shadow 0.32s ease-in-out, transform 0.32s ease-in-out;
}

.input-area :deep(.n-input:hover),
.input-area :deep(.n-input.n-input--focus) {
  box-shadow: 0 18px 44px rgba(44, 55, 73, 0.08);
}

.input-area :deep(.n-button) {
  min-width: 54px;
  height: auto;
  border-radius: 18px;
  transition: transform 0.32s ease-in-out, box-shadow 0.32s ease-in-out;
}

.input-area :deep(.n-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 16px 36px rgba(37, 99, 235, 0.14);
}

.file-select-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.file-prefix {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tool-markdown {
  max-height: 360px;
  overflow-y: auto;
  line-height: 1.8;
}

.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
}

.knowledge-card {
  cursor: pointer;
  transition: transform 0.32s ease-in-out, box-shadow 0.32s ease-in-out;
}

.knowledge-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 44px rgba(44, 55, 73, 0.1);
}

/* ===== AI 记忆 ===== */
.memory-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  color: #111827;
}

.memory-hero {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.86));
  border: 1px solid rgba(198, 210, 224, 0.62);
  border-radius: 22px;
  box-shadow: 0 22px 52px rgba(44, 55, 73, 0.08);
}

.memory-symbol {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  color: #fff;
  background: #111827;
  border-radius: 16px;
  box-shadow: 0 16px 34px rgba(17, 24, 39, 0.16);
}

.memory-hero p {
  margin: 0 0 4px;
  color: #667085;
  font-size: 14px;
  font-weight: 700;
}

.memory-hero h3 {
  margin: 0;
  color: #111827;
  font-size: 22px;
  font-weight: 800;
  line-height: 1.2;
}

.memory-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.memory-stat,
.memory-section {
  padding: 18px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(198, 210, 224, 0.58);
  border-radius: 18px;
}

.memory-stat span,
.memory-label {
  display: block;
  margin-bottom: 8px;
  color: #667085;
  font-size: 14px;
  font-weight: 700;
}

.memory-stat strong {
  color: #111827;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.1;
}

.memory-settings {
  display: grid;
  gap: 16px;
}

.memory-setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 0;
  border-bottom: 1px solid rgba(198, 210, 224, 0.52);
}

.memory-setting-row strong,
.memory-setting-row small {
  display: block;
}

.memory-setting-row strong {
  color: #111827;
  font-size: 15px;
  font-weight: 800;
}

.memory-setting-row small {
  margin-top: 4px;
  color: #667085;
  font-size: 13px;
  line-height: 1.45;
}

.memory-form {
  display: grid;
  gap: 2px;
}

.memory-form :deep(.n-select) {
  border-radius: 14px;
}

.memory-form :deep(.n-button) {
  min-height: 44px;
  margin-top: 4px;
  border-radius: 999px;
  font-weight: 800;
}

.memory-profile {
  display: grid;
  gap: 12px;
}

.memory-profile div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(198, 210, 224, 0.52);
}

.memory-profile div:last-child {
  border-bottom: 0;
}

.memory-profile small {
  color: #667085;
  font-size: 14px;
}

.memory-profile strong {
  color: #1d2939;
  font-size: 15px;
  font-weight: 800;
  text-align: right;
}

.memory-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.memory-tag {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  color: #1d2939;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(198, 210, 224, 0.58);
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
}

.memory-docs {
  display: grid;
  gap: 10px;
}

.memory-doc {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(198, 210, 224, 0.52);
}

.memory-doc:last-child {
  border-bottom: 0;
}

.memory-doc span {
  min-width: 0;
  overflow: hidden;
  color: #1d2939;
  font-size: 14px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.memory-doc small {
  flex-shrink: 0;
  color: #667085;
  font-size: 13px;
}

.memory-last-question {
  margin: 0;
  color: #344054;
  font-size: 15px;
  line-height: 1.7;
}

.memory-actions {
  padding-top: 4px;
}

.memory-actions :deep(.n-button) {
  min-height: 44px;
  border-radius: 999px;
  font-weight: 800;
}

/* ===== 个人信息 ===== */
.profile-panel {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.profile-hero {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.86));
  border: 1px solid rgba(198, 210, 224, 0.62);
  border-radius: 22px;
  box-shadow: 0 22px 52px rgba(44, 55, 73, 0.08);
}

.profile-hero-avatar {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  flex-shrink: 0;
  color: #fff;
  background: #111827;
  border-radius: 18px;
  box-shadow: 0 18px 36px rgba(17, 24, 39, 0.16);
  font-size: 17px;
  font-weight: 800;
}

.profile-hero p {
  margin: 0 0 4px;
  color: #667085;
  font-size: 14px;
  font-weight: 700;
}

.profile-hero h3 {
  margin: 0;
  color: #111827;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.18;
}

.profile-hero span {
  display: block;
  margin-top: 6px;
  color: #667085;
  font-size: 14px;
}

.profile-form {
  padding: 20px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(198, 210, 224, 0.58);
  border-radius: 20px;
}

.profile-form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-form :deep(.n-input) {
  border-radius: 14px;
}

.profile-form :deep(.n-button) {
  min-height: 46px;
  border-radius: 999px;
  font-weight: 800;
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1020px) {
  .chat-layout {
    flex-direction: column;
    gap: 12px;
    height: 100dvh;
    padding: 10px;
  }

  .sidebar {
    width: 100%;
    min-width: 0;
    max-height: 238px;
    border-radius: 24px;
  }

  .sidebar-header {
    min-height: 72px;
    padding: 16px 18px 12px;
  }

  .sidebar-actions {
    padding: 0 18px 14px;
  }

  .conv-list {
    display: flex;
    flex: none;
    gap: 10px;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 0 18px 16px;
  }

  .conv-item {
    min-width: 210px;
    margin-bottom: 0;
  }

  .sidebar-footer {
    display: none;
  }

  .main-area {
    min-height: 0;
    border-radius: 24px;
  }

  .chat-header {
    min-height: 72px;
    padding: 14px 18px;
  }

  .header-actions {
    gap: 6px;
  }

  .header-actions :deep(.n-button) {
    padding: 0 8px;
  }

  .message-area {
    padding: 26px 18px;
  }

  .welcome {
    grid-template-columns: 1fr;
    gap: 24px;
    padding-top: 8px;
  }

  .welcome-actions {
    justify-content: flex-start;
    padding-top: 0;
  }

  .preset-cards {
    grid-template-columns: 1fr;
  }

  .preset-card,
  .preset-card:nth-child(2),
  .preset-card:nth-child(5),
  .preset-card:hover,
  .preset-card:nth-child(2):hover,
  .preset-card:nth-child(5):hover {
    min-height: auto;
    transform: none;
  }

  .msg-bubble {
    max-width: calc(100vw - 92px);
  }

  .scope-bar {
    flex-wrap: wrap;
    overflow: visible;
  }

  .input-area {
    padding: 14px 16px 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
</style>
