<template>
  <div class="welcome">
    <h2>{{ title }}</h2>
    <p>{{ subtitle }}</p>
    <div class="preset-cards">
      <div v-for="q in questions" :key="q" class="preset-card" @click="$emit('send', q)">
        {{ q }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  questions: { type: Array, default: () => [] },
})
defineEmits(['send'])
</script>

<style scoped>
.welcome { text-align: center; padding: 60px 20px; }
.welcome h2 { font-size: 28px; color: #794f27; margin-bottom: 8px; }
.welcome p { color: #9f927d; margin-bottom: 24px; }

.preset-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.preset-card {
  padding: 14px 12px;
  background: #f7f3df;
  border-radius: 16px;
  cursor: pointer;
  font-size: 13px;
  color: #725d42;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
}

.preset-card:hover {
  background: #e6f9f6;
  color: #19c8b9;
  transform: translateY(-2px);
}
</style>
