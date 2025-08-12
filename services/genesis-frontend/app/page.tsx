'use client'

import { useEffect, useState } from 'react'
import { useGenesisStore } from '@/lib/store'
import { api } from '@/lib/api'
import LoadingScreen from '@/components/LoadingScreen'
import StarField from '@/components/StarField'
import GraphCanvas from '@/components/GraphCanvas'
import InfoPanel from '@/components/InfoPanel'
import HUD from '@/components/HUD'

export default function Home() {
  const [showLoading, setShowLoading] = useState(true)
  const {
    setGraphData,
    setUIState,
    setIsLoadingGraph,
    uiState
  } = useGenesisStore()
  
  const handleLoadingComplete = async () => {
    setShowLoading(false)
    setIsLoadingGraph(true)
    
    try {
      // 获取初始图数据
      const graphData = await api.getGraphDaily()
      setGraphData(graphData)
      setUIState('GRAPH_VIEW')
    } catch (error) {
      console.error('Failed to load initial graph data:', error)
    } finally {
      setIsLoadingGraph(false)
    }
  }
  
  if (showLoading) {
    return <LoadingScreen onComplete={handleLoadingComplete} />
  }
  
  return (
    <main className="relative w-screen h-screen overflow-hidden bg-deep-space">
      {/* 星空背景 */}
      <StarField />
      
      {/* HUD界面 */}
      <HUD />
      
      {/* 主要内容区域 */}
      <div className="pt-24 h-full">
        {/* 图谱画布 */}
        <div className={`w-full h-full transition-all duration-500 ${
          uiState === 'DETAIL_VIEW' ? 'blur-sm scale-95' : ''
        }`}>
          <GraphCanvas />
        </div>
        
        {/* 信息面板 */}
        <InfoPanel />
      </div>
    </main>
  )
}
