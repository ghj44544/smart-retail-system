<!--
  =====================================================
  src/views/products/index.vue
  商品管理列表页
  严格遵循 API 文档 4.1-4.7
  功能: 搜索筛选、分类过滤、CRUD、热门排行侧栏
  =====================================================
-->
<template>
  <div class="product-page">
    <!-- ========== 页面标题 ========== -->
    <div class="page-header">
      <div>
        <h2 class="page-title">商品管理</h2>
        <p class="page-subtitle">管理平台商品信息，查看热门排行与库存状态</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="handleAdd">新增商品</el-button>
    </div>

    <!-- ========== 统计卡片 ========== -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in statCards" :key="s.label" :style="{ '--stat-color': s.color }">
        <div class="stat-icon" :style="{ background: s.bg }">
          <component :is="s.icon" :size="20" />
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- ========== 主内容区 ========== -->
    <div class="product-layout">
      <!-- 左侧表格区 -->
      <div class="product-main">
        <!-- 搜索筛选 -->
        <el-card class="filter-card" shadow="never">
          <div class="filter-row">
            <el-input
              v-model="searchKeyword" placeholder="搜索商品名称或编号..."
              :prefix-icon="Search" clearable class="filter-input"
              @keyup.enter="handleSearch" @clear="handleSearch"
            />
            <el-select v-model="filterCategory" placeholder="全部分类" clearable class="filter-select" @change="handleSearch">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width:120px" @change="handleSearch">
              <el-option label="上架" value="on" />
              <el-option label="下架" value="off" />
            </el-select>
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            <el-button :icon="RefreshRight" @click="handleReset">重置</el-button>
          </div>
        </el-card>

        <!-- 商品表格 -->
        <el-card class="table-card" shadow="never">
          <el-table v-loading="loading" :data="productList" stripe border row-key="id">
            <el-table-column prop="id" label="ID" width="60" align="center" />
            <el-table-column prop="product_no" label="编号" width="100" />
            <el-table-column prop="name" label="商品名称" min-width="180">
              <template #default="{ row }">
                <el-link type="primary" @click="handleViewDetail(row.id)">{{ row.name }}</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="category_name" label="分类" width="110">
              <template #default="{ row }">
                <el-tag size="small" effect="light" type="info">{{ row.category_name }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="价格" width="110" align="right">
              <template #default="{ row }">
                <span class="price-text">¥{{ row.price.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="库存" width="90" align="center">
              <template #default="{ row }">
                <span :class="row.stock < 100 ? 'stock-low' : 'stock-normal'">{{ row.stock }}</span>
              </template>
            </el-table-column>
            <el-table-column label="销量" width="90" align="center" prop="sales_count" />
            <el-table-column label="评分" width="90" align="center">
              <template #default="{ row }">
                <el-rate :model-value="row.rating" disabled size="small" show-score text-color="#fdcb6e" />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-switch
                  :model-value="row.status === 'on'"
                  active-color="#6c5ce7"
                  inactive-color="#ccc"
                  @change="(val: boolean) => handleToggleStatus(row, val)"
                  size="small"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" align="center" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleViewDetail(row.id)">详情</el-button>
                <el-button link type="success" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-popconfirm title="确定删除该商品？" @confirm="handleDelete(row.id)">
                  <template #reference>
                    <el-button link type="danger" size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
              :total="pagination.total" :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper" background
              @size-change="handleSizeChange" @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </div>

      <!-- 右侧热门排行栏 -->
      <div class="product-sidebar">
        <el-card class="hot-card" shadow="never">
          <template #header>
            <div class="hot-header">
              <h3>🔥 热门商品排行</h3>
              <el-radio-group v-model="hotSortBy" size="small" @change="loadHotProducts">
                <el-radio-button value="sales">按销量</el-radio-button>
                <el-radio-button value="rating">按评分</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="hot-list">
            <div v-for="(item, idx) in hotProducts" :key="item.product_id" class="hot-item">
              <div class="hot-rank" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</div>
              <div class="hot-info">
                <div class="hot-name">{{ item.name }}</div>
                <div class="hot-meta">
                  <span class="hot-sales">销量 {{ item.sales_count }}</span>
                  <span class="hot-price">¥{{ item.price }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- ========== 新增/编辑对话框 ========== -->
    <el-dialog
      v-model="dialogVisible" :title="isEdit ? '编辑商品' : '新增商品'"
      width="540px" :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="90px" @closed="formRef?.resetFields()">
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入商品名称" maxlength="30" />
        </el-form-item>
        <el-form-item label="商品编号" prop="product_no" v-if="isEdit">
          <el-input v-model="formData.product_no" disabled />
        </el-form-item>
        <el-form-item label="所属分类" prop="category_id">
          <el-select v-model="formData.category_id" placeholder="请选择分类" style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="formData.price" :min="0.01" :precision="2" :step="10" style="width:100%" />
        </el-form-item>
        <el-form-item label="库存" prop="stock">
          <el-input-number v-model="formData.stock" :min="0" :step="10" style="width:100%" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio value="on">上架</el-radio>
            <el-radio value="off">下架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保 存' : '创 建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// 商品列表页逻辑
// =====================================================
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, RefreshRight, Goods, ShoppingCart, Remove, Coin } from '@element-plus/icons-vue'
import {
  getProductList, getCategories, getHotProducts,
  createProduct, updateProduct, deleteProduct,
} from '@/api/product'
import type { ProductItem, CategoryItem, ProductQueryParams } from '@/types/api'

const router = useRouter()

// ==================== 状态 ====================

const loading = ref(false)
const productList = ref<ProductItem[]>([])
const categories = ref<CategoryItem[]>([])
const hotProducts = ref<{ product_id: number; name: string; sales_count: number; rating: number; price: number }[]>([])
const hotSortBy = ref('sales')

const searchKeyword = ref('')
const filterCategory = ref<number | ''>('')
const filterStatus = ref('')

const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

// 统计卡片
const statCards = computed(() => [
  { label: '商品总数', value: pagination.total + ' 件', icon: Goods, color: '#6c5ce7', bg: 'rgba(108,92,231,0.08)' },
  { label: '在售商品', value: productList.value.filter((p) => p.status === 'on').length + ' 件', icon: ShoppingCart, color: '#00b894', bg: 'rgba(0,184,148,0.08)' },
  { label: '已下架', value: productList.value.filter((p) => p.status === 'off').length + ' 件', icon: Remove, color: '#e17055', bg: 'rgba(225,112,85,0.08)' },
  { label: '均价', value: '¥' + (productList.value.length ? (productList.value.reduce((s, p) => s + p.price, 0) / productList.value.length).toFixed(2) : '0'), icon: Coin, color: '#fdcb6e', bg: 'rgba(253,203,110,0.08)' },
])

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const formData = reactive({
  name: '', product_no: '', category_id: null as number | null, price: 0, stock: 0, status: 'on' as string,
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  stock: [{ required: true, message: '请输入库存', trigger: 'blur' }],
}

// ==================== 数据加载 ====================

const buildQuery = (): ProductQueryParams => ({
  page: pagination.page, page_size: pagination.pageSize,
  keyword: searchKeyword.value || undefined,
  category_id: filterCategory.value || undefined,
  status: filterStatus.value || undefined,
})

const loadList = async () => {
  loading.value = true
  try {
    const res = await getProductList(buildQuery())
    productList.value = res.data.items
    pagination.total = res.data.total
  } catch { ElMessage.error('商品数据加载失败') } finally { loading.value = false }
}

const loadCategories = async () => {
  try { const res = await getCategories(); categories.value = res.data } catch { /* */ }
}

const loadHotProducts = async () => {
  try { const res = await getHotProducts(10, hotSortBy.value as any); hotProducts.value = res.data } catch { /* */ }
}

const handleSearch = () => { pagination.page = 1; loadList() }
const handleReset = () => { searchKeyword.value = ''; filterCategory.value = ''; filterStatus.value = ''; pagination.page = 1; loadList() }
const handleSizeChange = () => { pagination.page = 1; loadList() }
const handlePageChange = () => { loadList() }

// ==================== CRUD ====================

const handleAdd = () => {
  isEdit.value = false; editingId.value = null
  Object.assign(formData, { name: '', product_no: '', category_id: null, price: 0, stock: 0, status: 'on' })
  dialogVisible.value = true
}

const handleEdit = (row: ProductItem) => {
  isEdit.value = true; editingId.value = row.id
  Object.assign(formData, { name: row.name, product_no: row.product_no, category_id: row.category_id, price: row.price, stock: row.stock, status: row.status })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try { await formRef.value.validate() } catch { return }
  submitting.value = true
  try {
    const payload = {
      name: formData.name, category_id: formData.category_id!, price: formData.price, stock: formData.stock, status: formData.status,
      product_no: formData.product_no || `P${Date.now()}`,
    }
    if (isEdit.value && editingId.value) {
      const { product_no: _, ...updatePayload } = payload
      await updateProduct(editingId.value, updatePayload as any)
      ElMessage.success('商品更新成功')
    } else {
      await createProduct(payload as any)
      ElMessage.success('商品创建成功')
    }
    dialogVisible.value = false; loadList(); loadHotProducts()
  } catch { /* */ } finally { submitting.value = false }
}

const handleDelete = async (id: number) => {
  try { await deleteProduct(id); ElMessage.success('已删除'); loadList(); loadHotProducts() } catch { /* */ }
}

const handleToggleStatus = async (row: ProductItem, val: boolean) => {
  try {
    await updateProduct(row.id, { status: val ? 'on' : 'off' } as any)
    row.status = val ? 'on' : 'off'
    ElMessage.success(val ? '已上架' : '已下架')
  } catch { /* */ }
}

const handleViewDetail = (id: number) => router.push(`/products/${id}`)

onMounted(() => {
  loadList(); loadCategories(); loadHotProducts()
})
</script>

<style lang="scss" scoped>
.product-page { max-width: 1500px; margin: 0 auto; animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; background: linear-gradient(135deg, #6c5ce7, #a29bfe); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.page-subtitle { font-size: 13px; color: #b2bec3; margin-top: 4px; }

/* 统计 */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.stat-card { display: flex; align-items: center; gap: 14px; padding: 18px 20px; background: #fff; border-radius: 14px; border: 1px solid var(--border-light); transition: all 0.3s; border-left: 3px solid var(--stat-color);
  &:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
}
.stat-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--stat-color); flex-shrink: 0; }
.stat-value { font-size: 18px; font-weight: 700; color: #2d3436; }
.stat-label { font-size: 12px; color: #b2bec3; }

/* 布局 */
.product-layout { display: flex; gap: 16px; align-items: flex-start; }
.product-main { flex: 1; min-width: 0; }
.product-sidebar { width: 300px; flex-shrink: 0; }

/* 筛选 */
.filter-card { margin-bottom: 16px; border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__body) { padding: 16px 20px; }
}
.filter-row { display: flex; gap: 12px; flex-wrap: wrap; }
.filter-input { width: 260px; }
.filter-select { width: 150px; }

/* 表格 */
.table-card { border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__body) { padding: 0; }
}
:deep(.el-table) {
  --el-table-border-color: #f0f3f7;
  th.el-table__cell { background: rgba(108,92,231,0.03); color: #636e72; font-weight: 600; font-size: 13px; height: 44px; }
  td.el-table__cell { font-size: 13px; }
}

.price-text { color: #6c5ce7; font-weight: 600; }
.stock-low { color: #e17055; font-weight: 600; }
.stock-normal { color: #00b894; font-weight: 600; }
.pagination-wrap { display: flex; justify-content: flex-end; padding: 16px 20px; }

/* 热门排行 */
.hot-card { border: 1px solid var(--border-light); border-radius: 14px; position: sticky; top: 20px;
  :deep(.el-card__header) { padding: 16px; border-bottom: 1px solid var(--border-light); }
  :deep(.el-card__body) { padding: 0; }
}
.hot-header { h3 { margin: 0 0 10px; font-size: 15px; color: #2d3436; } }
.hot-list { padding: 8px 0; }
.hot-item { display: flex; align-items: center; gap: 12px; padding: 10px 16px; transition: background 0.2s;
  &:hover { background: rgba(108,92,231,0.03); }
}
.hot-rank { width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; color: #b2bec3; background: #f0f3f7; flex-shrink: 0;
  &.rank-1 { background: linear-gradient(135deg, #fdcb6e, #f39c12); color: #fff; }
  &.rank-2 { background: linear-gradient(135deg, #dfe6e9, #b2bec3); color: #fff; }
  &.rank-3 { background: linear-gradient(135deg, #fab1a0, #e17055); color: #fff; }
}
.hot-name { font-size: 13px; color: #2d3436; font-weight: 500; }
.hot-meta { display: flex; gap: 12px; margin-top: 4px; }
.hot-sales { font-size: 11px; color: #b2bec3; }
.hot-price { font-size: 12px; color: #6c5ce7; font-weight: 600; }

/* 响应式 */
@media (max-width: 1100px) {
  .product-layout { flex-direction: column; }
  .product-sidebar { width: 100%; }
  .hot-card { position: static; }
}
@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .filter-row { flex-direction: column; .filter-input, .filter-select { width: 100%; } }
}
</style>
