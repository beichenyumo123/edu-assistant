/**
 * useFiles — 文件管理与知识操作
 */
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { api } from '../utils/api'
import { compactMarkdownText } from './useThinking'

export function useFiles() {
  const nMessage = useMessage()
  const files = ref([])
  const selectedFileIds = ref([])
  const selectionTouched = ref(false)
  const uploading = ref(false)
  const toolLoading = ref('')
  const toolResult = ref(null)

  const readyFiles = computed(() => files.value.filter((file) => file.status === 'ready'))
  const selectedReadyFiles = computed(() => readyFiles.value.filter((file) => selectedFileIds.value.includes(file.id)))
  const selectedScopePreview = computed(() => selectedReadyFiles.value.slice(0, 2))
  const selectedScopeExtraCount = computed(() => Math.max(0, selectedReadyFiles.value.length - selectedScopePreview.value.length))
  const selectedScopeLabel = computed(() => {
    if (readyFiles.value.length === 0) return '暂无可用资料'
    if (selectedReadyFiles.value.length === 0) return '未选择资料'
    if (selectedReadyFiles.value.length === readyFiles.value.length) return `全部资料 (${readyFiles.value.length})`
    return `已选 ${selectedReadyFiles.value.length} 份`
  })

  async function loadFiles() {
    try {
      const res = await api.get('/api/files')
      files.value = res.data.files || []
      syncSelectedFiles()
    } catch { /* ignore */ }
  }

  function syncSelectedFiles() {
    const readyIds = readyFiles.value.map((file) => file.id)
    if (!selectionTouched.value) {
      selectedFileIds.value = [...readyIds]
      return
    }
    selectedFileIds.value = selectedFileIds.value.filter((id) => readyIds.includes(id))
  }

  function isFileSelected(fileId) {
    return selectedFileIds.value.includes(fileId)
  }

  function toggleFileSelection(fileId, checked) {
    selectionTouched.value = true
    if (checked) {
      if (!selectedFileIds.value.includes(fileId)) {
        selectedFileIds.value = [...selectedFileIds.value, fileId]
      }
    } else {
      selectedFileIds.value = selectedFileIds.value.filter((id) => id !== fileId)
    }
  }

  function selectAllReadyFiles() {
    selectionTouched.value = true
    selectedFileIds.value = readyFiles.value.map((file) => file.id)
  }

  function clearSelectedFiles() {
    selectionTouched.value = true
    selectedFileIds.value = []
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

  function downloadKnowledgeMarkdown() {
    if (!toolResult.value?.points?.length) return
    const points = toolResult.value.points
    const groups = groupKnowledgePoints(points)
    const now = new Date().toLocaleString('zh-CN')
    let markdown = `# ${toolResult.value.title}\n\n`
    markdown += `> 导出时间：${now}  |  共 ${points.length} 个知识点  |  ${groups.length} 个模块\n\n`
    markdown += `## 文档概览\n\n`
    markdown += `- 知识点数量：${points.length}\n`
    markdown += `- 模块结构：${groups.map((group) => group.category).join('、')}\n\n`

    for (const [groupIndex, group] of groups.entries()) {
      markdown += `## ${groupIndex + 1}. ${group.category}\n\n`
      for (const [pointIndex, point] of group.points.entries()) {
        const title = compactMarkdownText(point.title) || `知识点 ${point.exportIndex}`
        const description = compactMarkdownText(point.description)
        const keyPoints = asExportList(point.key_points)
        const examples = asExportList(point.examples)
        const excerpts = getPointExcerpts(point)

        markdown += `### ${groupIndex + 1}.${pointIndex + 1} ${title}\n\n`
        if (description) {
          markdown += `${description}\n\n`
        }
        markdown = appendBulletList(markdown, '**复习要点：**', keyPoints)
        markdown = appendBulletList(markdown, '**可套用表达：**', examples)
        if (excerpts.length) {
          markdown += '**原文依据：**\n\n'
          for (const excerpt of excerpts) {
            markdown += `> ${excerpt.replace(/\n/g, '\n> ')}\n>\n`
          }
        }
        markdown += '\n'
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

  return {
    files, selectedFileIds, selectionTouched, uploading, toolLoading, toolResult,
    readyFiles, selectedReadyFiles, selectedScopePreview, selectedScopeExtraCount, selectedScopeLabel,
    loadFiles, syncSelectedFiles, isFileSelected, toggleFileSelection,
    selectAllReadyFiles, clearSelectedFiles,
    handleUpload, deleteFile, summarizeFile, extractKnowledge,
    copyToolResult, downloadKnowledgeMarkdown,
  }
}

// ── 导出工具函数（从 ChatView.vue 提取） ──

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
    const category = compactMarkdownText(point.category) || '核心知识点'
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
