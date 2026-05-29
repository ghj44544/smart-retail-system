<!--
  =====================================================
  src/views/users/rfm.vue
  RFM 用户价值分析页 - 分组分布图 + 评分明细表
  严格遵循 API 文档 7.1: GET /analysis/rfm
  额外: 7.3: POST /analysis/recalculate 重新计算按钮
  =====================================================
-->
<template>
  <div class="rfm-page">
    <!-- ========== 页面标题 ========== -->
    <div class="page-header">
      <div>
        <h2 class="page-title">RFM 用户价值分析</h2>
        <p class="page-subtitle">
          基于 R(近度) F(频度) M(额度) 三维模型对用户进行价值分层，识别高价值用户与流失风险用户
        </p>
      </div>
      <el-button
        type="primary"
        :icon="Refresh"
        :loading="recalculating"
        @click="handleRecalculate"
      >
        {{ recalculating ? '重新计算中...' : '重新计算 RFM' }}
      </el-button>
    </div>

    <!-- ========== 加载状态 ========== -->
    <div v-loading="loading" class="rfm-content">
      <template v-if="rfmData">
        <!-- ========== 用户分群分布图（饼图 + 柱状图） ========== -->
        <div class="chart-row">
          <!-- 环形饼图 -->
          <el-card class="chart-card" shadow="never">
            <template #header>
              <h3 class="chart-title">用户价值分群分布</h3>
            </template>
            <div ref="pieChartRef" class="chart-box"></div>
          </el-card>

          <!-- 横向柱状图 -->
          <el-card class="chart-card" shadow="never">
            <template #header>
              <h3 class="chart-title">各分群用户数量</h3>
            </template>
            <div ref="barChartRef" class="chart-box"></div>
          </el-card>
        </div>

        <!-- ========== RFM 指标均值雷达图 + 分群概述 ========== -->
        <div class="chart-row">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <h3 class="chart-title">分群特征雷达图</h3>
            </template>
            <div ref="radarChartRef" class="chart-box"></div>
          </el-card>

          <el-card class="chart-card" shadow="never">
            <template #header>
              <h3 class="chart-title">分群说明</h3>
            </template>
            <div class="segment-desc-list">
              <div v-for="(item, idx) in segmentDescriptions" :key="item.name" class="segment-desc-item">
                <div class="segment-desc-dot" :style="{ background: segmentColors[idx] }"></div>
                <div class="segment-desc-content">
                  <div class="segment-desc-name">{{ item.name }}</div>
                  <div class="segment-desc-text">{{ item.desc }}</div>
                </div>
                <span class="segment-desc-count">{{ item.count }} 人</span>
              </div>
            </div>
          </el-card>
        </div>

        <!-- ========== RFM 评分明细表 ========== -->
        <el-card class="table-card" shadow="never">
          <template #header>
            <div class="table-card-header">
              <h3 class="chart-title">RFM 评分明细</h3>
              <el-input
                v-model="scoreSearch"
                placeholder="搜索用户ID..."
                :prefix-icon="Search"
                clearable
                size="small"
                style="width: 200px"
              />
            </div>
          </template>
          <el-table :data="filteredScores" stripe border max-height="450" row-key="user_id">
            <el-table-column prop="user_id" label="用户ID" width="90" align="center" />
            <el-table-column label="R 近度" width="100" align="center">
              <template #default="{ row }">
                <el-rate :model-value="row.recency" :max="5" disabled size="small" />
              </template>
            </el-table-column>
            <el-table-column label="F 频度" width="100" align="center">
              <template #default="{ row }">
                <el-rate :model-value="row.frequency" :max="5" disabled size="small" />
              </template>
            </el-table-column>
            <el-table-column label="M 额度" width="100" align="center">
              <template #default="{ row }">
                <el-rate :model-value="row.monetary" :max="5" disabled size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="segment" label="分群标签" min-width="160">
              <template #default="{ row }">
                <el-tag
                  :color="segmentColors[Math.max(0, segmentNames.indexOf(row.segment))]"
                  effect="dark"
                  size="small"
                >
                  {{ row.segment || '未知' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// RFM 分析页逻辑
// =====================================================
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { getRFMAnalysis, recalculateAnalysis } from '@/api/analysis'
import type { RFMResult, RFMScore } from '@/types/api'

// ==================== 状态定义 ====================

const loading = ref(false)
const recalculating = ref(false)
const rfmData = ref<RFMResult | null>(null)
const scoreSearch = ref('')

// ==================== 图表引用 ====================

const pieChartRef = ref<HTMLDivElement | null>(null)
const barChartRef = ref<HTMLDivElement | null>(null)
const radarChartRef = ref<HTMLDivElement | null>(null)

let pieChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null

// ==================== 常量 ====================

const segmentColors = ['#6c5ce7', '#00b894', '#74b9ff', '#fdcb6e', '#e17055']
const segmentNames = ['高价值用户', '忠诚用户', '潜力用户', '新用户', '流失用户']
const segmentDescriptions = [
  { name: '高价值用户', desc: 'R低 F高 M高 — 最近购买、频率高、消费大，平台核心资产', count: 0 },
  { name: '忠诚用户', desc: 'R中 F高 M中 — 稳定购买的老用户，可通过会员体系维护', count: 0 },
  { name: '潜力用户', desc: 'R低 F中 M中 — 近期活跃但消费不高，有提升空间', count: 0 },
  { name: '新用户', desc: 'R低 F低 M低 — 刚注册不久，需引导完成首次购买', count: 0 },
  { name: '流失用户', desc: 'R高 F低 M低 — 长时间未购买，需进行召回营销', count: 0 },
]

// ==================== 计算属性 ====================

/** 搜索过滤后的评分列表 */
const filteredScores = computed<RFMScore[]>(() => {
  if (!rfmData.value) return []
  const scores = rfmData.value.scores
  if (!scoreSearch.value) return scores
  return scores.filter((s) => String(s.user_id).includes(scoreSearch.value))
})

// ==================== 图表渲染 ====================

/** 渲染分群分布环形饼图 */
const renderPieChart = (): void => {
  if (!pieChartRef.value || !rfmData.value) return
  if (!pieChart) pieChart = echarts.init(pieChartRef.value)

  const dist = rfmData.value.distribution
  const data = dist.labels.map((name, i) => ({
    name,
    value: dist.values[i],
    itemStyle: { color: segmentColors[i], borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
  }))

  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e8ecf1',
      textStyle: { color: '#2d3436', fontSize: 13 },
      formatter: '{b}: {c}人 ({d}%)',
      padding: [10, 14],
      extraCssText: 'border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.06);',
    },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '50%'],
      padAngle: 2,
      data,
      label: { show: false },
      emphasis: { scaleSize: 10, label: { show: true, fontSize: 15, fontWeight: 'bold' } },
    }],
  }

  pieChart.setOption(option)
}

/** 渲染分群柱状图 */
const renderBarChart = (): void => {
  if (!barChartRef.value || !rfmData.value) return
  if (!barChart) barChart = echarts.init(barChartRef.value)

  const dist = rfmData.value.distribution
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e8ecf1',
      textStyle: { color: '#2d3436', fontSize: 13 },
      padding: [10, 14],
      extraCssText: 'border-radius:8px;',
    },
    grid: { left: '3%', right: '6%', bottom: '3%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: dist.labels,
      axisLabel: { color: '#636e72', fontSize: 11, rotate: 20 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e8ecf1' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#b2bec3', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } },
    },
    series: [{
      type: 'bar',
      data: dist.values.map((v, i) => ({
        value: v,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: segmentColors[i] },
            { offset: 1, color: segmentColors[i] + '60' },
          ]),
          borderRadius: [10, 10, 0, 0],
        },
      })),
      barWidth: 36,
      label: { show: true, position: 'top', color: '#636e72', fontSize: 13, fontWeight: 600 },
    }],
  }

  barChart.setOption(option)
}

/** 渲染分群特征雷达图 */
const renderRadarChart = (): void => {
  if (!radarChartRef.value || !rfmData.value) return
  if (!radarChart) radarChart = echarts.init(radarChartRef.value)

  // 计算每组的平均 R/F/M
  const allScores = rfmData.value.scores
  const seriesData = segmentNames.map((seg, i) => {
    const group = allScores.filter((s) => s.segment === seg)
    if (group.length === 0) return { name: seg, value: [0, 0, 0] }
    const avg = (key: keyof RFMScore) =>
      +(group.reduce((s, u) => s + (u[key] as number), 0) / group.length).toFixed(1)
    return {
      name: seg,
      value: [avg('recency'), avg('frequency'), avg('monetary')],
    }
  })

  const option: EChartsOption = {
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      textStyle: { color: '#636e72', fontSize: 11 },
      itemWidth: 10, itemHeight: 10,
    },
    radar: {
      center: ['50%', '45%'],
      radius: '55%',
      indicator: [
        { name: 'R 近度', max: 5 },
        { name: 'F 频度', max: 5 },
        { name: 'M 额度', max: 5 },
      ],
      axisName: { color: '#636e72', fontSize: 12 },
      splitArea: { areaStyle: { color: ['rgba(108,92,231,0.02)', 'rgba(108,92,231,0.04)'] } },
      splitLine: { lineStyle: { color: '#e8ecf1' } },
      axisLine: { lineStyle: { color: '#e8ecf1' } },
    },
    series: [{
      type: 'radar',
      data: seriesData.map((item, i) => ({
        ...item,
        areaStyle: { color: segmentColors[i] + '15' },
        lineStyle: { color: segmentColors[i], width: 1.5 },
        itemStyle: { color: segmentColors[i] },
      })),
    }],
  }

  radarChart.setOption(option)
}

/** 渲染所有图表 */
const renderAllCharts = (): void => {
  renderPieChart()
  renderBarChart()
  renderRadarChart()
}

// ==================== 数据加载 ====================

const loadData = async (): Promise<void> => {
  loading.value = true
  try {
    const res = await getRFMAnalysis()
    rfmData.value = res.data
    // 更新分群描述中的数量
    res.data.distribution.values.forEach((v, i) => {
      if (segmentDescriptions[i]) segmentDescriptions[i].count = v
    })
    await nextTick()
    renderAllCharts()
  } catch {
    ElMessage.error('RFM 数据加载失败，请稍后重试')
  } finally { loading.value = false }
}

/** 触发重新计算 - API 7.3 */
const handleRecalculate = async (): Promise<void> => {
  recalculating.value = true
  try {
    await recalculateAnalysis('rfm')
    ElMessage.success('RFM 分析重新计算完成')
    await loadData()
  } catch {
    ElMessage.error('RFM 重新计算失败，请稍后重试')
  } finally { recalculating.value = false }
}

// ==================== 生命周期 ====================

const handleResize = () => {
  pieChart?.resize()
  barChart?.resize()
  radarChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  pieChart?.dispose()
  barChart?.dispose()
  radarChart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.rfm-page {
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

.rfm-content { min-height: 400px; }

/* 图表行 */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.chart-card {
  border: 1px solid var(--border-light);
  border-radius: 14px;
  :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--border-light); }
  :deep(.el-card__body) { padding: 16px; }
}

.chart-title { margin: 0; font-size: 15px; font-weight: 700; color: #2d3436; }

.chart-box { width: 100%; height: 320px; }

/* 分群说明 */
.segment-desc-list { display: flex; flex-direction: column; gap: 12px; }
.segment-desc-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px; border-radius: 10px; transition: background 0.2s;
  &:hover { background: rgba(108,92,231,0.03); }
}
.segment-desc-dot { width: 10px; height: 10px; border-radius: 3px; margin-top: 4px; flex-shrink: 0; }
.segment-desc-name { font-size: 13px; font-weight: 600; color: #2d3436; }
.segment-desc-text { font-size: 12px; color: #636e72; margin-top: 2px; line-height: 1.5; }
.segment-desc-count { font-size: 14px; font-weight: 700; color: #6c5ce7; flex-shrink: 0; white-space: nowrap; }

/* 表格 */
.table-card {
  border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__header) { padding: 16px 20px; }
  :deep(.el-card__body) { padding: 0; }
}

.table-card-header { display: flex; justify-content: space-between; align-items: center; }

:deep(.el-table) {
  --el-table-border-color: #f0f3f7;
  th.el-table__cell { background: rgba(108,92,231,0.03); color: #636e72; font-weight: 600; }
  td.el-table__cell { font-size: 13px; }
}

/* 响应式 */
@media (max-width: 992px) {
  .chart-row { grid-template-columns: 1fr; }
}
</style>
