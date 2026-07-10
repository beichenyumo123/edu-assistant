<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="brand-panel">
        <div class="brand-mark">
          <div class="logo-badge">CC</div>
          <span>CorpKnow Compass</span>
        </div>
        <div class="brand-copy">
          <p class="eyebrow">Corporate Knowledge Compass</p>
          <h1>让企业知识真正参与答疑</h1>
          <p>上传员工手册、制度流程和岗位培训资料，AI 精准定位原文回答。</p>
        </div>
        <div class="feature-grid" aria-label="产品能力">
          <div class="feature-item">
            <strong>制度驱动</strong>
            <span>基于企业知识库回答</span>
          </div>
          <div class="feature-item">
            <strong>来源追溯</strong>
            <span>制度结论对应原文</span>
          </div>
          <div class="feature-item">
            <strong>新人培训</strong>
            <span>制度、流程一体化</span>
          </div>
          <div class="feature-item">
            <strong>质量观测</strong>
            <span>检索与引用指标可见</span>
          </div>
        </div>
      </section>

      <div class="login-card">
        <!-- Logo & 标题 -->
        <div class="login-header">
          <div class="mobile-logo">CC</div>
          <h2>{{ activeTab === 'login' ? '欢迎回来' : '创建账号' }}</h2>
          <p>{{ activeTab === 'login' ? '登录后继续使用企业知识库' : '开始建立你的企业知识导航' }}</p>
        </div>

        <!-- Tab切换：登录 / 注册 -->
        <n-tabs v-model:value="activeTab" type="segment" animated>
          <n-tab-pane name="login" tab="登录" />
          <n-tab-pane name="register" tab="注册" />
        </n-tabs>

        <!-- 登录表单 -->
        <n-form v-if="activeTab === 'login'" class="auth-form" @submit.prevent="handleLogin">
          <n-form-item>
            <n-input v-model:value="loginForm.username" size="large" placeholder="用户名" clearable>
              <template #prefix><n-icon><person-outline /></n-icon></template>
            </n-input>
          </n-form-item>
          <n-form-item>
            <n-input v-model:value="loginForm.password" size="large" type="password" placeholder="密码"
              show-password-on="click" @keyup.enter="handleLogin">
              <template #prefix><n-icon><lock-closed-outline /></n-icon></template>
            </n-input>
          </n-form-item>
          <n-button type="primary" size="large" block :loading="loading" @click="handleLogin">
            登录
          </n-button>
        </n-form>

        <!-- 注册表单 -->
        <n-form v-else class="auth-form" @submit.prevent="handleRegister">
          <n-form-item>
            <n-input v-model:value="regForm.username" size="large" placeholder="用户名 3-50 位" clearable>
              <template #prefix><n-icon><person-outline /></n-icon></template>
            </n-input>
          </n-form-item>
          <n-form-item>
            <n-input v-model:value="regForm.email" size="large" placeholder="邮箱" clearable />
          </n-form-item>
          <n-form-item>
            <n-input v-model:value="regForm.password" size="large" type="password" placeholder="密码 6-50 位"
              show-password-on="click">
              <template #prefix><n-icon><lock-closed-outline /></n-icon></template>
            </n-input>
          </n-form-item>
          <div class="form-row">
            <n-form-item>
              <n-input v-model:value="regForm.grade" size="large" placeholder="部门" clearable />
            </n-form-item>
            <n-form-item>
              <n-input v-model:value="regForm.major" size="large" placeholder="岗位" clearable />
            </n-form-item>
          </div>
          <n-button type="primary" size="large" block :loading="loading" @click="handleRegister">
            注册
          </n-button>
        </n-form>

        <!-- 提示 -->
        <div class="login-footer">
          <n-text depth="3">
            {{ activeTab === 'login' ? '首次使用？切换到注册创建账号' : '已有账号？切换到登录继续使用' }}
          </n-text>
        </div>
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
  padding: 28px;
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.96) 0%, rgba(240, 244, 248, 0.92) 48%, rgba(229, 236, 244, 0.88) 100%),
    #f6f8fb;
}

.login-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(400px, 0.62fr);
  width: min(1360px, 100%);
  min-height: calc(100vh - 56px);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(198, 210, 224, 0.72);
  border-radius: 32px;
  box-shadow: 0 34px 90px rgba(37, 48, 66, 0.14);
  backdrop-filter: blur(30px);
}

.brand-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: clamp(44px, 6vw, 84px);
  overflow: hidden;
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.88), rgba(239, 244, 249, 0.72)),
    #f5f7fa;
}

.brand-mark {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 14px;
  color: #111827;
  font-size: 18px;
  font-weight: 700;
  animation: fade-up 0.45s ease-in-out both;
}

.logo-badge,
.mobile-logo {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  color: #fff;
  background: #111827;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 800;
  box-shadow: 0 16px 34px rgba(17, 24, 39, 0.18);
}

.brand-copy {
  position: relative;
  z-index: 1;
  max-width: 780px;
  animation: fade-up 0.52s 0.05s ease-in-out both;
}

.eyebrow {
  margin: 0 0 22px;
  color: #667085;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0;
}

.brand-copy h1 {
  max-width: 760px;
  margin: 0;
  color: #0b1220;
  font-size: clamp(52px, 7vw, 86px);
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: 0;
}

.brand-copy p:last-child {
  max-width: 620px;
  margin: 28px 0 0;
  color: #4b5563;
  font-size: 19px;
  font-weight: 300;
  line-height: 1.85;
}

.feature-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 0.85fr) minmax(0, 1fr);
  gap: 18px;
  max-width: 720px;
  animation: fade-up 0.56s 0.12s ease-in-out both;
}

.feature-item {
  min-height: 112px;
  padding: 22px 24px;
  background: rgba(255, 255, 255, 0.48);
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 16px;
  box-shadow: 0 24px 60px rgba(45, 58, 78, 0.08);
  backdrop-filter: blur(22px);
  transition: transform 0.35s ease-in-out, border-color 0.35s ease-in-out, box-shadow 0.35s ease-in-out;
}

.feature-item:nth-child(2),
.feature-item:nth-child(4) {
  transform: translateY(18px);
}

.feature-item:hover {
  transform: translateY(-4px);
  border-color: rgba(17, 24, 39, 0.12);
  box-shadow: 0 30px 70px rgba(45, 58, 78, 0.12);
}

.feature-item:nth-child(2):hover,
.feature-item:nth-child(4):hover {
  transform: translateY(10px);
}

.feature-item strong {
  display: block;
  color: #111827;
  font-size: 18px;
  margin-bottom: 10px;
}

.feature-item span {
  color: #667085;
  font-size: 14px;
  line-height: 1.6;
}

.login-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: clamp(34px, 4vw, 58px);
  background: rgba(255, 255, 255, 0.78);
  border-left: 1px solid rgba(198, 210, 224, 0.58);
  backdrop-filter: blur(26px);
  animation: fade-up 0.48s 0.08s ease-in-out both;
}

.login-header {
  margin-bottom: 30px;
}

.mobile-logo {
  display: none;
  margin-bottom: 22px;
}

.login-header h2 {
  margin: 0 0 12px;
  color: #111827;
  font-size: 38px;
  font-weight: 800;
  line-height: 1.12;
}

.login-header p {
  color: #667085;
  margin: 0;
  font-size: 16px;
  line-height: 1.7;
}

.auth-form {
  margin-top: 26px;
}

.auth-form :deep(.n-input) {
  border-radius: 16px;
  transition: box-shadow 0.35s ease-in-out, transform 0.35s ease-in-out;
}

.auth-form :deep(.n-input:hover),
.auth-form :deep(.n-input.n-input--focus) {
  box-shadow: 0 18px 38px rgba(37, 48, 66, 0.08);
}

.auth-form :deep(.n-button) {
  height: 48px;
  border-radius: 999px;
  font-size: 16px;
  font-weight: 700;
  transition: transform 0.32s ease-in-out, box-shadow 0.32s ease-in-out;
}

.auth-form :deep(.n-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 18px 36px rgba(24, 24, 27, 0.16);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.login-footer {
  text-align: left;
  margin-top: 26px;
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

@media (max-width: 980px) {
  .login-page {
    padding: 16px;
    align-items: flex-start;
  }

  .login-shell {
    grid-template-columns: 1fr;
    min-height: auto;
    border-radius: 24px;
  }

  .brand-panel {
    min-height: 48vh;
    padding: 38px 26px;
  }

  .brand-copy h1 {
    font-size: clamp(46px, 14vw, 68px);
  }

  .feature-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .feature-item,
  .feature-item:nth-child(2),
  .feature-item:nth-child(4) {
    min-height: auto;
    transform: none;
  }

  .login-card {
    padding: 34px 24px 38px;
    border-left: 0;
    border-top: 1px solid rgba(198, 210, 224, 0.58);
  }

  .mobile-logo {
    display: grid;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
