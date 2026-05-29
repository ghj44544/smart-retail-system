<template>
  <!--
    App.vue - 根组件
    使用 RouterView 根据路由渲染不同页面
    配合 <Transition> 实现页面切换动画
  -->
  <router-view v-slot="{ Component, route }">
    <transition name="fade-page" mode="out-in">
      <component :is="Component" :key="route.path" />
    </transition>
  </router-view>
</template>

<script setup lang="ts">
// 根组件逻辑
// RouterView 会自动根据当前路由渲染对应组件
</script>

<style lang="scss">
/* ==================== 页面切换动画 ==================== */
.fade-page-enter-active,
.fade-page-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-page-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.fade-page-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
