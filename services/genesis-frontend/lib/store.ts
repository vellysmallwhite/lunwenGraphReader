import { create } from 'zustand'

export interface Node {
  id: string
  title?: string
  summary?: string
  domain?: string
  type: 'today' | 'cited' | 'expanded' | 'center'
  first_author?: string
  author_count?: number
  year?: string
  key_contributions?: string[]
  methodology?: string
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
  vx?: number
  vy?: number
}

export interface Link {
  source: string | Node
  target: string | Node
  type: 'CITES'
}

export interface GraphData {
  nodes: Node[]
  links: Link[]
}

export interface PaperDetail {
  arxiv_id: string
  title: string
  authors: string[]
  abstract: string
  pdf_url: string
  publication_date: string
  domain: string
}

export type UIState = 'INITIAL_LOADING' | 'GRAPH_VIEW' | 'DETAIL_VIEW'
export type NodeState = 'IDLE' | 'HOVERED' | 'LOADING_EXPAND' | 'CENTER' | 'GHOST'

interface GenesisStore {
  // UI State
  uiState: UIState
  setUIState: (state: UIState) => void
  
  // Graph Data
  graphData: GraphData
  setGraphData: (data: GraphData) => void
  addGraphData: (data: GraphData) => void
  
  // Selected Paper
  selectedPaper: string | null
  setSelectedPaper: (paperId: string | null) => void
  
  // Paper Detail
  paperDetail: PaperDetail | null
  setPaperDetail: (detail: PaperDetail | null) => void
  
  // Insight
  insight: string | null
  setInsight: (insight: string | null) => void
  isGeneratingInsight: boolean
  setIsGeneratingInsight: (generating: boolean) => void
  
  // Loading states
  isLoadingGraph: boolean
  setIsLoadingGraph: (loading: boolean) => void
  isExpandingNode: boolean
  setIsExpandingNode: (expanding: boolean) => void
  expandingNodeId: string | null
  setExpandingNodeId: (nodeId: string | null) => void
  
  // Interaction
  hoveredNode: string | null
  setHoveredNode: (nodeId: string | null) => void
  
  // Camera control
  cameraTarget: { x: number; y: number } | null
  setCameraTarget: (target: { x: number; y: number } | null) => void
}

export const useGenesisStore = create<GenesisStore>((set, get) => ({
  // UI State
  uiState: 'INITIAL_LOADING',
  setUIState: (state) => set({ uiState: state }),
  
  // Graph Data
  graphData: { nodes: [], links: [] },
  setGraphData: (data) => set({ graphData: data }),
  addGraphData: (data) => {
    const current = get().graphData
    const existingNodeIds = new Set(current.nodes.map(n => n.id))
    const existingLinks = new Set(current.links.map(l => `${typeof l.source === 'string' ? l.source : l.source.id}-${typeof l.target === 'string' ? l.target : l.target.id}`))
    
    const newNodes = data.nodes.filter(n => !existingNodeIds.has(n.id))
    const newLinks = data.links.filter(l => {
      const linkId = `${typeof l.source === 'string' ? l.source : l.source.id}-${typeof l.target === 'string' ? l.target : l.target.id}`
      return !existingLinks.has(linkId)
    })
    
    set({
      graphData: {
        nodes: [...current.nodes, ...newNodes],
        links: [...current.links, ...newLinks]
      }
    })
  },
  
  // Selected Paper
  selectedPaper: null,
  setSelectedPaper: (paperId) => set({ selectedPaper: paperId }),
  
  // Paper Detail
  paperDetail: null,
  setPaperDetail: (detail) => set({ paperDetail: detail }),
  
  // Insight
  insight: null,
  setInsight: (insight) => set({ insight }),
  isGeneratingInsight: false,
  setIsGeneratingInsight: (generating) => set({ isGeneratingInsight: generating }),
  
  // Loading states
  isLoadingGraph: false,
  setIsLoadingGraph: (loading) => set({ isLoadingGraph: loading }),
  isExpandingNode: false,
  setIsExpandingNode: (expanding) => set({ isExpandingNode: expanding }),
  expandingNodeId: null,
  setExpandingNodeId: (nodeId) => set({ expandingNodeId: nodeId }),
  
  // Interaction
  hoveredNode: null,
  setHoveredNode: (nodeId) => set({ hoveredNode: nodeId }),
  
  // Camera control
  cameraTarget: null,
  setCameraTarget: (target) => set({ cameraTarget: target }),
}))
