import request from '@/utils/request'
import type { ApiResponse, AIChatResult, AIKnowledgeItem, AISummary } from '@/types/api'

export const getAISummary = (): Promise<ApiResponse<AISummary>> => {
  return request.get('/ai/summary')
}

export const askAI = (question: string): Promise<ApiResponse<AIChatResult>> => {
  return request.post('/ai/chat', { question })
}

export const searchAIKnowledge = (q = ''): Promise<ApiResponse<{ items: AIKnowledgeItem[] }>> => {
  return request.get('/ai/knowledge', { params: { q } })
}
