<template>
  <div class="message-area" ref="areaRef">
    <WelcomeCards
      v-if="messages.length === 0 && !isThinking"
      :title="welcomeTitle"
      :subtitle="welcomeSubtitle"
      :questions="presetQuestions"
      @send="$emit('send', $event)"
    />
    <MessageBubble
      v-for="(msg, idx) in messages"
      :key="idx"
      :message="msg"
      :is-active="activeIndex === idx"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import WelcomeCards from './WelcomeCards.vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  isThinking: { type: Boolean, default: false },
  agentType: { type: String, default: 'edu' },
})

defineEmits(['send'])

const areaRef = ref(null)

const eduPresets = [
  '帮我总结这篇课文的核心内容', '提取这一章节的重要知识点',
  '这篇文章的结构是什么？', '用简单的话解释这个概念',
  '给我出几道关于这个知识点的题', '帮我制定一个学习计划',
]
const baoyanPresets = [
  '保研需要准备哪些材料？', '计算机专业有哪些好学校推荐？',
  '预推免和夏令营有什么区别？', '如何选择导师？',
  '保研面试一般问什么？', '我的条件能保什么层次的学校？',
]
const presetQuestions = computed(() => props.agentType === 'edu' ? eduPresets : baoyanPresets)
const welcomeTitle = computed(() => props.agentType === 'edu' ? '📖 你好，我是教育助手' : '🎓 你好，我是保研助手')
const welcomeSubtitle = computed(() =>
  props.agentType === 'edu'
    ? '上传学习资料或直接提问，我会基于你的资料帮你学习'
    : '关于保研的任何问题，我都可以帮你解答'
)

const activeIndex = computed(() =>
  props.isThinking ? props.messages.length - 1 : -1
)

defineExpose({ areaRef })
</script>

<style scoped>
.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
</style>
