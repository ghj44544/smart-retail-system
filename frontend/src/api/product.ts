// =====================================================
// src/api/product.ts
// 商品管理模块 API 接口层
// 严格遵循 API 接口规范文档 v1.0 第四章
// 包含: 商品CRUD、分类列表、热门商品排行
// 当前使用 Mock 数据，后端就绪后设置 USE_MOCK = false
// =====================================================

import request from '@/utils/request'
import type {
  ApiResponse,
  PaginatedData,
  ProductItem,
  ProductDetail,
  ProductQueryParams,
  CategoryItem,
} from '@/types/api'

// ==================== Mock 开关 ====================
const USE_MOCK = false

// ==================== Mock 数据 ====================

/** Mock 商品分类 */
const mockCategories: CategoryItem[] = [
  { id: 1, name: '电子产品', parent_id: null },
  { id: 2, name: '服装鞋帽', parent_id: null },
  { id: 3, name: '家居用品', parent_id: null },
  { id: 4, name: '食品饮料', parent_id: null },
  { id: 5, name: '运动户外', parent_id: null },
  { id: 6, name: '图书音像', parent_id: null },
  { id: 7, name: '美妆个护', parent_id: null },
  { id: 8, name: '母婴玩具', parent_id: null },
]

/** 商品名称库 */
const productNames: { name: string; categoryId: number; price: number }[] = [
  { name: '无线蓝牙耳机 Pro', categoryId: 1, price: 299.00 },
  { name: '智能手表 S3', categoryId: 1, price: 899.00 },
  { name: 'Type-C 数据线 1m', categoryId: 1, price: 29.90 },
  { name: '便携充电宝 20000mAh', categoryId: 1, price: 129.00 },
  { name: '降噪耳机罩', categoryId: 1, price: 399.00 },
  { name: '机械键盘 RGB', categoryId: 1, price: 299.00 },
  { name: '无线鼠标', categoryId: 1, price: 129.00 },
  { name: 'USB 集线器 7口', categoryId: 1, price: 69.00 },
  { name: '平板电脑支架', categoryId: 1, price: 79.00 },
  { name: '高清摄像头 1080P', categoryId: 1, price: 249.00 },
  { name: '男士休闲夹克', categoryId: 2, price: 359.00 },
  { name: '女士连衣裙', categoryId: 2, price: 259.00 },
  { name: '运动跑鞋', categoryId: 2, price: 499.00 },
  { name: '纯棉T恤', categoryId: 2, price: 99.00 },
  { name: '牛仔裤', categoryId: 2, price: 189.00 },
  { name: '智能台灯', categoryId: 3, price: 159.00 },
  { name: '保温杯 500ml', categoryId: 3, price: 89.00 },
  { name: '乳胶枕', categoryId: 3, price: 199.00 },
  { name: '收纳箱套装', categoryId: 3, price: 79.00 },
  { name: '加湿器', categoryId: 3, price: 129.00 },
  { name: '坚果礼盒', categoryId: 4, price: 168.00 },
  { name: '有机绿茶', categoryId: 4, price: 88.00 },
  { name: '进口咖啡豆', categoryId: 4, price: 129.00 },
  { name: '酸奶机', categoryId: 4, price: 199.00 },
  { name: '瑜伽垫', categoryId: 5, price: 79.00 },
  { name: '羽毛球拍', categoryId: 5, price: 249.00 },
  { name: '登山背包', categoryId: 5, price: 399.00 },
  { name: '跳绳', categoryId: 5, price: 29.00 },
  { name: 'Python编程入门', categoryId: 6, price: 59.00 },
  { name: '数据科学导论', categoryId: 6, price: 79.00 },
  { name: '防晒霜 SPF50', categoryId: 7, price: 129.00 },
  { name: '洗面奶', categoryId: 7, price: 89.00 },
  { name: '婴儿纸尿裤', categoryId: 8, price: 139.00 },
  { name: '积木套装', categoryId: 8, price: 199.00 },
]

/** Mock 商品存储 */
let mockProducts: ProductItem[] = productNames.map((item, index) => ({
  id: index + 1,
  product_no: `P${1001 + index}`,
  name: item.name,
  category_id: item.categoryId,
  category_name: mockCategories.find((c) => c.id === item.categoryId)?.name || '其他',
  price: item.price,
  stock: Math.floor(Math.random() * 2000) + 50,
  status: Math.random() > 0.1 ? 'on' : 'off',
  sales_count: Math.floor(Math.random() * 2000),
  rating: parseFloat((3 + Math.random() * 2).toFixed(1)),
  created_at: new Date(2025, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28)).toISOString(),
}))

/** Mock 商品详情数据 */
const mockProductDetail = (productId: number): ProductDetail => {
  const base = mockProducts.find((p) => p.id === productId) || mockProducts[0]
  // 随机选3个其他商品作为关联商品
  const others = mockProducts.filter((p) => p.id !== base.id)
  const related = others.sort(() => Math.random() - 0.5).slice(0, 3).map((p) => p.id)
  return {
    ...base,
    description: `${base.name} - 高品质产品，深受用户喜爱。累计销量超过${base.sales_count}件，用户评分${base.rating}分。支持7天无理由退换，1年质保。`,
    related_products: related,
  }
}

/** 模拟网络延迟 */
const mockDelay = <T>(data: T, delay = 300): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(data), delay))

// ==================== API 接口函数 ====================

/**
 * 4.1 获取商品列表
 * 接口: GET /products
 * 描述: 分页获取商品列表，支持分类筛选、关键词搜索、状态筛选
 */
export const getProductList = (
  params: ProductQueryParams
): Promise<ApiResponse<PaginatedData<ProductItem>>> => {
  if (USE_MOCK) {
    const page = params.page || 1
    const pageSize = params.page_size || 10
    const keyword = params.keyword || ''
    const categoryId = params.category_id
    const status = params.status

    let filtered = [...mockProducts]
    if (keyword) {
      const kw = keyword.toLowerCase()
      filtered = filtered.filter(
        (p) => p.name.toLowerCase().includes(kw) || p.product_no.toLowerCase().includes(kw)
      )
    }
    if (categoryId) {
      filtered = filtered.filter((p) => p.category_id === categoryId)
    }
    if (status) {
      filtered = filtered.filter((p) => p.status === status)
    }

    return mockDelay({
      code: 200, message: 'success',
      data: {
        items: filtered.slice((page - 1) * pageSize, page * pageSize),
        total: filtered.length, page, page_size: pageSize,
      },
    })
  }
  return request.get('/products', { params })
}

/**
 * 4.2 获取商品详情
 * 接口: GET /products/{product_id}
 * 描述: 获取指定商品的详细信息（含描述 + 关联商品）
 */
export const getProductDetail = (productId: number): Promise<ApiResponse<ProductDetail>> => {
  if (USE_MOCK) {
    return mockDelay({ code: 200, message: 'success', data: mockProductDetail(productId) })
  }
  return request.get(`/products/${productId}`)
}

/**
 * 4.3 创建商品
 * 接口: POST /products
 */
export const createProduct = (
  data: Partial<ProductItem>
): Promise<ApiResponse<ProductItem>> => {
  if (USE_MOCK) {
    const newProduct: ProductItem = {
      id: mockProducts.length + 1,
      product_no: `P${1001 + mockProducts.length}`,
      name: data.name || '',
      category_id: data.category_id || 1,
      category_name: mockCategories.find((c) => c.id === data.category_id)?.name || '其他',
      price: data.price || 0,
      stock: data.stock || 0,
      status: data.status || 'on',
      sales_count: 0,
      rating: 0,
      created_at: new Date().toISOString(),
    }
    mockProducts.unshift(newProduct)
    return mockDelay({ code: 200, message: '创建成功', data: newProduct })
  }
  return request.post('/products', data)
}

/**
 * 4.4 更新商品
 * 接口: PUT /products/{product_id}
 */
export const updateProduct = (
  productId: number,
  data: Partial<ProductItem>
): Promise<ApiResponse<ProductItem>> => {
  if (USE_MOCK) {
    const index = mockProducts.findIndex((p) => p.id === productId)
    if (index !== -1) {
      if (data.category_id) {
        data.category_name = mockCategories.find((c) => c.id === data.category_id)?.name
      }
      mockProducts[index] = { ...mockProducts[index], ...data }
      return mockDelay({ code: 200, message: '更新成功', data: mockProducts[index] })
    }
    return Promise.reject(new Error('商品不存在'))
  }
  return request.put(`/products/${productId}`, data)
}

/**
 * 4.5 删除商品
 * 接口: DELETE /products/{product_id}
 */
export const deleteProduct = (productId: number): Promise<ApiResponse<null>> => {
  if (USE_MOCK) {
    mockProducts = mockProducts.filter((p) => p.id !== productId)
    return mockDelay({ code: 200, message: '删除成功', data: null })
  }
  return request.delete(`/products/${productId}`)
}

/**
 * 4.6 获取商品分类列表
 * 接口: GET /categories
 * 描述: 获取所有商品分类（用于筛选和表单选择）
 */
export const getCategories = (): Promise<ApiResponse<CategoryItem[]>> => {
  if (USE_MOCK) {
    return mockDelay({ code: 200, message: 'success', data: [...mockCategories] }, 200)
  }
  return request.get('/categories')
}

export const createCategory = (
  data: Pick<CategoryItem, 'name'> & { parent_id?: number | null }
): Promise<ApiResponse<CategoryItem>> => {
  if (USE_MOCK) {
    const item: CategoryItem = {
      id: Math.max(0, ...mockCategories.map((c) => c.id)) + 1,
      name: data.name,
      parent_id: data.parent_id ?? null,
    }
    mockCategories.push(item)
    return mockDelay({ code: 200, message: '创建成功', data: item })
  }
  return request.post('/categories', data)
}

export const updateCategory = (
  categoryId: number,
  data: Partial<Pick<CategoryItem, 'name' | 'parent_id'>>
): Promise<ApiResponse<CategoryItem>> => {
  if (USE_MOCK) {
    const item = mockCategories.find((c) => c.id === categoryId)
    if (!item) return Promise.reject(new Error('分类不存在'))
    Object.assign(item, data)
    return mockDelay({ code: 200, message: '更新成功', data: item })
  }
  return request.put(`/categories/${categoryId}`, data)
}

export const deleteCategory = (categoryId: number): Promise<ApiResponse<null>> => {
  if (USE_MOCK) {
    const index = mockCategories.findIndex((c) => c.id === categoryId)
    if (index >= 0) mockCategories.splice(index, 1)
    return mockDelay({ code: 200, message: '删除成功', data: null })
  }
  return request.delete(`/categories/${categoryId}`)
}

/**
 * 4.7 获取热门商品排行
 * 接口: GET /products/hot
 * 描述: 获取热门商品排行榜（Redis 缓存）
 */
export const getHotProducts = (
  limit = 10,
  sortBy: 'sales' | 'rating' = 'sales'
): Promise<
  ApiResponse<{ product_id: number; name: string; sales_count: number; rating: number; price: number }[]>
> => {
  if (USE_MOCK) {
    const sorted = [...mockProducts]
      .filter((p) => p.status === 'on')
      .sort((a, b) => (sortBy === 'rating' ? b.rating - a.rating : b.sales_count - a.sales_count))
      .slice(0, limit)
      .map((p) => ({
        product_id: p.id,
        name: p.name,
        sales_count: p.sales_count,
        rating: p.rating,
        price: p.price,
      }))
    return mockDelay({ code: 200, message: 'success', data: sorted })
  }
  return request.get('/products/hot', { params: { limit, sort_by: sortBy } })
}
