<!--
  =====================================================
  src/views/recommend/index.vue
  推荐系统页
  严格遵循 API 文档 8.1-8.4
  三个 Tab: 热门推荐 + 关联推荐 + 个性化推荐
  =====================================================
-->
<template>
  <div class="recommend-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">推荐系统</h2>
        <p class="page-subtitle">基于大数据算法的智能商品推荐，提升转化率与用户粘性</p>
      </div>
      <el-button type="primary" :icon="Refresh" :loading="refreshing" @click="handleRefresh">
        {{ refreshing ? '重新计算中...' : '刷新推荐结果' }}
      </el-button>
    </div>

    <el-tabs v-model="activeTab" type="border-card" class="recommend-tabs">
      <!-- ========== Tab 1: 热门推荐 ========== -->
      <el-tab-pane label="🔥 热门推荐" name="hot">
        <div class="tab-content" v-loading="hotLoading">
          <el-empty v-if="!hotList.length" description="暂无热门推荐" />
          <div v-else class="recommend-grid">
            <div v-for="(item, idx) in hotList" :key="item.product_id" class="recommend-card">
              <div class="rc-rank" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</div>
              <div class="rc-body">
                <div class="rc-name">{{ item.name }}</div>
                <div class="rc-meta">
                  <span class="rc-price">¥{{ item.price!.toFixed(2) }}</span>
                  <span class="rc-sales">已售 {{ item.sales_count }}</span>
                </div>
                <div class="rc-rating">
                  <el-rate :model-value="item.rating" disabled size="small" show-score text-color="#fdcb6e" />
                </div>
              </div>
              <div class="rc-action">
                <el-button type="primary" size="small" :icon="View" round @click="handleViewProduct(item.product_id)">查看</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ========== Tab 2: 关联推荐 ========== -->
      <el-tab-pane label="🔗 关联推荐" name="association">
        <div class="tab-content" v-loading="assoLoading">
          <div class="asso-select">
            <span class="asso-select-label">选择商品查看关联推荐：</span>
            <el-select v-model="assoProductId" placeholder="请选择商品" filterable style="width:360px" @change="loadAssociation">
              <el-option
                v-for="p in productOptions"
                :key="p.id"
                :label="`${p.name} (${p.product_no})`"
                :value="p.id"
              />
            </el-select>
          </div>
          <el-empty v-if="assoProductId && !assoList.length" description="该商品暂无关联推荐" />
          <div v-if="assoList.length" class="recommend-grid" style="margin-top:16px">
            <div v-for="item in assoList" :key="item.product_id" class="recommend-card">
              <div class="rc-body">
                <div class="rc-name">{{ item.name }}</div>
                <div class="rc-meta"><span class="rc-price">¥{{ item.price!.toFixed(2) }}</span></div>
              </div>
              <div class="rc-extra">
                <div class="asso-metrics">
                  <span class="asso-metric">置信度 {{ ((item.confidence || 0) * 100).toFixed(0) }}%</span>
                  <span class="asso-metric">提升度 {{ (item.lift || 0).toFixed(1) }}x</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ========== Tab 3: 个性化推荐 ========== -->
      <el-tab-pane label="👤 个性化推荐" name="personalized">
        <div class="tab-content" v-loading="persLoading">
          <div class="asso-select">
            <span class="asso-select-label">选择用户查看个性化推荐：</span>
            <el-select v-model="persUserId" placeholder="请选择用户" filterable style="width:260px">
              <el-option
                v-for="u in userOptions"
                :key="u.id"
                :label="`${u.username}${u.nickname ? ' - ' + u.nickname : ''} (#${u.id})`"
                :value="u.id"
              />
            </el-select>
            <el-button type="primary" @click="loadPersonalized">查询推荐</el-button>
          </div>
          <el-empty v-if="persUserId && !persList.length" description="暂无个性化推荐数据" />
          <div v-if="persList.length" class="recommend-grid" style="margin-top:16px">
            <div v-for="item in persList" :key="item.product_id" class="recommend-card pers-card">
              <div class="rc-body">
                <div class="rc-name">{{ item.name }}</div>
                <div class="rc-meta">
                  <span class="rc-price">¥{{ item.price!.toFixed(2) }}</span>
                  <el-tag size="small" effect="plain" type="primary">匹配 {{ scorePercent(item.score) }}%</el-tag>
                </div>
                <div class="pers-reason">{{ item.reason }}</div>
              </div>
              <div class="rc-score-bar">
                <el-progress :percentage="scorePercent(item.score)" :stroke-width="6" :color="progressColor(item.score || 0)" />
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, View } from '@element-plus/icons-vue'
import { getHotRecommend, getAssociationRecommend, getPersonalizedRecommend, refreshRecommend } from '@/api/recommend'
import { getProductList } from '@/api/product'
import { getUserList } from '@/api/user'
import type { ProductItem, RecommendItem, UserItem } from '@/types/api'

// ==================== 状态 ====================
const activeTab = ref('hot')
const router = useRouter()
const refreshing = ref(false)
const hotLoading = ref(false); const assoLoading = ref(false); const persLoading = ref(false)

const hotList = ref<RecommendItem[]>([])
const assoProductId = ref<number | null>(null); const assoList = ref<RecommendItem[]>([])
const persUserId = ref<number | null>(null); const persList = ref<RecommendItem[]>([])

const productOptions = ref<ProductItem[]>([])
const userOptions = ref<UserItem[]>([])

const scorePercent = (score?: number) => Math.round(Math.max(0, Math.min(score || 0, 1)) * 100)
const progressColor = (score: number) => score >= 0.85 ? '#00b894' : score >= 0.7 ? '#6c5ce7' : '#fdcb6e'

// ==================== 数据加载 ====================
const loadHot = async () => { hotLoading.value = true; try { const r = await getHotRecommend(10); hotList.value = r.data } catch {/* */} finally { hotLoading.value = false } }
const loadAssociation = async () => { if (!assoProductId.value) return; assoLoading.value = true; try { const r = await getAssociationRecommend(assoProductId.value); assoList.value = r.data } catch {/* */} finally { assoLoading.value = false } }
const loadPersonalized = async () => { if (!persUserId.value) return; persLoading.value = true; try { const r = await getPersonalizedRecommend(persUserId.value); persList.value = r.data } catch {/* */} finally { persLoading.value = false } }
const handleViewProduct = (productId: number) => router.push(`/products/${productId}`)

const loadProductOptions = async () => {
  try {
    const r = await getProductList({ page: 1, page_size: 100, status: 'on' })
    productOptions.value = (r.data.items || []).filter((p) => !String(p.product_no || '').startsWith('DEMO-'))
    if (!assoProductId.value && productOptions.value.length) assoProductId.value = productOptions.value[0].id
  } catch {
    productOptions.value = []
  }
}

const loadUserOptions = async () => {
  try {
    const r = await getUserList({ page: 1, page_size: 100, role: 'user' })
    userOptions.value = r.data.items || []
    if (!persUserId.value && userOptions.value.length) persUserId.value = userOptions.value[0].id
  } catch {
    userOptions.value = []
  }
}

const handleRefresh = async () => {
  refreshing.value = true
  try { await refreshRecommend(); ElMessage.success('推荐结果已刷新'); loadHot(); if (assoProductId.value) loadAssociation(); if (persUserId.value) loadPersonalized() } catch {/* */} finally { refreshing.value = false }
}

onMounted(async () => {
  await Promise.all([loadHot(), loadProductOptions(), loadUserOptions()])
})
</script>

<style lang="scss" scoped>
.recommend-page { max-width: 1200px; margin: 0 auto; animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; background: linear-gradient(135deg, #6c5ce7, #a29bfe); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.page-subtitle { font-size: 13px; color: #b2bec3; margin-top: 4px; }

.recommend-tabs { border-radius: 14px; overflow: hidden; border: 1px solid var(--border-light); box-shadow: none;
  :deep(.el-tabs__header) { background: #fafbfc; border-bottom: 1px solid var(--border-light); margin: 0; }
  :deep(.el-tabs__content) { padding: 0; }
}
.tab-content { padding: 24px; min-height: 400px; }

/* 推荐卡片网格 */
.recommend-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
.recommend-card { display: flex; align-items: center; gap: 16px; padding: 18px 20px; background: #fff; border: 1px solid var(--border-light); border-radius: 14px; transition: all 0.3s ease;
  &:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: #6c5ce7; }
}

.rc-rank { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 800; color: #b2bec3; background: #f0f3f7; flex-shrink: 0;
  &.rank-1 { background: linear-gradient(135deg, #fdcb6e, #f39c12); color: #fff; }
  &.rank-2 { background: linear-gradient(135deg, #dfe6e9, #b2bec3); color: #fff; }
  &.rank-3 { background: linear-gradient(135deg, #fab1a0, #e17055); color: #fff; }
}

.rc-body { flex: 1; min-width: 0; }
.rc-name { font-size: 14px; font-weight: 600; color: #2d3436; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rc-meta { display: flex; align-items: center; gap: 12px; margin-top: 6px; flex-wrap: wrap; }
.rc-price { font-size: 18px; font-weight: 700; color: #6c5ce7; }
.rc-sales { font-size: 12px; color: #b2bec3; }
.rc-rating { margin-top: 4px; }

.rc-action { flex-shrink: 0; }
.rc-extra { flex-shrink: 0; }

.asso-metrics { display: flex; flex-direction: column; gap: 4px; }
.asso-metric { font-size: 12px; color: #00b894; font-weight: 500; white-space: nowrap; }

.asso-select { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }
.asso-select-label { font-size: 13px; color: #636e72; white-space: nowrap; }

.pers-reason { font-size: 12px; color: #a29bfe; margin-top: 6px; }
.rc-score-bar { width: 80px; flex-shrink: 0; }

@media (max-width: 768px) {
  .recommend-grid { grid-template-columns: 1fr; }
  .recommend-card { flex-wrap: wrap; }
}
</style>
