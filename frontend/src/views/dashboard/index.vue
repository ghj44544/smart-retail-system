<!--
  =====================================================
  src/views/dashboard/index.vue
  数据驾驶舱页面 - 炫酷浅色系图表大屏
  严格遵循 API 接口规范文档 v1.0 第九章

  页面布局:
  ┌──────────────────────────────────────────────┐
  │  KPI 指标卡片 x8（4x2 网格）                    │
  ├──────────────────────┬───────────────────────┤
  │  销售趋势折线图（全宽）                          │
  ├──────────────────────┼───────────────────────┤
  │  用户行为 PV/UV 趋势   │  用户分群饼图          │
  ├──────────────────────┼───────────────────────┤
  │  商品销售排行柱状图     │  转化漏斗（额外展示）    │
  └──────────────────────┴───────────────────────┘

  配色: 全浅色系，柔和紫/蓝/绿/粉色调
  =====================================================
-->
<template>
  <div class="dashboard-page">
    <!-- ========== 页面标题栏 ========== -->
    <div class="dashboard-header">
      <div class="dashboard-header-left">
        <h2 class="dashboard-title">数据驾驶舱</h2>
        <p class="dashboard-subtitle">实时监控核心业务指标，洞察用户行为趋势</p>
      </div>
      <div class="dashboard-header-right">
        <el-tag type="info" size="small" effect="plain" class="refresh-tag">
          <el-icon><Timer /></el-icon>
          最后更新: {{ lastUpdateTime }}
        </el-tag>
        <el-button
          :loading="refreshing"
          :icon="Refresh"
          type="primary"
          plain
          size="small"
          @click="handleRefresh"
        >
          {{ refreshing ? '刷新中...' : '刷新数据' }}
        </el-button>
      </div>
    </div>

    <!-- ========== KPI 核心指标卡片（第一行 4个） ========== -->
    <div class="kpi-row">
      <div
        v-for="item in kpiCards1"
        :key="item.label"
        class="kpi-card"
        :style="{ '--kpi-color': item.color, '--kpi-bg': item.bgColor }"
      >
        <div class="kpi-card-left">
          <div class="kpi-card-label">{{ item.label }}</div>
          <div class="kpi-card-value">
            <!-- 使用 countup 效果展示数字 -->
            <span class="kpi-value-prefix" v-if="item.prefix">{{ item.prefix }}</span>
            <span>{{ item.displayValue }}</span>
          </div>
          <div class="kpi-card-trend" :class="item.trendClass">
            <el-icon>
              <component :is="item.trendIcon" />
            </el-icon>
            <span>{{ item.trendText }}</span>
          </div>
        </div>
        <div class="kpi-card-right">
          <div class="kpi-card-icon">
            <component :is="item.icon" :size="28" />
          </div>
        </div>
      </div>
    </div>

    <!-- KPI 指标卡片（第二行 4个） -->
    <div class="kpi-row">
      <div
        v-for="item in kpiCards2"
        :key="item.label"
        class="kpi-card kpi-card-sm"
        :style="{ '--kpi-color': item.color, '--kpi-bg': item.bgColor }"
      >
        <div class="kpi-card-left">
          <div class="kpi-card-label">{{ item.label }}</div>
          <div class="kpi-card-value kpi-card-value-sm">
            <span>{{ item.displayValue }}</span>
          </div>
        </div>
        <div class="kpi-card-right">
          <div class="kpi-card-icon kpi-card-icon-sm">
            <component :is="item.icon" :size="22" />
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 销售趋势折线图（全宽） ========== -->
    <el-card class="chart-card" shadow="never">
      <template #header>
        <div class="chart-card-header">
          <h3 class="chart-card-title">销售趋势分析</h3>
          <div class="chart-card-actions">
            <el-radio-group v-model="salesPeriod" size="small" @change="loadSalesTrend">
              <el-radio-button value="day">按日</el-radio-button>
              <el-radio-button value="week">按周</el-radio-button>
              <el-radio-button value="month">按月</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>
      <div ref="salesChartRef" class="chart-container"></div>
    </el-card>

    <!-- ========== 中间两栏：用户行为 + 用户分群 ========== -->
    <div class="chart-grid-2">
      <!-- 用户行为 PV/UV 趋势 -->
      <el-card class="chart-card" shadow="never">
        <template #header>
          <div class="chart-card-header">
            <h3 class="chart-card-title">用户行为趋势 PV/UV</h3>
          </div>
        </template>
        <div ref="behaviorChartRef" class="chart-container chart-container-md"></div>
      </el-card>

      <!-- 用户分群分布 -->
      <el-card class="chart-card" shadow="never">
        <template #header>
          <div class="chart-card-header">
            <h3 class="chart-card-title">用户分群分布</h3>
          </div>
        </template>
        <div class="segment-chart-wrapper">
          <div ref="segmentChartRef" class="chart-container-segment"></div>
          <!-- 图例列表 -->
          <div class="segment-legend">
            <div
              v-for="(item, index) in segmentData"
              :key="item.name"
              class="segment-legend-item"
            >
              <span class="segment-dot" :style="{ background: segmentColors[index] }"></span>
              <span class="segment-name">{{ item.name }}</span>
              <span class="segment-value">{{ item.value }}人</span>
              <span class="segment-percent">{{ getSegmentPercent(item.value) }}%</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- ========== 底部两栏：商品排行 + 转化漏斗 ========== -->
    <div class="chart-grid-2">
      <!-- 商品销售排行 -->
      <el-card class="chart-card" shadow="never">
        <template #header>
          <div class="chart-card-header">
            <h3 class="chart-card-title">商品销售排行 TOP10</h3>
            <div class="chart-card-actions">
              <el-radio-group v-model="rankSortBy" size="small" @change="loadProductRanking">
                <el-radio-button value="sales">按销量</el-radio-button>
                <el-radio-button value="revenue">按销售额</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        <div ref="rankingChartRef" class="chart-container chart-container-md"></div>
      </el-card>

      <!-- 行为转化漏斗（额外展示，调用 /behaviors/funnel 接口预留） -->
      <el-card class="chart-card" shadow="never">
        <template #header>
          <div class="chart-card-header">
            <h3 class="chart-card-title">行为转化漏斗</h3>
            <span class="chart-card-badge">浏览→加购→购买</span>
          </div>
        </template>
        <div class="funnel-wrapper">
          <template v-for="(step, index) in funnelSteps" :key="step.name">
            <div
              class="funnel-row"
              :style="{ transitionDelay: index * 0.08 + 's' }"
            >
              <div class="funnel-row-head">
                <span class="funnel-name">{{ step.name }}</span>
                <span class="funnel-count">{{ step.count.toLocaleString() }}</span>
                <span class="funnel-rate">{{ funnelPercent(step.rate) }}</span>
              </div>
              <div class="funnel-track">
                <div
                  class="funnel-fill"
                  :style="{
                    width: funnelWidth(step.rate),
                    background: funnelColors[index],
                  }"
                ></div>
              </div>
            </div>
            <div v-if="index < funnelSteps.length - 1" class="funnel-connector">
              <span>转化 {{ stepConversionPercent(index) }}</span>
            </div>
          </template>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// 数据驾驶舱页面逻辑
// =====================================================
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'
import {
  Timer, Refresh, Coin, List, DataAnalysis, TrendCharts,
  User, ShoppingCart, Wallet, Trophy, ShoppingCartFull,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

// 引入数据驾驶舱 API
import {
  getMetrics,
  getSalesTrend,
  getUserBehavior,
  getProductRanking,
  getUserSegments,
} from '@/api/dashboard'
import { getBehaviorFunnel } from '@/api/behavior'
import type {
  DashboardMetrics,
  SalesTrendData,
  BehaviorTrendData,
  ProductRankingItem,
  UserSegmentItem,
} from '@/types/api'

type DashboardCache = {
  loaded: boolean
  updatedAt: string
  metrics: DashboardMetrics | null
  salesTrend: Record<string, SalesTrendData>
  behavior: BehaviorTrendData | null
  ranking: Record<string, ProductRankingItem[]>
  segments: UserSegmentItem[] | null
  funnel: Array<{ name: string; count: number; rate: number }> | null
}

const dashboardCache: DashboardCache = {
  loaded: false,
  updatedAt: '',
  metrics: null,
  salesTrend: {},
  behavior: null,
  ranking: {},
  segments: null,
  funnel: null,
}

// ==================== 依赖注入 ====================

const authStore = useAuthStore()

// ==================== 状态定义 ====================

/** 刷新加载状态 */
const refreshing = ref(false)

/** 最后更新时间 */
const lastUpdateTime = ref('--')

/** 核心指标数据 */
const metrics = ref<DashboardMetrics | null>(null)

/** 销售趋势数据 */
const salesTrendData = ref<SalesTrendData | null>(null)

/** 用户行为数据 */
const behaviorData = ref<BehaviorTrendData | null>(null)

/** 商品排行数据 */
const productRanking = ref<ProductRankingItem[]>([])

/** 用户分群数据 */
const segmentData = ref<UserSegmentItem[]>([])

/** 销售趋势时间粒度 */
const salesPeriod = ref('day')

/** 商品排行排序方式 */
const rankSortBy = ref('sales')

// ==================== 图表 DOM 引用 ====================

const salesChartRef = ref<HTMLDivElement | null>(null)
const behaviorChartRef = ref<HTMLDivElement | null>(null)
const segmentChartRef = ref<HTMLDivElement | null>(null)
const rankingChartRef = ref<HTMLDivElement | null>(null)

// ==================== 图表实例 ====================

let salesChart: echarts.ECharts | null = null
let behaviorChart: echarts.ECharts | null = null
let segmentChart: echarts.ECharts | null = null
let rankingChart: echarts.ECharts | null = null

// ==================== 配色常量 ====================

/** 蓝白专业风图表配色 */
const chartColors = [
  '#3b82f6',  // 蓝
  '#10b981',  // 翠绿
  '#06b6d4',  // 青色
  '#f59e0b',  // 琥珀
  '#ef4444',  // 红
  '#6366f1',  // 靛蓝
  '#14b8a6',  // 蓝绿
  '#8b5cf6',  // 紫
  '#0ea5e9',  // 天蓝
  '#f97316',  // 橙
]

/** 用户分群饼图颜色 */
const segmentColors = ['#3b82f6', '#10b981', '#06b6d4', '#f59e0b', '#ef4444']

/** 转化漏斗颜色 */
const funnelColors = [
  'linear-gradient(90deg, #2563eb, #3b82f6)',
  'linear-gradient(90deg, #3b82f6, #06b6d4)',
  'linear-gradient(90deg, #06b6d4, #10b981)',
]

// ==================== 转化漏斗数据 ===================

/** 行为转化漏斗步骤 */
const funnelSteps = ref([
  { name: '浏览商品', count: 0, rate: 1.0 },
  { name: '加入购物车', count: 0, rate: 0 },
  { name: '完成购买', count: 0, rate: 0 },
])

const clampRate = (rate: number) => Math.max(0, Math.min(Number(rate) || 0, 1))
const funnelWidth = (rate: number) => `${Math.max(8, clampRate(rate) * 100)}%`
const funnelPercent = (rate: number) => `${(clampRate(rate) * 100).toFixed(1)}%`
const stepConversionPercent = (index: number) => {
  const current = funnelSteps.value[index]?.count || 0
  const next = funnelSteps.value[index + 1]?.count || 0
  if (!current) return '0.0%'
  return `${Math.min((next / current) * 100, 100).toFixed(1)}%`
}

/** 加载漏斗数据 */
const loadFunnelData = async (force: boolean | string = false) => {
  if (force !== true && dashboardCache.funnel) {
    funnelSteps.value = dashboardCache.funnel
    return
  }
  try {
    const res = await getBehaviorFunnel()
    if (res.data?.steps) {
      funnelSteps.value = res.data.steps
      dashboardCache.funnel = res.data.steps
    }
  } catch {
    // 保持默认值
  }
}

// ==================== KPI 卡片数据 ====================

/** 第一行 KPI 卡片 - 核心业务指标 */
const kpiCards1 = computed(() => {
  const m = metrics.value
  return [
    {
      label: '销售总额',
      displayValue: m ? `¥${(m.total_sales / 10000).toFixed(2)}万` : '--',
      icon: Coin,
      color: '#3b82f6',
      bgColor: 'rgba(59,130,246,0.08)',
      prefix: '',
      trendIcon: TrendCharts,
      trendText: '较上月 +12.5%',
      trendClass: 'trend-up',
    },
    {
      label: '订单总量',
      displayValue: m ? m.total_orders.toLocaleString() : '--',
      icon: List,
      color: '#10b981',
      bgColor: 'rgba(16,185,129,0.08)',
      prefix: '',
      trendIcon: TrendCharts,
      trendText: '较上月 +8.3%',
      trendClass: 'trend-up',
    },
    {
      label: '客单价',
      displayValue: m ? `¥${m.avg_order_value.toFixed(2)}` : '--',
      icon: Wallet,
      color: '#06b6d4',
      bgColor: 'rgba(6,182,212,0.08)',
      prefix: '',
      trendIcon: TrendCharts,
      trendText: '较上月 +3.6%',
      trendClass: 'trend-up',
    },
    {
      label: '用户总数',
      displayValue: m ? m.total_users.toLocaleString() : '--',
      icon: User,
      color: '#f59e0b',
      bgColor: 'rgba(245,158,11,0.08)',
      prefix: '',
      trendIcon: TrendCharts,
      trendText: '较上月 +15.2%',
      trendClass: 'trend-up',
    },
  ]
})

/** 第二行 KPI 卡片 - 今日/效率指标 */
const kpiCards2 = computed(() => {
  const m = metrics.value
  return [
    {
      label: '今日销售额',
      displayValue: m ? `¥${m.today_sales.toLocaleString()}` : '--',
      icon: ShoppingCart,
      color: '#a29bfe',
      bgColor: 'rgba(162,155,254,0.08)',
    },
    {
      label: '今日订单量',
      displayValue: m ? `${m.today_orders} 笔` : '--',
      icon: ShoppingCartFull,
      color: '#55efc4',
      bgColor: 'rgba(85,239,196,0.08)',
    },
    {
      label: '转化率',
      displayValue: m ? `${(m.conversion_rate * 100).toFixed(2)}%` : '--',
      icon: DataAnalysis,
      color: '#fd79a8',
      bgColor: 'rgba(253,121,168,0.08)',
    },
    {
      label: '复购率',
      displayValue: m ? `${(m.repurchase_rate * 100).toFixed(2)}%` : '--',
      icon: Trophy,
      color: '#e17055',
      bgColor: 'rgba(225,112,85,0.08)',
    },
  ]
})

// ==================== 工具函数 ====================

/** 计算分群百分比（安全除零处理） */
const getSegmentPercent = (value: number): string => {
  const total = segmentData.value?.reduce((sum, item) => sum + (item.value || 0), 0) || 0
  if (total <= 0) return '0.0'
  return ((value / total) * 100).toFixed(1)
}

/** 格式化更新时间 */
const updateRefreshTime = (): void => {
  const now = new Date()
  lastUpdateTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
}

/** ECharts 通用浅色主题配置 */
const getBaseChartOption = (): EChartsOption => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderColor: '#e8ecf1',
    borderWidth: 1,
    textStyle: { color: '#2d3436', fontSize: 13 },
    padding: [12, 16],
    extraCssText: 'border-radius: 10px; box-shadow: 0 4px 16px rgba(108,92,231,0.08);',
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true,
  },
  legend: {
    textStyle: { color: '#636e72', fontSize: 12 },
    itemWidth: 10,
    itemHeight: 10,
    itemGap: 20,
    borderRadius: 3,
  },
})

// ==================== 图表渲染函数 ====================

/**
 * 渲染销售趋势折线图
 * 对应 API 9.2: GET /dashboard/sales-trend
 */
const renderSalesChart = (): void => {
  if (!salesChartRef.value || !salesTrendData.value) return

  if (!salesChart) {
    salesChart = echarts.init(salesChartRef.value)
  }

  const data = salesTrendData.value
  const formatSalesDate = (val: string) => {
    if (salesPeriod.value === 'month') return val
    if (salesPeriod.value === 'week') return val
    return val.includes('-') ? val.slice(5) : val
  }

  const option: EChartsOption = {
    ...getBaseChartOption(),
    grid: {
      left: '3%',
      right: '4%',
      bottom: '9%',
      top: '12%',
      containLabel: true,
    },
    tooltip: {
      ...(getBaseChartOption().tooltip as object),
      axisPointer: {
        type: 'cross',
        crossStyle: { color: '#999' },
        label: {
          backgroundColor: '#3b82f6',
          borderRadius: 6,
        },
      },
    },
    legend: {
      data: ['销售额(元)', '订单量(笔)', '活跃用户(人)'],
      top: 0,
      textStyle: { color: '#636e72', fontSize: 12 },
      itemWidth: 14,
      itemHeight: 3,
      itemGap: 24,
    },
    xAxis: {
      type: 'category',
      data: data.dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#e8ecf1' } },
      axisTick: { show: false },
      axisLabel: {
        show: true,
        interval: 0,
        color: '#b2bec3',
        fontSize: 11,
        margin: 12,
        hideOverlap: true,
        formatter: formatSalesDate,
      },
      splitLine: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '金额(元)',
        nameTextStyle: { color: '#b2bec3', fontSize: 11, padding: [0, 40, 0, 0] },
        axisLabel: {
          color: '#b2bec3',
          fontSize: 11,
          formatter: (val: number) => {
            if (val >= 10000) return `${(val / 10000).toFixed(1)}万`
            return val.toString()
          },
        },
        splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } },
      },
      {
        type: 'value',
        name: '数量',
        nameTextStyle: { color: '#b2bec3', fontSize: 11, padding: [0, 0, 0, 40] },
        axisLabel: { color: '#b2bec3', fontSize: 11 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '销售额(元)',
        type: 'line',
        data: data.sales,
        yAxisIndex: 0,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          color: '#3b82f6',
          width: 3,
          shadowBlur: 8,
          shadowColor: 'rgba(59,130,246,0.3)',
        },
        itemStyle: {
          color: '#3b82f6',
          borderColor: '#fff',
          borderWidth: 2,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59,130,246,0.15)' },
            { offset: 1, color: 'rgba(59,130,246,0)' },
          ]),
        },
      },
      {
        name: '订单量(笔)',
        type: 'line',
        data: data.orders,
        yAxisIndex: 1,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 6,
        lineStyle: {
          color: '#10b981',
          width: 2.5,
          shadowBlur: 6,
          shadowColor: 'rgba(16,185,129,0.3)',
        },
        itemStyle: {
          color: '#00b894',
          borderColor: '#fff',
          borderWidth: 2,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16,185,129,0.1)' },
            { offset: 1, color: 'rgba(16,185,129,0)' },
          ]),
        },
      },
      {
        name: '活跃用户(人)',
        type: 'line',
        data: data.users,
        yAxisIndex: 1,
        smooth: true,
        symbol: 'triangle',
        symbolSize: 8,
        lineStyle: {
          color: '#74b9ff',
          width: 2.5,
          shadowBlur: 6,
          shadowColor: 'rgba(6,182,212,0.3)',
          type: 'dashed',
        },
        itemStyle: {
          color: '#74b9ff',
          borderColor: '#fff',
          borderWidth: 2,
        },
      },
    ],
  }

  salesChart.setOption(option, true)
}

/**
 * 渲染用户行为 PV/UV 趋势图（柱状图 + 折线图组合）
 * 对应 API 9.3: GET /dashboard/user-behavior
 */
const renderBehaviorChart = (): void => {
  if (!behaviorChartRef.value || !behaviorData.value) return

  if (!behaviorChart) {
    behaviorChart = echarts.init(behaviorChartRef.value)
  }

  const data = behaviorData.value

  const option: EChartsOption = {
    ...getBaseChartOption(),
    tooltip: {
      ...(getBaseChartOption().tooltip as object),
      trigger: 'axis',
    },
    legend: {
      data: ['PV(页面访问)', 'UV(独立访客)', '加购数', '购买数'],
      bottom: 0,
      textStyle: { color: '#636e72', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.dates,
      axisLabel: {
        color: '#b2bec3',
        fontSize: 10,
        formatter: (val: string) => val.slice(5),
        rotate: 45,
      },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e8ecf1' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#b2bec3',
        fontSize: 11,
        formatter: (val: number) => (val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val.toString()),
      },
      splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } },
    },
    series: [
      {
        name: 'PV(页面访问)',
        type: 'bar',
        data: data.pv,
        barWidth: 6,
        itemStyle: {
          color: 'rgba(108,92,231,0.25)',
          borderRadius: [3, 3, 0, 0],
        },
        emphasis: {
          itemStyle: { color: 'rgba(108,92,231,0.5)' },
        },
      },
      {
        name: 'UV(独立访客)',
        type: 'line',
        data: data.uv,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#6c5ce7',
          width: 2.5,
          shadowBlur: 6,
          shadowColor: 'rgba(108,92,231,0.25)',
        },
      },
      {
        name: '加购数',
        type: 'line',
        data: data.cart_count,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#00b894',
          width: 2,
          shadowBlur: 4,
          shadowColor: 'rgba(0,184,148,0.2)',
        },
      },
      {
        name: '购买数',
        type: 'line',
        data: data.buy_count,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#e17055',
          width: 2,
          shadowBlur: 4,
          shadowColor: 'rgba(225,112,85,0.2)',
        },
      },
    ],
  }

  behaviorChart.setOption(option)
}

/**
 * 渲染用户分群环形图
 * 对应 API 9.5: GET /dashboard/user-segments
 */
const renderSegmentChart = (): void => {
  if (!segmentChartRef.value || segmentData.value.length === 0) return

  if (!segmentChart) {
    segmentChart = echarts.init(segmentChartRef.value)
  }

  const total = segmentData.value.reduce((sum, item) => sum + item.value, 0)

  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e8ecf1',
      borderWidth: 1,
      textStyle: { color: '#2d3436', fontSize: 13 },
      formatter: '{b}: {c}人 ({d}%)',
      padding: [10, 14],
      extraCssText: 'border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);',
    },
    series: [
      {
        name: '用户分群',
        type: 'pie',
        radius: ['55%', '78%'],  // 环形图
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 0,
          borderWidth: 0,
        },
        label: {
          show: false,
        },
        emphasis: {
          scale: false,
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
          },
          scaleSize: 8,
        },
        labelLine: {
          show: false,
        },
        data: segmentData.value.map((item, index) => ({
          value: item.value,
          name: item.name,
          itemStyle: {
            color: segmentColors[index],
          },
        })),
      },
      // 中心文字
      {
        type: 'pie',
        radius: ['0%', '0%'],
        center: ['50%', '50%'],
        label: {
          position: 'inner',
          fontSize: 18,
          fontWeight: 700,
          color: '#2d3436',
          formatter: `总用户\n{count|${total}人}`,
          rich: {
            count: {
              fontSize: 24,
              fontWeight: 700,
              color: '#6c5ce7',
              lineHeight: 32,
            },
          },
        },
        data: [{ value: 1, name: '' }],
      },
    ],
  }

  segmentChart.setOption(option, true)
}

/**
 * 渲染商品销售排行柱状图
 * 对应 API 9.4: GET /dashboard/product-ranking
 */
const renderRankingChart = (): void => {
  if (!rankingChartRef.value || productRanking.value.length === 0) return

  if (!rankingChart) {
    rankingChart = echarts.init(rankingChartRef.value)
  }

  const isRevenue = rankSortBy.value === 'revenue'
  // 反转数据让大的在上面
  const sorted = [...productRanking.value].sort((a, b) => {
    const valA = isRevenue ? a.revenue : a.sales
    const valB = isRevenue ? b.revenue : b.sales
    return valA - valB  // 升序，渲染时从上到下越来越大
  })

  const names = sorted.map((item) => item.name)
  const values = sorted.map((item) => (isRevenue ? item.revenue : item.sales))
  const maxVal = Math.max(...values)

  const option: EChartsOption = {
    ...getBaseChartOption(),
    tooltip: {
      ...(getBaseChartOption().tooltip as object),
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        const val = isRevenue ? `¥${p.value.toLocaleString()}` : `${p.value} 件`
        return `${p.name}<br/>${val}`
      },
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      top: '5%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#b2bec3',
        fontSize: 11,
        formatter: (val: number) => {
          if (isRevenue && val >= 10000) return `${(val / 10000).toFixed(0)}万`
          return val.toString()
        },
      },
      splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    yAxis: {
      type: 'category',
      data: names,
      inverse: true,
      axisLabel: {
        color: '#636e72',
        fontSize: 11,
        width: 90,
        overflow: 'truncate',
        ellipsis: '...',
      },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: values.map((val, index) => ({
          value: val,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: chartColors[index % chartColors.length] },
              { offset: 1, color: chartColors[index % chartColors.length] + '80' },
            ]),
            borderRadius: [0, 8, 8, 0],
          },
        })),
        barWidth: 18,
        label: {
          show: true,
          position: 'right',
          color: '#636e72',
          fontSize: 11,
          formatter: (params: any) => {
            const val = params.value
            if (isRevenue) return val >= 10000 ? `${(val / 10000).toFixed(1)}万` : `¥${val}`
            return `${val}件`
          },
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 12,
            shadowColor: 'rgba(108,92,231,0.2)',
          },
        },
      },
    ],
  }

  rankingChart.setOption(option)
}

// ==================== 数据加载函数 ====================

/** 加载核心指标 */
const loadMetrics = async (force: boolean | string = false): Promise<void> => {
  if (force !== true && dashboardCache.metrics) {
    metrics.value = dashboardCache.metrics
    return
  }
  try {
    const res = await getMetrics()
    metrics.value = res.data
    dashboardCache.metrics = res.data
  } catch {
    // 错误已由 request 拦截器处理
  }
}

/** 加载销售趋势 */
const loadSalesTrend = async (force: boolean | string = false): Promise<void> => {
  if (force !== true && dashboardCache.salesTrend[salesPeriod.value]) {
    salesTrendData.value = dashboardCache.salesTrend[salesPeriod.value]
    await nextTick()
    renderSalesChart()
    return
  }
  try {
    const res = await getSalesTrend(salesPeriod.value)
    salesTrendData.value = res.data
    dashboardCache.salesTrend[salesPeriod.value] = res.data
    await nextTick()
    renderSalesChart()
  } catch {
    // 忽略
  }
}

/** 加载用户行为趋势 */
const loadUserBehavior = async (force: boolean | string = false): Promise<void> => {
  if (force !== true && dashboardCache.behavior) {
    behaviorData.value = dashboardCache.behavior
    await nextTick()
    renderBehaviorChart()
    return
  }
  try {
    const res = await getUserBehavior()
    behaviorData.value = res.data
    dashboardCache.behavior = res.data
    await nextTick()
    renderBehaviorChart()
  } catch {
    // 忽略
  }
}

/** 加载商品排行 */
const loadProductRanking = async (force: boolean | string = false): Promise<void> => {
  if (force !== true && dashboardCache.ranking[rankSortBy.value]) {
    productRanking.value = dashboardCache.ranking[rankSortBy.value]
    await nextTick()
    renderRankingChart()
    return
  }
  try {
    const res = await getProductRanking(10, rankSortBy.value)
    productRanking.value = res.data.products
    dashboardCache.ranking[rankSortBy.value] = res.data.products
    await nextTick()
    renderRankingChart()
  } catch {
    // 忽略
  }
}

/** 加载用户分群 */
const loadUserSegments = async (force: boolean | string = false): Promise<void> => {
  if (force !== true && dashboardCache.segments) {
    segmentData.value = dashboardCache.segments
    await nextTick()
    renderSegmentChart()
    return
  }
  try {
    const res = await getUserSegments()
    segmentData.value = res.data.segments
    dashboardCache.segments = res.data.segments
    await nextTick()
    renderSegmentChart()
  } catch {
    // 忽略
  }
}

/** 一次性加载所有数据 */
const applyDashboardCache = async (): Promise<void> => {
  if (dashboardCache.metrics) metrics.value = dashboardCache.metrics
  if (dashboardCache.salesTrend[salesPeriod.value]) salesTrendData.value = dashboardCache.salesTrend[salesPeriod.value]
  if (dashboardCache.behavior) behaviorData.value = dashboardCache.behavior
  if (dashboardCache.ranking[rankSortBy.value]) productRanking.value = dashboardCache.ranking[rankSortBy.value]
  if (dashboardCache.segments) segmentData.value = dashboardCache.segments
  if (dashboardCache.funnel) funnelSteps.value = dashboardCache.funnel
  if (dashboardCache.updatedAt) lastUpdateTime.value = dashboardCache.updatedAt

  await nextTick()
  renderSalesChart()
  renderBehaviorChart()
  renderRankingChart()
  renderSegmentChart()
}

const loadAllData = async (force = false): Promise<void> => {
  if (!force && dashboardCache.loaded) {
    await applyDashboardCache()
    return
  }

  let errorCount = 0
  const tasks = [
    loadMetrics(force), loadSalesTrend(force), loadUserBehavior(force),
    loadProductRanking(force), loadUserSegments(force), loadFunnelData(force),
  ]
  const results = await Promise.allSettled(tasks)
  results.forEach(r => { if (r.status === 'rejected') errorCount++ })

  updateRefreshTime()
  dashboardCache.loaded = true
  dashboardCache.updatedAt = lastUpdateTime.value
  return errorCount > 0 ? Promise.reject(errorCount) : Promise.resolve()
}

/** 刷新按钮处理 */
const handleRefresh = async (): Promise<void> => {
  refreshing.value = true
  try {
    await loadAllData(true)
    ElMessage.success('数据已刷新')
  } catch (errorCount: any) {
    ElMessage.warning(`数据已刷新，但 ${errorCount} 个接口加载失败`)
  } finally {
    refreshing.value = false
  }
}

// ==================== 监听窗口大小变化 ====================

/** 窗口大小变化时重新渲染所有图表 */
const handleResize = (): void => {
  salesChart?.resize()
  behaviorChart?.resize()
  segmentChart?.resize()
  rankingChart?.resize()
}

// ==================== 生命周期 ====================

onMounted(async () => {
  // 加载所有数据
  await loadAllData()

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  // 销毁所有图表实例，释放内存
  salesChart?.dispose()
  behaviorChart?.dispose()
  segmentChart?.dispose()
  rankingChart?.dispose()

  // 移除 resize 监听
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
/* =====================================================
   数据驾驶舱页面样式 - 浅色系炫酷设计
   ===================================================== */

/* ==================== 页面容器 ==================== */
.dashboard-page {
  padding: 4px;
  max-width: 1400px;
  margin: 0 auto;
  animation: dashboard-fadeIn 0.6s ease-out;
}

@keyframes dashboard-fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ==================== 页面标题栏 ==================== */
.dashboard-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.dashboard-header-left {
  .dashboard-title {
    font-size: 24px;
    font-weight: 700;
    color: #2d3436;
    letter-spacing: 2px;
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .dashboard-subtitle {
    margin-top: 4px;
    font-size: 13px;
    color: #b2bec3;
  }
}

.dashboard-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 4px;
}

.refresh-tag {
  font-size: 12px;

  .el-icon {
    margin-right: 4px;
    font-size: 11px;
  }
}

/* ==================== KPI 指标卡片 ==================== */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.kpi-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 24px;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid var(--border-light);
  cursor: default;
  position: relative;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);

  // 左侧彩色装饰条
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 36px;
    background: var(--kpi-color);
    border-radius: 0 3px 3px 0;
    opacity: 0.6;
    transition: height 0.3s ease;
  }

  &:hover {
    transform: translateY(-4px);
    box-shadow:
      0 12px 32px rgba(108, 92, 231, 0.08),
      0 4px 8px rgba(0, 0, 0, 0.03);

    &::before {
      height: 48px;
      opacity: 1;
    }

    .kpi-card-icon {
      transform: scale(1.1);
    }
  }

  &.kpi-card-sm {
    padding: 18px 20px;
  }
}

.kpi-card-left {
  position: relative;
  z-index: 1;
}

.kpi-card-label {
  font-size: 13px;
  color: #b2bec3;
  margin-bottom: 8px;
  font-weight: 500;
}

.kpi-card-value {
  font-size: 28px;
  font-weight: 800;
  color: #2d3436;
  letter-spacing: -0.5px;
  line-height: 1.2;

  &.kpi-card-value-sm {
    font-size: 22px;
  }
}

.kpi-value-prefix {
  font-size: 16px;
  font-weight: 500;
  color: #b2bec3;
  margin-right: 2px;
}

.kpi-card-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  font-size: 12px;

  .el-icon {
    font-size: 14px;
  }
}

.trend-up {
  color: #00b894;
}

.trend-down {
  color: #e17055;
}

.kpi-card-right {
  position: relative;
  z-index: 1;
}

.kpi-card-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--kpi-bg);
  color: var(--kpi-color);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.35s ease;

  &.kpi-card-icon-sm {
    width: 44px;
    height: 44px;
    border-radius: 12px;
  }
}

/* ==================== 图表卡片 ==================== */
.chart-card {
  margin-bottom: 16px;
  border: 1px solid var(--border-light);
  border-radius: 16px;
  overflow: hidden;
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: var(--shadow-md);
  }

  :deep(.el-card__header) {
    padding: 18px 24px;
    border-bottom: 1px solid var(--border-light);
    background: rgba(255, 255, 255, 0.5);
  }

  :deep(.el-card__body) {
    padding: 20px;
  }
}

.chart-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chart-card-title {
  font-size: 16px;
  font-weight: 700;
  color: #2d3436;
}

.chart-card-badge {
  font-size: 12px;
  color: #a29bfe;
  background: rgba(162, 155, 254, 0.08);
  padding: 4px 10px;
  border-radius: 20px;
}

/* 图表容器 */
.chart-container {
  width: 100%;
  height: 380px;
}

.chart-container-md {
  height: 320px;
}

.chart-container-segment {
  width: 240px;
  height: 240px;
  flex-shrink: 0;
}

/* 两栏网格布局 */
.chart-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* ==================== 用户分群图例 ==================== */
.segment-chart-wrapper {
  display: flex;
  align-items: center;
  gap: 24px;
}

.segment-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.segment-legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background 0.2s;

  &:hover {
    background: rgba(108, 92, 231, 0.04);
  }
}

.segment-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

.segment-name {
  font-size: 13px;
  color: #636e72;
  flex: 1;
}

.segment-value {
  font-size: 13px;
  color: #2d3436;
  font-weight: 600;
  min-width: 40px;
  text-align: right;
}

.segment-percent {
  font-size: 12px;
  color: #b2bec3;
  min-width: 45px;
  text-align: right;
}

/* ==================== 转化漏斗 ==================== */
.funnel-wrapper {
  padding: 18px 22px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.funnel-row {
  animation: funnel-appear 0.6s ease-out backwards;
}

@keyframes funnel-appear {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

.funnel-row-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.funnel-name {
  font-size: 14px;
  font-weight: 600;
  color: #2d3436;
  white-space: nowrap;
}

.funnel-count {
  margin-left: auto;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.funnel-rate {
  min-width: 52px;
  text-align: right;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.funnel-track {
  width: 100%;
  height: 16px;
  overflow: hidden;
  border-radius: 999px;
  background: #eef2f7;
}

.funnel-fill {
  height: 100%;
  border-radius: inherit;
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.25);
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.funnel-connector {
  display: flex;
  justify-content: center;
  color: #94a3b8;
  font-size: 12px;
  line-height: 16px;

  span {
    padding: 2px 10px;
    border-radius: 999px;
    background: #f8fafc;
  }
}

/* ==================== 响应式适配 ==================== */
@media (max-width: 1200px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-grid-2 {
    grid-template-columns: 1fr;
  }

  .segment-chart-wrapper {
    flex-direction: column;
    align-items: center;
  }
}

@media (max-width: 768px) {
  .kpi-row {
    grid-template-columns: 1fr;
  }

  .dashboard-header {
    flex-direction: column;
  }

  .kpi-card-value {
    font-size: 24px;
  }

  .chart-container {
    height: 280px;
  }
}
</style>
