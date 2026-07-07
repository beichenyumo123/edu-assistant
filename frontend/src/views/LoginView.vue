<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="brand-panel">
        <div class="brand-mark">
          <div class="logo-badge">OA</div>
          <span>OnboardAgent</span>
        </div>
        <div class="brand-copy">
          <p class="eyebrow">Enterprise Onboarding Assistant</p>
          <h1>让新人培训资料真正参与答疑</h1>
          <p>上传员工手册、制度流程和岗位培训资料，生成带来源的入职问答。</p>
        </div>
        <div class="feature-grid">
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
            <span>入职、制度、流程一体化</span>
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
          <div class="mobile-logo">OA</div>
          <h2>{{ activeTab === 'login' ? '欢迎回来' : '创建账号' }}</h2>
          <p>{{ activeTab === 'login' ? '登录后继续使用企业培训资料库' : '开始建立你的入职培训助手' }}</p>
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
  padding: 32px;
  background:
    linear-gradient(180deg, rgba(20, 184, 166, 0.08), rgba(37, 99, 235, 0.05)),
    #f6f9fc;
}

.login-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) 440px;
  width: min(1040px, 100%);
  min-height: 620px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #dbe7f3;
  border-radius: 24px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
}

.brand-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(20, 184, 166, 0.10)),
    #eef7fb;
}

.brand-panel::after {
  content: '';
  position: absolute;
  right: -76px;
  bottom: -82px;
  z-index: 0;
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.16), rgba(20, 184, 166, 0.08) 48%, transparent 70%);
  pointer-events: none;
}

.brand-mark {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #0f172a;
  font-size: 18px;
  font-weight: 700;
}

.logo-badge,
.mobile-logo {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  color: #fff;
  background: #2563eb;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 800;
}

.brand-copy {
  position: relative;
  z-index: 1;
  max-width: 480px;
}

.eyebrow {
  margin: 0 0 14px;
  color: #14b8a6;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0;
}

.brand-copy h1 {
  margin: 0;
  color: #0f172a;
  font-size: 44px;
  line-height: 1.16;
}

.brand-copy p:last-child {
  margin: 18px 0 0;
  color: #52637a;
  font-size: 17px;
  line-height: 1.7;
}

.feature-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  max-width: 460px;
}

.feature-item {
  padding: 16px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 14px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}

.feature-item strong {
  display: block;
  color: #0f172a;
  font-size: 16px;
  margin-bottom: 6px;
}

.feature-item span {
  color: #64748b;
  font-size: 13px;
}

.login-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px 42px;
  background: #fff;
}

.login-header {
  margin-bottom: 26px;
}

.mobile-logo {
  display: none;
  margin-bottom: 18px;
}

.login-header h2 {
  margin: 0 0 8px;
  color: #0f172a;
  font-size: 30px;
  line-height: 1.2;
}

.login-header p {
  color: #64748b;
  margin: 0;
  font-size: 15px;
}

.auth-form {
  margin-top: 22px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.login-footer {
  text-align: center;
  margin-top: 22px;
}

@media (max-width: 860px) {
  .login-page {
    padding: 18px;
  }

  .login-shell {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .brand-panel {
    display: none;
  }

  .login-card {
    padding: 34px 24px;
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
