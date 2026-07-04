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
      <n-tabs v-model:value="activeTab" type="segment" animated>
        <n-tab-pane name="login" tab="登录" />
        <n-tab-pane name="register" tab="注册" />
      </n-tabs>

      <!-- 登录表单 -->
      <n-form v-if="activeTab === 'login'" @submit.prevent="handleLogin">
        <n-form-item>
          <n-input v-model:value="loginForm.username" placeholder="用户名" clearable>
            <template #prefix><n-icon><person-outline /></n-icon></template>
          </n-input>
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="loginForm.password" type="password" placeholder="密码"
            show-password-on="click" @keyup.enter="handleLogin">
            <template #prefix><n-icon><lock-closed-outline /></n-icon></template>
          </n-input>
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleLogin">
          登 录
        </n-button>
      </n-form>

      <!-- 注册表单 -->
      <n-form v-else @submit.prevent="handleRegister">
        <n-form-item>
          <n-input v-model:value="regForm.username" placeholder="用户名(3-50位)" clearable />
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="regForm.email" placeholder="邮箱" clearable />
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="regForm.password" type="password" placeholder="密码(6-50位)"
            show-password-on="click" />
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="regForm.grade" placeholder="年级 (如: 大三)" clearable />
        </n-form-item>
        <n-form-item>
          <n-input v-model:value="regForm.major" placeholder="专业 (如: 计算机科学)" clearable />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleRegister">
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
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
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
  color: #333;
  margin: 0 0 4px 0;
}

.login-header p {
  color: #999;
  margin: 0;
  font-size: 14px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
}
</style>
