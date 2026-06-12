<template>
  <div class="ai-page">
    <section class="ai-header">
      <div>
        <h2>AI 智能助手</h2>
        <p>基于订单、用户分层、行为漏斗和商品数据生成经营洞察。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" type="primary" plain @click="loadSummary">
        刷新洞察
      </el-button>
    </section>

    <section class="metric-grid">
      <div v-for="item in metrics" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </div>
    </section>

    <section class="insight-strip">
      <article
        v-for="item in summary?.insights || []"
        :key="item.title"
        class="insight-card"
        :class="`priority-${item.priority}`"
      >
        <div class="insight-title">
          <el-icon><Opportunity /></el-icon>
          <strong>{{ item.title }}</strong>
        </div>
        <p>{{ item.content }}</p>
      </article>
    </section>

    <section class="workbench">
      <div class="chat-panel">
        <div class="panel-head">
          <h3>经营问答</h3>
          <el-tag size="small" effect="plain">本地数据分析</el-tag>
        </div>

        <div class="quick-questions">
          <el-button
            v-for="question in quickQuestions"
            :key="question"
            size="small"
            plain
            @click="sendQuestion(question)"
          >
            {{ question }}
          </el-button>
        </div>

        <div ref="chatBodyRef" class="chat-body">
          <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
            <div class="bubble">
              <p>{{ message.content }}</p>
              <ul v-if="message.suggestions?.length">
                <li v-for="suggestion in message.suggestions" :key="suggestion">{{ suggestion }}</li>
              </ul>
            </div>
          </div>
        </div>

        <div class="chat-input">
          <el-input
            v-model="question"
            :rows="3"
            type="textarea"
            maxlength="500"
            show-word-limit
            placeholder="例如：哪些商品需要补货？怎么提升转化率？用户分层应该怎么运营？"
            @keydown.ctrl.enter.prevent="handleAsk"
          />
          <el-button :icon="Promotion" :loading="asking" type="primary" @click="handleAsk">
            发送
          </el-button>
        </div>
      </div>

      <aside class="side-panel">
        <div class="panel-head">
          <h3>知识库</h3>
          <el-input
            v-model="knowledgeKeyword"
            size="small"
            clearable
            placeholder="搜索主题"
            @input="loadKnowledge"
          />
        </div>

        <div class="knowledge-list">
          <article v-for="item in knowledge" :key="item.id" class="knowledge-item">
            <strong>{{ item.title }}</strong>
            <p>{{ item.summary }}</p>
            <div class="tag-row">
              <el-tag v-for="tag in item.keywords.slice(0, 3)" :key="tag" size="small" effect="plain">
                {{ tag }}
              </el-tag>
            </div>
          </article>
        </div>

        <div class="product-rank">
          <div class="panel-head compact">
            <h3>热销商品</h3>
          </div>
          <div v-for="product in summary?.top_products || []" :key="product.id" class="rank-item">
            <span>{{ product.name }}</span>
            <strong>¥{{ product.revenue.toFixed(2) }}</strong>
            <small>库存 {{ product.stock }} / 已售 {{ product.sold_qty }}</small>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Opportunity, Promotion, Refresh } from '@element-plus/icons-vue'
import { askAI, getAISummary, searchAIKnowledge } from '@/api/ai'
import type { AIKnowledgeItem, AISummary } from '@/types/api'

type ChatMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
  suggestions?: string[]
}

const loading = ref(false)
const asking = ref(false)
const question = ref('')
const knowledgeKeyword = ref('')
const summary = ref<AISummary | null>(null)
const knowledge = ref<AIKnowledgeItem[]>([])
const chatBodyRef = ref<HTMLDivElement | null>(null)

const messages = ref<ChatMessage[]>([
  {
    id: Date.now(),
    role: 'assistant',
    content: '你好，我可以基于当前系统数据回答经营、用户分层、转化和商品搭配问题。',
    suggestions: ['先试试问：最近经营情况怎么样？'],
  },
])

const quickQuestions = ['最近经营情况怎么样？', '哪些商品需要补货？', '怎么提升转化率？', '用户分层怎么运营？']

const formatMoney = (value = 0) => `¥${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`

const metrics = computed(() => {
  const m = summary.value?.metrics
  return [
    { label: '累计销售额', value: m ? formatMoney(m.total_sales) : '--', hint: `${m?.total_orders || 0} 笔成交` },
    { label: '客单价', value: m ? formatMoney(m.avg_order_value) : '--', hint: '成交订单平均金额' },
    { label: '近 30 天销售额', value: m ? formatMoney(m.recent_30d_sales) : '--', hint: `${m?.recent_30d_orders || 0} 笔订单` },
    { label: '浏览到购买', value: m ? `${m.buy_rate.toFixed(2)}%` : '--', hint: `${m?.view_count || 0} 次浏览` },
  ]
})

const scrollToBottom = async () => {
  await nextTick()
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  }
}

const loadSummary = async () => {
  loading.value = true
  try {
    const res = await getAISummary()
    summary.value = res.data
  } finally {
    loading.value = false
  }
}

let knowledgeTimer: number | undefined
const loadKnowledge = () => {
  window.clearTimeout(knowledgeTimer)
  knowledgeTimer = window.setTimeout(async () => {
    const res = await searchAIKnowledge(knowledgeKeyword.value)
    knowledge.value = res.data.items
  }, 250)
}

const sendQuestion = async (text: string) => {
  const clean = text.trim()
  if (!clean || asking.value) return

  messages.value.push({ id: Date.now(), role: 'user', content: clean })
  question.value = ''
  asking.value = true
  await scrollToBottom()

  try {
    const res = await askAI(clean)
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: res.data.answer,
      suggestions: res.data.suggestions,
    })
  } catch {
    ElMessage.error('AI 助手暂时没有拿到回答')
  } finally {
    asking.value = false
    await scrollToBottom()
  }
}

const handleAsk = () => sendQuestion(question.value)

onMounted(async () => {
  await Promise.all([loadSummary(), searchAIKnowledge().then(res => { knowledge.value = res.data.items })])
})
</script>

<style scoped lang="scss">
.ai-page {
  max-width: 1440px;
  margin: 0 auto;
  color: #1f2937;
}

.ai-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;

  h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 800;
  }

  p {
    margin: 6px 0 0;
    color: #64748b;
    font-size: 14px;
  }
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.metric-card,
.insight-card,
.chat-panel,
.side-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.metric-card {
  padding: 16px;

  span,
  small {
    display: block;
    color: #64748b;
    font-size: 13px;
  }

  strong {
    display: block;
    margin: 8px 0 6px;
    font-size: 24px;
  }
}

.insight-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.insight-card {
  padding: 16px;
  border-left: 4px solid #3b82f6;

  &.priority-high {
    border-left-color: #ef4444;
  }

  &.priority-medium {
    border-left-color: #f59e0b;
  }

  p {
    margin: 10px 0 0;
    color: #475569;
    line-height: 1.7;
    font-size: 14px;
  }
}

.insight-title,
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.insight-title {
  justify-content: flex-start;
}

.workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 14px;
  align-items: start;
}

.chat-panel,
.side-panel {
  padding: 16px;
}

.panel-head {
  margin-bottom: 12px;

  h3 {
    margin: 0;
    font-size: 16px;
  }

  &.compact {
    margin-top: 18px;
  }
}

.quick-questions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.chat-body {
  height: 430px;
  overflow-y: auto;
  padding: 14px;
  border: 1px solid #eef2f7;
  background: #f8fafc;
  border-radius: 8px;
}

.message {
  display: flex;
  margin-bottom: 12px;

  &.user {
    justify-content: flex-end;

    .bubble {
      color: #fff;
      background: #2563eb;
    }
  }

  &.assistant .bubble {
    background: #fff;
    border: 1px solid #e5e7eb;
  }
}

.bubble {
  max-width: 78%;
  padding: 12px 14px;
  border-radius: 8px;
  white-space: pre-line;
  line-height: 1.7;

  p {
    margin: 0;
  }

  ul {
    margin: 10px 0 0;
    padding-left: 18px;
  }
}

.chat-input {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 96px;
  gap: 10px;
  margin-top: 12px;
  align-items: end;
}

.knowledge-list {
  display: grid;
  gap: 10px;
}

.knowledge-item,
.rank-item {
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #eef2f7;
  border-radius: 8px;
}

.knowledge-item {
  p {
    margin: 8px 0;
    color: #64748b;
    line-height: 1.6;
    font-size: 13px;
  }
}

.tag-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.rank-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 4px 10px;
  margin-bottom: 8px;

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  small {
    grid-column: 1 / -1;
    color: #64748b;
  }
}

@media (max-width: 1200px) {
  .metric-grid,
  .insight-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workbench {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .ai-header,
  .chat-input {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  .metric-grid,
  .insight-strip {
    grid-template-columns: 1fr;
  }

  .chat-body {
    height: 360px;
  }

  .bubble {
    max-width: 92%;
  }
}
</style>
