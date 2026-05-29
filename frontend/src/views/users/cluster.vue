<!--
  =====================================================
  src/views/users/cluster.vue
  K-Means 用户聚类分析页 - 散点图 + 雷达图 + 分群详情
  严格遵循 API 文档 7.2: GET /analysis/cluster
  额外: 7.3: POST /analysis/recalculate 重新聚类按钮
  =====================================================
-->
<template>
  <div class="cluster-page">
    <!-- ========== 页面标题 ========== -->
    <div class="page-header">
      <div>
        <h2 class="page-title">K-Means 用户聚类分析</h2>
        <p class="page-subtitle">
          基于 RFM 三维特征使用 K-Means 算法对用户进行聚类，探索不同用户群体的行为模式
        </p>
      </div>
      <el-button
        type="primary"
        :icon="Refresh"
        :loading="recalculating"
        @click="handleRecalculate"
      >
        {{ recalculating ? '重新聚类中...' : '重新聚类分析' }}
      </el-button>
    </div>

    <!-- ========== 加载状态 ========== -->
    <div v-loading="loading" class="cluster-content">
      <template v-if="clusterData">
        <!-- ========== 聚类概览卡片 ========== -->
        <div class="cluster-summary">
          <div
            v-for="(c, idx) in clusterData.clusters"
            :key="c.label"
            class="cluster-summary-card"
            :style="{ '--cluster-color': clusterColors[idx], '--cluster-bg': clusterColors[idx] + '12' }"
          >
            <div class="summary-header">
              <div class="summary-badge" :style="{ background: clusterColors[idx] }">
                {{ c.label }}
              </div>
              <span class="summary-name">{{ c.name }}</span>
            </div>
            <div class="summary-count">{{ c.count }} <span class="summary-unit">人</span></div>
            <div class="summary-center">
              中心点: R{{ c.center[0] }} F{{ c.center[1] }} M{{ c.center[2] }}
            </div>
          </div>
        </div>

        <!-- ========== 图表区: 散点图 + 雷达图 ========== -->
        <div class="chart-row">
          <!-- RFM 三维散点图 -->
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="chart-card-hd">
                <h3 class="chart-title">RFM 三维散点分布</h3>
                <el-radio-group v-model="scatterAxis" size="small" @change="renderScatterChart">
                  <el-radio-button value="rf">R × F</el-radio-button>
                  <el-radio-button value="fm">F × M</el-radio-button>
                  <el-radio-button value="rm">R × M</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div ref="scatterChartRef" class="chart-box"></div>
          </el-card>

          <!-- 聚类中心雷达图 -->
          <el-card class="chart-card" shadow="never">
            <template #header>
              <h3 class="chart-title">聚类中心特征对比</h3>
            </template>
            <div ref="clusterRadarRef" class="chart-box"></div>
          </el-card>
        </div>

        <!-- ========== 各聚类分群详情 ========== -->
        <div class="cluster-details">
          <el-card
            v-for="(c, idx) in clusterData.clusters"
            :key="c.label"
            class="cluster-detail-card"
            shadow="never"
          >
            <template #header>
              <div class="detail-header">
                <div class="detail-badge" :style="{ background: clusterColors[idx] }">{{ c.label }}</div>
                <span class="detail-name">{{ c.name }}</span>
                <el-tag size="small" effect="light" :color="clusterColors[idx] + '20'">
                  {{ c.count }} 人
                </el-tag>
              </div>
            </template>
            <div class="detail-body">
              <div class="detail-item">
                <span class="detail-label">R 近度中心</span>
                <el-progress
                  :percentage="(c.center[0] / 10) * 100"
                  :color="clusterColors[idx]"
                  :stroke-width="8"
                >
                  <span class="detail-progress-text">{{ c.center[0].toFixed(1) }}</span>
                </el-progress>
              </div>
              <div class="detail-item">
                <span class="detail-label">F 频度中心</span>
                <el-progress
                  :percentage="(c.center[1] / 10) * 100"
                  :color="clusterColors[idx]"
                  :stroke-width="8"
                >
                  <span class="detail-progress-text">{{ c.center[1].toFixed(1) }}</span>
                </el-progress>
              </div>
              <div class="detail-item">
                <span class="detail-label">M 额度中心</span>
                <el-progress
                  :percentage="Math.min((c.center[2] / 2000) * 100, 100)"
                  :color="clusterColors[idx]"
                  :stroke-width="8"
                >
                  <span class="detail-progress-text">¥{{ c.center[2].toFixed(0) }}</span>
                </el-progress>
              </div>
              <div class="detail-strategy">
                <span class="strategy-label">运营策略</span>
                <p class="strategy-text">{{ clusterStrategies[idx] || '根据此群体特征制定个性化运营策略' }}</p>
              </div>
            </div>
          </el-card>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// K-Means 聚类分析页逻辑
// =====================================================
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getClusterAnalysis, recalculateAnalysis } from '@/api/analysis'
import type { ClusterResult } from '@/types/api'

// ==================== 状态定义 ====================

const loading = ref(false)
const recalculating = ref(false)
const clusterData = ref<ClusterResult | null>(null)
const scatterAxis = ref('rf')

// ==================== 图表引用 ====================

const scatterChartRef = ref<HTMLDivElement | null>(null)
const clusterRadarRef = ref<HTMLDivElement | null>(null)

let scatterChart: echarts.ECharts | null = null
let clusterRadarChart: echarts.ECharts | null = null

// ==================== 常量 ====================

const clusterColors = ['#6c5ce7', '#00b894', '#74b9ff', '#fdcb6e', '#e17055']
const clusterStrategies = [
  '重点维护：提供VIP专属服务，推送高端新品和限量商品，建立1对1客户关系管理体系。',
  '提升客单价：通过满减、套餐组合等促销手段提升单次消费金额，引导购买高毛利商品。',
  '激活用户：发放首单优惠券，通过EDM/短信推送热门商品，降低首次购买门槛。',
  '引导购买：新用户注册礼包，新人专享折扣，设计新手引导流程帮助完成首次体验。',
  '召回策略：发送回流优惠券，推送平台最新活动和热门商品，分析流失原因并优化。',
]

// ==================== 图表渲染 ====================

/** 渲染 RFM 三维散点图（可选择投影轴） */
const renderScatterChart = (): void => {
  if (!scatterChartRef.value || !clusterData.value) return
  if (!scatterChart) scatterChart = echarts.init(scatterChartRef.value)

  const clusters = clusterData.value.clusters
  const axisMap: Record<string, { xKey: string; yKey: string; xLabel: string; yLabel: string }> = {
    rf: { xKey: 'R 近度', yKey: 'F 频度', xLabel: 'R 近度 (越低越好)', yLabel: 'F 频度' },
    fm: { xKey: 'F 频度', yKey: 'M 额度', xLabel: 'F 频度', yLabel: 'M 额度 (元)' },
    rm: { xKey: 'R 近度', yKey: 'M 额度', xLabel: 'R 近度 (越低越好)', yLabel: 'M 额度 (元)' },
  }
  const config = axisMap[scatterAxis.value]

  const series = clusters.map((c, i) => ({
    name: c.name,
    type: 'scatter' as const,
    data: c.points.map((p) => {
      const valMap: Record<string, number> = { rf: p.x, fm: p.y, rm: p.x }
      const valMap2: Record<string, number> = { rf: p.y, fm: p.z, rm: p.z }
      return [valMap[scatterAxis.value], valMap2[scatterAxis.value], p.user_id]
    }),
    symbolSize: 10,
    itemStyle: {
      color: clusterColors[i],
      opacity: 0.7,
    },
    emphasis: {
      scale: 1.6,
      itemStyle: { opacity: 1 },
    },
  }))

  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e8ecf1',
      textStyle: { color: '#2d3436', fontSize: 13 },
      formatter: (params: any) => {
        const d = params.data
        return `用户ID: ${d[2]}<br/>${config.xLabel}: ${d[0]}<br/>${config.yLabel}: ${d[1]}<br/><span style="color:${params.color}">${params.seriesName}</span>`
      },
      padding: [10, 14],
      extraCssText: 'border-radius:8px;',
    },
    legend: { bottom: 0, textStyle: { color: '#636e72', fontSize: 11 }, itemWidth: 10, itemHeight: 10 },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: {
      type: 'value',
      name: config.xLabel,
      nameTextStyle: { color: '#b2bec3', fontSize: 11 },
      axisLabel: { color: '#b2bec3', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } },
    },
    yAxis: {
      type: 'value',
      name: config.yLabel,
      nameTextStyle: { color: '#b2bec3', fontSize: 11 },
      axisLabel: { color: '#b2bec3', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } },
    },
    series,
  }

  scatterChart.setOption(option)
}

/** 渲染聚类中心雷达图 */
const renderClusterRadar = (): void => {
  if (!clusterRadarRef.value || !clusterData.value) return
  if (!clusterRadarChart) clusterRadarChart = echarts.init(clusterRadarRef.value)

  const clusters = clusterData.value.clusters
  const maxR = Math.max(...clusters.map((c) => c.center[0]))
  const maxF = Math.max(...clusters.map((c) => c.center[1]))
  const maxM = Math.max(...clusters.map((c) => c.center[2]))

  const option: EChartsOption = {
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      data: clusters.map((c) => c.name),
      textStyle: { color: '#636e72', fontSize: 11 },
      itemWidth: 8, itemHeight: 8,
    },
    radar: {
      center: ['50%', '45%'],
      radius: '55%',
      indicator: [
        { name: 'R 近度', max: Math.ceil(maxR) },
        { name: 'F 频度', max: Math.ceil(maxF) },
        { name: 'M 额度(元)', max: Math.ceil(maxM) },
      ],
      axisName: { color: '#636e72', fontSize: 12 },
      splitArea: { areaStyle: { color: ['rgba(108,92,231,0.02)', 'rgba(108,92,231,0.04)'] } },
      splitLine: { lineStyle: { color: '#e8ecf1' } },
      axisLine: { lineStyle: { color: '#e8ecf1' } },
    },
    series: [{
      type: 'radar',
      data: clusters.map((c, i) => ({
        name: c.name,
        value: c.center,
        areaStyle: { color: clusterColors[i] + '15' },
        lineStyle: { color: clusterColors[i], width: 2 },
        itemStyle: { color: clusterColors[i] },
        symbol: 'circle',
        symbolSize: 5,
      })),
    }],
  }

  clusterRadarChart.setOption(option)
}

/** 渲染所有图表 */
const renderAllCharts = (): void => {
  renderScatterChart()
  renderClusterRadar()
}

// ==================== 数据加载 ====================

const loadData = async (): Promise<void> => {
  loading.value = true
  try {
    const res = await getClusterAnalysis()
    clusterData.value = res.data
    await nextTick()
    renderAllCharts()
  } catch {
    ElMessage.error('聚类数据加载失败，请稍后重试')
  } finally { loading.value = false }
}

/** 触发重新聚类 - API 7.3 */
const handleRecalculate = async (): Promise<void> => {
  recalculating.value = true
  try {
    await recalculateAnalysis('cluster')
    ElMessage.success('聚类分析重新计算完成')
    await loadData()
  } catch {
    ElMessage.error('聚类重新计算失败，请稍后重试')
  } finally { recalculating.value = false }
}

// ==================== 生命周期 ====================

const handleResize = () => {
  scatterChart?.resize()
  clusterRadarChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  scatterChart?.dispose()
  clusterRadarChart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.cluster-page {
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 20px; flex-wrap: wrap; gap: 12px;
}

.page-title {
  font-size: 22px; font-weight: 700;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

.page-subtitle { font-size: 13px; color: #b2bec3; margin-top: 4px; }

.cluster-content { min-height: 400px; }

/* ========== 聚类概览卡片 ========== */
.cluster-summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.cluster-summary-card {
  background: #ffffff;
  border: 1px solid var(--border-light);
  border-radius: 14px;
  padding: 16px;
  transition: all 0.3s ease;
  border-left: 3px solid var(--cluster-color);

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }
}

.summary-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.summary-badge {
  width: 28px; height: 28px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 14px; font-weight: 700;
}
.summary-name { font-size: 13px; font-weight: 600; color: #2d3436; }
.summary-count { font-size: 24px; font-weight: 800; color: var(--cluster-color); margin-bottom: 4px; }
.summary-unit { font-size: 12px; font-weight: 400; color: #b2bec3; }
.summary-center { font-size: 11px; color: #b2bec3; }

/* ========== 图表行 ========== */
.chart-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;
}

.chart-card {
  border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--border-light); }
  :deep(.el-card__body) { padding: 16px; }
}

.chart-card-hd { display: flex; justify-content: space-between; align-items: center; }
.chart-title { margin: 0; font-size: 15px; font-weight: 700; color: #2d3436; }
.chart-box { width: 100%; height: 360px; }

/* ========== 聚类详情 ========== */
.cluster-details {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;

  @media (max-width: 1200px) { grid-template-columns: repeat(2, 1fr); }
  @media (max-width: 768px) { grid-template-columns: 1fr; }

  .cluster-detail-card:last-child {
    @media (min-width: 769px) and (max-width: 1200px) { grid-column: 1 / -1; }
  }
}

.cluster-detail-card {
  border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__header) { padding: 14px 18px; border-bottom: 1px solid var(--border-light); }
  :deep(.el-card__body) { padding: 16px 18px; }
}

.detail-header { display: flex; align-items: center; gap: 8px; }
.detail-badge {
  width: 24px; height: 24px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 12px; font-weight: 700;
}
.detail-name { font-size: 14px; font-weight: 600; color: #2d3436; flex: 1; }

.detail-item { margin-bottom: 14px; }
.detail-label { font-size: 12px; color: #b2bec3; display: block; margin-bottom: 4px; }
.detail-progress-text { font-size: 11px; color: #636e72; }

.detail-strategy {
  margin-top: 12px; padding: 10px 12px;
  background: rgba(108,92,231,0.03); border-radius: 8px;
}
.strategy-label { font-size: 12px; color: #6c5ce7; font-weight: 600; }
.strategy-text { font-size: 12px; color: #636e72; margin-top: 4px; line-height: 1.6; }

/* 响应式 */
@media (max-width: 992px) {
  .chart-row { grid-template-columns: 1fr; }
  .cluster-summary { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
}
</style>
