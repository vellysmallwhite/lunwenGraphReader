import { GraphData, PaperDetail } from './store'

// Use Next.js rewrite proxy (/api -> backend) to avoid CORS issues in dev
const API_BASE = ''

export const api = {
  async getGraphDaily(): Promise<GraphData> {
    const response = await fetch(`${API_BASE}/api/graph/daily`)
    if (!response.ok) throw new Error('Failed to fetch daily graph')
    return response.json()
  },

  async expandNode(arxivId: string): Promise<GraphData> {
    const response = await fetch(`${API_BASE}/api/graph/expand/${arxivId}`)
    if (!response.ok) throw new Error('Failed to expand node')
    return response.json()
  },

  async getPaperDetail(arxivId: string): Promise<PaperDetail> {
    const response = await fetch(`${API_BASE}/api/papers/${arxivId}/detail`)
    if (!response.ok) throw new Error('Failed to fetch paper detail')
    return response.json()
  },

  async getPaperInsight(arxivId: string): Promise<{ arxiv_id: string; insight: string }> {
    const response = await fetch(`${API_BASE}/api/papers/${arxivId}/insight`)
    if (!response.ok) throw new Error('Failed to generate insight')
    return response.json()
  }
}
