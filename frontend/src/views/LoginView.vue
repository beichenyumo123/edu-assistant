<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo & 标题 -->
      <div class="login-header">
        <div class="logo">📚</div>
        <h1>EduAssistant</h1>
        <p>AI驱动的智能学习助手</p>
      </div>

      <!-- Tab切换：登录 / 注册 -->
      <div class="login-tabs">
        <div class="tab-bar">
          <button
            :class="['tab-btn', { active: activeTab === 'login' }]"
            @click="activeTab = 'login'"
          >
            登录
          </button>
          <button
            :class="['tab-btn', { active: activeTab === 'register' }]"
            @click="activeTab = 'register'"
          >
            注册
          </button>
        </div>
      </div>

      <!-- 登录表单 -->
      <n-form v-if="activeTab === 'login'" @submit.prevent="handleLogin">
        <n-form-item>
          <n-input v-model:value="loginForm.username" placeholder="用户名" clearable :style="{ borderRadius: '50px' }">
            <template #prefix><n-icon><person-outline /></n-icon></template>
          </n-input>
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="loginForm.password" type="password" placeholder="密码"
            show-password-on="click" @keyup.enter="handleLogin" :style="{ borderRadius: '50px' }">
            <template #prefix><n-icon><lock-closed-outline /></n-icon></template>
          </n-input>
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleLogin" class="submit-btn">
          登 录
        </n-button>
      </n-form>

      <!-- 注册表单 -->
      <n-form v-else @submit.prevent="handleRegister">
        <n-form-item>
          <n-input v-model:value="regForm.username" placeholder="用户名(3-50位)" clearable :style="{ borderRadius: '50px' }" />
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="regForm.email" placeholder="邮箱" clearable :style="{ borderRadius: '50px' }" />
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="regForm.password" type="password" placeholder="密码(6-50位)"
            show-password-on="click" :style="{ borderRadius: '50px' }" />
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="regForm.grade" placeholder="年级 (如: 大三)" clearable :style="{ borderRadius: '50px' }" />
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="regForm.major" placeholder="专业 (如: 计算机科学)" clearable :style="{ borderRadius: '50px' }" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleRegister" class="submit-btn">
          注 册
        </n-button>
      </n-form>

      <!-- 提示 -->
      <div class="login-footer">
        <n-text depth="3">首次使用？切换到"注册"标签创建账号</n-text>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { PersonOutline, LockClosedOutline } from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)

const loginForm = ref({ username: '', password: '' })
const regForm = ref({ username: '', email: '', password: '', grade: '', major: '' })

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    message.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.login(loginForm.value.username, loginForm.value.password)
    message.success('登录成功')
    router.push('/')
  } catch (e) {
    message.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!regForm.value.username || !regForm.value.email || !regForm.value.password) {
    message.warning('请填写必填项')
    return
  }
  loading.value = true
  try {
    await authStore.register(regForm.value)
    message.success('注册成功')
    router.push('/')
  } catch (e) {
    message.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ── 页面背景：羊皮纸 + 波尔卡圆点 ── */
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f8f8f0;
  background-image:
    radial-gradient(circle, rgba(121, 79, 39, 0.06) 1.5px, transparent 1.5px),
    radial-gradient(circle, rgba(121, 79, 39, 0.04) 1px, transparent 1px);
  background-size: 28px 28px, 14px 14px;
  background-position: 0 0, 7px 7px;
}

/* ── 卡片 ── */
.login-card {
  width: 420px;
  padding: 40px;
  background: rgb(247, 243, 223);
  border-radius: 20px;
  border: 1.5px solid #e8e2d6;
  box-shadow: 0 3px 10px rgba(61, 52, 40, 0.10);
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.logo {
  font-size: 48px;
  margin-bottom: 8px;
}

.login-header h1 {
  font-size: 24px;
  color: #794f27;
  margin: 0 0 4px 0;
  font-weight: 700;
}

.login-header p {
  color: #9f927d;
  margin: 0;
  font-size: 14px;
}

/* ── 自定义 Tab 切换 ── */
.login-tabs {
  margin-bottom: 20px;
}

.tab-bar {
  display: flex;
  background: #f0e8d8;
  border-radius: 24px;
  padding: 3px;
  border: 2px solid #e8e2d6;
}

.tab-btn {
  flex: 1;
  padding: 8px 0;
  border: none;
  background: transparent;
  color: #9f927d;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 24px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
}

.tab-btn.active {
  background: #19c8b9;
  color: #fff9e3;
}

.tab-btn:hover:not(.active) {
  color: #19c8b9;
}

/* ── 提交按钮 ── */
.submit-btn {
  height: 48px;
  border-radius: 50px !important;
  font-size: 16px;
  font-weight: 700;
  margin-top: 8px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
}
</style>
