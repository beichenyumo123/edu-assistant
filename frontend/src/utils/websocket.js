/**
 * WebSocket连接管理器
 * 支持自动重连、流式消息处理
 */
export class ChatWebSocket {
  constructor(userId) {
    this.userId = userId
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnect = 5
    this.listeners = {
      thinking: [],
      token: [],
      done: [],
      error: [],
      meta: [],
    }
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws/chat/${this.userId}`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('✅ WebSocket已连接')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const handlers = this.listeners[data.type] || []
        handlers.forEach((fn) => fn(data))
      } catch (e) {
        console.error('WebSocket消息解析失败:', e)
      }
    }

    this.ws.onclose = () => {
      console.log('🔌 WebSocket已断开')
      this._tryReconnect()
    }

    this.ws.onerror = (err) => {
      console.error('WebSocket错误:', err)
    }
  }

  _tryReconnect() {
    if (this.reconnectAttempts >= this.maxReconnect) return
    this.reconnectAttempts++
    setTimeout(() => {
      console.log(`🔄 重连中... (${this.reconnectAttempts}/${this.maxReconnect})`)
      this.connect()
    }, 2000 * this.reconnectAttempts)
  }

  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback)
    }
  }

  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
      return true
    } else {
      console.warn('WebSocket未连接')
      return false
    }
  }

  close() {
    if (this.ws) {
      this.maxReconnect = 0  // 手动关闭不重连
      this.ws.close()
    }
  }
}
