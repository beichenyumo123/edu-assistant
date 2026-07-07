/**
 * useThinking — Agent 思考步骤处理
 */
export function compactMarkdownText(value, maxLength = 0) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  if (maxLength > 0 && text.length > maxLength) {
    return `${text.slice(0, Math.max(0, maxLength - 3)).trim()}...`
  }
  return text
}

export function inferStepTool(text) {
  if (/(检索|文档片段|知识库|匹配)/.test(text)) return '知识库检索'
  if (/(生成|回答)/.test(text)) return '回答生成'
  if (/(分析|保研)/.test(text)) return '问题分析'
  return 'Agent'
}

export function normalizeThinkingStep(step) {
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

export function normalizeThinkingSteps(steps) {
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

export function formatDuration(ms) {
  if (ms === null || ms === undefined) return ''
  const value = Number(ms)
  if (!Number.isFinite(value)) return ''
  if (value < 1000) return `${Math.max(0, Math.round(value))} ms`
  if (value < 10000) return `${(value / 1000).toFixed(1)} s`
  return `${Math.round(value / 1000)} s`
}

export function formatStepDuration(step) {
  return formatDuration(normalizeThinkingStep(step).elapsed_ms)
}

export function formatMessageDuration(message) {
  const steps = normalizeThinkingSteps(message.agent_steps)
  const lastWithDuration = [...steps].reverse().find((step) => step.elapsed_ms !== null)
  if (lastWithDuration) {
    return `总耗时 ${formatDuration(lastWithDuration.elapsed_ms)}`
  }
  return `${steps.length} 步`
}

export function getMessageSteps(message) {
  return normalizeThinkingSteps(message.agent_steps)
}

export function getStepText(step) {
  return normalizeThinkingStep(step).text
}

export function getStepTool(step) {
  return normalizeThinkingStep(step).tool_name
}
