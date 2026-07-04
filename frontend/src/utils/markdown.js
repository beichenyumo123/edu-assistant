import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// Markdown渲染器（支持代码高亮）
export const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch {}
    }
    return code
  },
})
