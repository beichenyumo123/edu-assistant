<template>
  <Cursor>
    <n-config-provider :theme-overrides="themeOverrides">
      <n-message-provider>
        <n-dialog-provider>
          <router-view />
        </n-dialog-provider>
      </n-message-provider>
    </n-config-provider>
  </Cursor>
</template>

<script setup>
import { Cursor } from 'animal-island-vue'
import { themeOverrides } from './theme/naiveOverrides'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--animal-font-family, Nunito, 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif);
  background: var(--animal-bg-color, #f8f8f0);
  color: var(--animal-text-color, #725d42);
}

#app {
  width: 100%;
  height: 100vh;
}
</style>
