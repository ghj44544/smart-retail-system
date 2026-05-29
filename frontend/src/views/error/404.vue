<!--
  =====================================================
  src/views/error/404.vue
  404 页面未找到
  =====================================================
-->
<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <div class="not-found-code">404</div>
      <h1>页面未找到</h1>
      <p>您访问的页面不存在或已被移除</p>
      <el-button type="primary" size="large" @click="$router.push('/')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.not-found-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: var(--bg-body);
}

.not-found-content {
  text-align: center;

  .not-found-code {
    font-size: 120px;
    font-weight: 800;
    background: linear-gradient(135deg, #6c5ce7, #a29bfe, #00b894);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
    opacity: 0.3;
  }

  h1 {
    font-size: 24px;
    color: var(--text-primary);
    margin: 16px 0 8px;
  }

  p {
    color: var(--text-secondary);
    margin-bottom: 24px;
  }
}
</style>
