<template>
  <header class="app-header">
    <div class="header-inner">
      <div class="logo" @click="$router.push('/')">
        <span class="logo-icon">▶</span>
        <span class="logo-text">VideoNote</span>
      </div>
      <nav class="nav-tabs">
        <router-link
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="nav-tab"
          active-class="nav-tab--active"
        >
          {{ tab.label }}
        </router-link>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
const tabs = [
  { path: '/', label: '视频笔记' },
  { path: '/qa', label: '视频问答' },
  { path: '/download', label: '视频下载' },
  { path: '/settings', label: '设置' },
]
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba($bg-secondary, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid $border-color;
  height: $header-height;
}

.header-inner {
  max-width: $content-max-width;
  margin: 0 auto;
  padding: 0 $spacing-lg;
  height: 100%;
  display: flex;
  align-items: center;
  gap: $spacing-xl;
}

.logo {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  cursor: pointer;
  flex-shrink: 0;
}

.logo-icon {
  font-size: 20px;
  color: $accent-primary;
}

.logo-text {
  font-size: $font-size-lg;
  font-weight: 700;
  color: $text-primary;
}

.nav-tabs {
  display: flex;
  gap: $spacing-xs;
}

.nav-tab {
  padding: $spacing-sm $spacing-md;
  border-radius: $radius-md;
  color: $text-secondary;
  font-size: $font-size-base;
  font-weight: 500;
  transition: all $transition-fast;
  text-decoration: none;

  &:hover {
    color: $text-primary;
    background: $bg-hover;
  }

  &--active {
    color: $accent-primary;
    background: rgba($accent-primary, 0.1);
  }
}

@media (max-width: 640px) {
  .nav-tabs {
    gap: 0;
  }

  .nav-tab {
    padding: $spacing-sm $spacing-sm;
    font-size: $font-size-sm;
  }
}
</style>
