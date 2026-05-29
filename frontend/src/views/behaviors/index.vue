<!--
  =====================================================
  src/views/behaviors/index.vue
  行为分析页
  严格遵循 API 文档 6.1-6.4
  功能: 数据导入、列表查询、转化漏斗、PV/UV 趋势图
  =====================================================
-->
<template>
  <div class="behavior-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">行为分析</h2>
        <p class="page-subtitle">导入用户行为数据，分析转化漏斗与行为趋势</p>
      </div>
      <el-button type="primary" :icon="Upload" @click="handleImport">导入数据</el-button>
    </div>

    <!-- ========== 漏斗 + 趋势 双栏图表 ========== -->
    <div class="chart-row">
      <!-- 转化漏斗 -->
      <el-card class="chart-card" shadow="never">
        <template #header><div class="chart-hd"><h3>行为转化漏斗</h3><el-button :icon="Refresh" size="small" text @click="loadFunnel">刷新</el-button></div></template>
        <div ref="funnelChartRef" style="width:100%;height:340px"></div>
        <div class="funnel-stats" v-if="funnelData">
          <div class="funnel-stat" v-for="(s, i) in funnelData.steps" :key="s.name" :style="{ '--fc': ['#6c5ce7','#a29bfe','#00b894'][i] }">
            <div class="fs-val">{{ s.count.toLocaleString() }}</div>
            <div class="fs-label">{{ s.name }}</div>
            <div class="fs-rate">{{ (s.rate * 100).toFixed(1) }}%</div>
          </div>
        </div>
      </el-card>

      <!-- 行为趋势 -->
      <el-card class="chart-card" shadow="never">
        <template #header><div class="chart-hd"><h3>PV/UV 行为趋势</h3><el-radio-group v-model="trendMode" size="small" @change="loadTrend"><el-radio-button value="all">综合</el-radio-button><el-radio-button value="funnel">漏斗</el-radio-button></el-radio-group></div></template>
        <div ref="trendChartRef" style="width:100%;height:340px"></div>
      </el-card>
    </div>

    <!-- ========== 筛选 + 列表 ========== -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <el-select v-model="filterType" placeholder="行为类型" clearable style="width:130px" @change="handleSearch">
          <el-option v-for="(l, k) in typeLabels" :key="k" :label="l" :value="k" />
        </el-select>
        <el-input-number v-model="filterUserId" :min="0" placeholder="用户ID" controls-position="right" style="width:130px" @change="handleSearch" />
        <el-input-number v-model="filterProductId" :min="0" placeholder="商品ID" controls-position="right" style="width:130px" @change="handleSearch" />
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:240px" @change="handleSearch" />
        <el-button :icon="RefreshRight" @click="handleReset">重置</el-button>
      </div>
    </el-card>

    <el-card class="table-card" shadow="never">
      <el-table v-loading="loading" :data="list" stripe border row-key="id" max-height="450">
        <el-table-column prop="id" label="#" width="70" align="center" />
        <el-table-column prop="user_id" label="用户ID" width="90" align="center" />
        <el-table-column prop="product_id" label="商品ID" width="90" align="center" />
        <el-table-column label="行为类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="tagType(row.behavior_type)" effect="light" size="small">{{ typeLabels[row.behavior_type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pg.page" v-model:page-size="pg.ps" :total="pg.total" :page-sizes="[10,20,50]" layout="total,sizes,prev,pager,next" background @size-change="loadList" @current-change="loadList" />
      </div>
    </el-card>

    <!-- ========== 导入对话框 ========== -->
    <el-dialog v-model="importVisible" title="导入行为数据" width="500px" :close-on-click-modal="false">
      <el-upload ref="uploadRef" drag :auto-upload="false" :on-change="handleFileChange" accept=".xlsx,.xls,.csv" :limit="1">
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处 或 <em>点击上传</em></div>
        <template #tip><div class="el-upload__tip">支持 Excel(.xlsx/.xls) 和 CSV 格式</div></template>
      </el-upload>
      <div style="margin-top:16px">
        <span style="font-size:13px;color:#636e72;">导入模式：</span>
        <el-radio-group v-model="importMode"><el-radio value="append">追加</el-radio><el-radio value="replace">替换</el-radio></el-radio-group>
      </div>
      <template #footer>
        <el-button @click="importVisible = false">取 消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport" :disabled="!uploadFile">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'
import { Upload, Refresh, RefreshRight, UploadFilled } from '@element-plus/icons-vue'
import { getBehaviorList, getBehaviorFunnel, getBehaviorTrend, importBehaviors } from '@/api/behavior'
import type { BehaviorItem, FunnelData, BehaviorTrendData, BehaviorQueryParams } from '@/types/api'

const typeLabels: Record<string, string> = { view: '浏览', cart: '加购', favorite: '收藏', buy: '购买' }
const tagType = (t: string) => ({ view: '', cart: 'primary', favorite: 'warning', buy: 'success' })[t] || 'info'

// ==================== 状态 ====================
const loading = ref(false)
const list = ref<BehaviorItem[]>([])
const pg = reactive({ page: 1, ps: 10, total: 0 })
const filterType = ref(''); const filterUserId = ref<number | null>(null); const filterProductId = ref<number | null>(null)
const dateRange = ref<[string, string] | null>(null)
const trendMode = ref('all')
const funnelData = ref<FunnelData | null>(null)

// 导入
const importVisible = ref(false); const importing = ref(false); const importMode = ref('append'); const uploadFile = ref<File | null>(null)

// 图表
const funnelChartRef = ref<HTMLDivElement | null>(null); const trendChartRef = ref<HTMLDivElement | null>(null)
let funnelChart: echarts.ECharts | null = null; let trendChart: echarts.ECharts | null = null

const formatDate = (s: string) => s ? new Date(s).toLocaleString('zh-CN') : '--'
const buildQuery = (): BehaviorQueryParams => ({
  page: pg.page, page_size: pg.ps,
  behavior_type: filterType.value || undefined,
  user_id: filterUserId.value || undefined,
  product_id: filterProductId.value || undefined,
  start_date: dateRange.value?.[0], end_date: dateRange.value?.[1],
})

// ==================== 数据加载 ====================
const loadList = async () => { loading.value = true; try { const r = await getBehaviorList(buildQuery()); list.value = r.data.items; pg.total = r.data.total } catch { ElMessage.error('行为数据加载失败') } finally { loading.value = false } }
const handleSearch = () => { pg.page = 1; loadList() }
const handleReset = () => { filterType.value = ''; filterUserId.value = null; filterProductId.value = null; dateRange.value = null; pg.page = 1; loadList() }

// ==================== 图表渲染 ====================
const loadFunnel = async () => {
  try { const r = await getBehaviorFunnel(); funnelData.value = r.data; await nextTick(); renderFunnel() } catch { ElMessage.error('漏斗数据加载失败') }
}

const renderFunnel = () => {
  if (!funnelChartRef.value || !funnelData.value) return
  if (!funnelChart) funnelChart = echarts.init(funnelChartRef.value)
  const d = funnelData.value.steps
  const opt: EChartsOption = {
    tooltip: { trigger: 'item', backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e8ecf1', textStyle: { color: '#2d3436' }, formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'funnel', left: '15%', right: '15%', top: 20, bottom: 20, width: '70%', minSize: '25%', gap: 6,
      label: { show: true, position: 'inside', fontSize: 14, color: '#fff' },
      data: d.map((s, i) => ({ name: s.name, value: s.count, itemStyle: { color: ['#6c5ce7', '#a29bfe', '#00b894'][i], borderRadius: 4 } })),
    }],
  }
  funnelChart.setOption(opt)
}

const loadTrend = async () => {
  try { const r = await getBehaviorTrend(30); await nextTick(); renderTrend(r.data) } catch {/* */}
}

const renderTrend = (d: BehaviorTrendData) => {
  if (!trendChartRef.value) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)

  const series: any[] = trendMode.value === 'all'
    ? [
      { name: 'PV', type: 'bar', data: d.pv, barWidth: 6, itemStyle: { color: 'rgba(108,92,231,0.2)', borderRadius: [3,3,0,0] } },
      { name: 'UV', type: 'line', data: d.uv, smooth: true, symbol: 'none', lineStyle: { color: '#6c5ce7', width: 2.5 } },
    ]
    : [
      { name: '浏览', type: 'line', data: d.view_count, smooth: true, symbol: 'none', lineStyle: { color: '#6c5ce7', width: 2 } },
      { name: '加购', type: 'line', data: d.cart_count, smooth: true, symbol: 'none', lineStyle: { color: '#00b894', width: 2 } },
      { name: '购买', type: 'line', data: d.buy_count, smooth: true, symbol: 'none', lineStyle: { color: '#e17055', width: 2 } },
    ]

  const opt: EChartsOption = {
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e8ecf1', textStyle: { color: '#2d3436', fontSize: 13 }, padding: [10,14], extraCssText: 'border-radius:8px;' },
    legend: { data: series.map((s: any) => s.name), bottom: 0, textStyle: { color: '#636e72', fontSize: 11 } },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: { type: 'category', data: d.dates, axisLabel: { color: '#b2bec3', fontSize: 10, formatter: (v: string) => v.slice(5) } },
    yAxis: { type: 'value', axisLabel: { color: '#b2bec3', fontSize: 11 }, splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } } },
    series,
  }
  trendChart.setOption(opt)
}

// ==================== 导入 ====================
const handleImport = () => { importVisible.value = true; uploadFile.value = null }
const handleFileChange = (file: any) => { uploadFile.value = file.raw }

const doImport = async () => {
  if (!uploadFile.value) { ElMessage.warning('请选择文件'); return }
  importing.value = true
  try {
    const fd = new FormData(); fd.append('file', uploadFile.value); fd.append('mode', importMode.value)
    const r = await importBehaviors(fd)
    ElMessage.success(r.message + ` — 导入 ${r.data.imported_count} 条，跳过 ${r.data.skipped_count} 条`)
    importVisible.value = false; loadList(); loadFunnel(); loadTrend()
  } catch {/* */} finally { importing.value = false }
}

// ==================== 生命周期 ====================
const handleResize = () => { funnelChart?.resize(); trendChart?.resize() }
onMounted(() => { loadList(); loadFunnel(); loadTrend(); window.addEventListener('resize', handleResize) })
onBeforeUnmount(() => { funnelChart?.dispose(); trendChart?.dispose(); window.removeEventListener('resize', handleResize) })
</script>

<style lang="scss" scoped>
.behavior-page { max-width: 1500px; margin: 0 auto; animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; background: linear-gradient(135deg, #6c5ce7, #a29bfe); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.page-subtitle { font-size: 13px; color: #b2bec3; margin-top: 4px; }

.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.chart-card { border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--border-light); }
  :deep(.el-card__body) { padding: 16px; }
}
.chart-hd { display: flex; justify-content: space-between; align-items: center; h3 { margin: 0; font-size: 15px; font-weight: 700; color: #2d3436; } }

.funnel-stats { display: flex; justify-content: center; gap: 40px; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-light); }
.funnel-stat { text-align: center; .fs-val { font-size: 22px; font-weight: 800; color: var(--fc); } .fs-label { font-size: 12px; color: #636e72; margin-top: 2px; } .fs-rate { font-size: 11px; color: #b2bec3; } }

.filter-card { margin-bottom: 16px; border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__body) { padding: 14px 20px; }
}
.filter-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }

.table-card { border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__body) { padding: 0; }
}
:deep(.el-table) { --el-table-border-color: #f0f3f7; th.el-table__cell { background: rgba(108,92,231,0.03); color: #636e72; font-weight: 600; font-size: 13px; } }
.pagination-wrap { display: flex; justify-content: flex-end; padding: 12px 20px; }

@media (max-width: 992px) { .chart-row { grid-template-columns: 1fr; } .filter-row { flex-direction: column; } }
</style>
