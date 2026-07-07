/**
 * useEvaluation — RAG 评价指标处理
 */
export function normalizeEvaluation(evaluation) {
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

export function formatMetricPercent(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return `${Math.round(number * 100)}%`
}

export function metricClass(value, reverse = false) {
  const number = Number(value)
  if (!Number.isFinite(number)) return ''
  const good = reverse ? number <= 0.25 : number >= 0.7
  const bad = reverse ? number >= 0.55 : number < 0.4
  if (good) return 'metric-good'
  if (bad) return 'metric-bad'
  return 'metric-warn'
}

export function getEvaluationSummary(evaluation) {
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
