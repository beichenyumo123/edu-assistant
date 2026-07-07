import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import router from './router'
import App from './App.vue'

// 动物森友会设计系统 — CSS 变量 + 字体
import 'animal-island-vue/style'
// Naive UI 组件 CSS 修正
import './theme/naiveOverrides.css'

const app = createApp(App)
app.use(naive)
app.use(createPinia())
app.use(router)
app.mount('#app')
