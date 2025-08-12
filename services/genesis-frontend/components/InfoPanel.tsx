'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, FileText, Users, Calendar, Zap, Lightbulb } from 'lucide-react'
import { useGenesisStore } from '@/lib/store'
import { api } from '@/lib/api'

export default function InfoPanel() {
  const {
    selectedPaper,
    setSelectedPaper,
    paperDetail,
    setPaperDetail,
    insight,
    setInsight,
    isGeneratingInsight,
    setIsGeneratingInsight,
    uiState,
    setUIState
  } = useGenesisStore()
  
  const [isVisible, setIsVisible] = useState(false)
  
  useEffect(() => {
    setIsVisible(!!selectedPaper)
    if (selectedPaper && uiState !== 'DETAIL_VIEW') {
      setUIState('DETAIL_VIEW')
      loadPaperDetail(selectedPaper)
    } else if (!selectedPaper && uiState === 'DETAIL_VIEW') {
      setUIState('GRAPH_VIEW')
    }
  }, [selectedPaper, uiState, setUIState])
  
  // ESC 键关闭面板
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isVisible) {
        handleClose()
      }
    }
    
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isVisible])
  
  const loadPaperDetail = async (paperId: string) => {
    try {
      const detail = await api.getPaperDetail(paperId)
      setPaperDetail(detail)
    } catch (error) {
      console.error('Failed to load paper detail:', error)
    }
  }
  
  const generateInsight = async () => {
    if (!selectedPaper || isGeneratingInsight) return
    
    setIsGeneratingInsight(true)
    setInsight(null)
    
    try {
      const result = await api.getPaperInsight(selectedPaper)
      
      // 模拟打字机效果
      let currentText = ''
      const fullText = result.insight
      const typeSpeed = 30
      
      for (let i = 0; i < fullText.length; i++) {
        currentText += fullText[i]
        setInsight(currentText)
        await new Promise(resolve => setTimeout(resolve, typeSpeed))
      }
    } catch (error) {
      console.error('Failed to generate insight:', error)
      setInsight('生成洞察时发生错误，请稍后重试。')
    } finally {
      setIsGeneratingInsight(false)
    }
  }
  
  const handleClose = () => {
    setSelectedPaper(null)
    setPaperDetail(null)
    setInsight(null)
  }
  
  return (
    <AnimatePresence>
      {isVisible && (
        <>
          {/* 背景遮罩 */}
          <motion.div
            className="fixed inset-0 bg-deep-space/50 backdrop-blur-sm z-30"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
          />
          
          {/* 主面板 - 更大更醒目 */}
          <motion.div
            className="fixed inset-0 z-40 flex items-center justify-center"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <div className="w-full md:w-2/3 lg:w-3/5 xl:w-1/2 h-[90vh] holographic-glass backdrop-blur-xl overflow-y-auto border-l-2 border-cyber-blue/50 shadow-2xl shadow-cyber-blue/20">
            {/* 头部 - 更大更醒目 */}
            <div className="sticky top-0 bg-deep-space/95 backdrop-blur-md p-6 border-b-2 border-cyber-blue/50 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-8 bg-gradient-to-b from-cyber-blue to-neon-pink rounded-full animate-pulse-glow"></div>
                  <h2 className="text-2xl font-orbitron font-bold bg-gradient-to-r from-cyber-blue to-neon-pink bg-clip-text text-transparent">
                    全息甲板分析
                  </h2>
                </div>
                <button
                  onClick={handleClose}
                  className="p-3 hover:bg-cyber-blue/20 rounded-xl transition-all duration-300 hover:scale-110"
                  title="关闭面板"
                >
                  <X className="w-6 h-6 text-starlight" />
                </button>
              </div>
            </div>
            
            {/* 内容 - 更宽敞的布局 */}
            <div className="p-6 lg:p-8 space-y-8 max-w-4xl mx-auto">
              {paperDetail ? (
                <>
                  {/* 论文标题 */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <h3 className="text-2xl lg:text-3xl font-bold text-starlight leading-tight mb-4">
                      {paperDetail.title}
                    </h3>
                    <div className="inline-block px-4 py-2 bg-neon-pink/20 border border-neon-pink/50 rounded-full">
                      <span className="text-neon-pink text-base font-roboto-mono font-medium">
                        {paperDetail.domain}
                      </span>
                    </div>
                  </motion.div>
                  
                  {/* 元数据 */}
                  <motion.div
                    className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6 bg-deep-space/50 rounded-xl border border-starlight/20"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-electric-green/20 rounded-lg">
                        <Users className="w-5 h-5 text-electric-green" />
                      </div>
                      <div>
                        <p className="text-xs text-starlight/60">作者</p>
                        <p className="text-sm text-starlight font-medium">
                          {paperDetail.authors.slice(0, 3).join(', ')}
                          {paperDetail.authors.length > 3 && ' 等'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-electric-green/20 rounded-lg">
                        <Calendar className="w-5 h-5 text-electric-green" />
                      </div>
                      <div>
                        <p className="text-xs text-starlight/60">发布日期</p>
                        <p className="text-sm text-starlight font-medium">{paperDetail.publication_date}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-electric-green/20 rounded-lg">
                        <FileText className="w-5 h-5 text-electric-green" />
                      </div>
                      <div>
                        <p className="text-xs text-starlight/60">文档</p>
                        <a
                          href={paperDetail.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-cyber-blue hover:text-cyber-blue/80 transition-colors font-medium"
                        >
                          查看原文 PDF
                        </a>
                      </div>
                    </div>
                  </motion.div>
                  
                  {/* 摘要 */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="p-6 bg-gradient-to-br from-deep-space/50 to-deep-space/30 rounded-xl border border-starlight/10"
                  >
                    <h4 className="text-lg font-semibold mb-4 flex items-center text-starlight">
                      <div className="p-2 bg-cyber-blue/20 rounded-lg mr-3">
                        <FileText className="w-5 h-5 text-cyber-blue" />
                      </div>
                      摘要
                    </h4>
                    <p className="text-starlight/90 text-base leading-relaxed">
                      {paperDetail.abstract}
                    </p>
                  </motion.div>
                  
                  {/* 一键洞察按钮 */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                  >
                    <button
                      onClick={generateInsight}
                      disabled={isGeneratingInsight}
                      className="w-full py-4 px-6 bg-gradient-to-r from-cyber-blue to-neon-pink 
                               text-deep-space font-bold text-lg rounded-xl transition-all duration-300
                               hover:shadow-2xl hover:shadow-cyber-blue/30 hover:scale-[1.02]
                               disabled:opacity-50 disabled:cursor-not-allowed pulse-ring
                               relative overflow-hidden group"
                    >
                      <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                      <div className="relative flex items-center justify-center space-x-3">
                        <Zap className="w-6 h-6" />
                        <span>
                          {isGeneratingInsight ? 'AI Agent 分析中...' : '一键洞察'}
                        </span>
                      </div>
                    </button>
                  </motion.div>
                  
                  {/* 洞察结果 */}
                  <AnimatePresence>
                    {insight && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.5 }}
                        className="overflow-hidden"
                      >
                        <div className="border-2 border-electric-green/30 rounded-xl p-6 bg-gradient-to-br from-electric-green/10 to-electric-green/5 shadow-lg shadow-electric-green/10">
                          <h4 className="text-xl font-semibold mb-4 flex items-center text-electric-green">
                            <div className="p-2 bg-electric-green/20 rounded-lg mr-3">
                              <Lightbulb className="w-6 h-6" />
                            </div>
                            AI 深度洞察
                          </h4>
                          <div className="prose prose-base text-starlight/90 leading-relaxed space-y-3">
                            {insight.split('\n').map((line, index) => (
                              <p key={index} className="text-base">
                                {line}
                              </p>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  {/* 加载状态 */}
                  {isGeneratingInsight && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center justify-center py-8"
                    >
                      <div className="star-rings">
                        <div className="star-ring"></div>
                        <div className="star-ring"></div>
                        <div className="star-ring"></div>
                      </div>
                    </motion.div>
                  )}
                </>
              ) : (
                // 骨架屏 - 适配更大的布局
                <div className="space-y-8 animate-pulse">
                  <div>
                    <div className="h-8 bg-starlight/20 rounded w-3/4 mb-4"></div>
                    <div className="h-6 bg-starlight/20 rounded w-32"></div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="h-20 bg-starlight/20 rounded-xl"></div>
                    <div className="h-20 bg-starlight/20 rounded-xl"></div>
                    <div className="h-20 bg-starlight/20 rounded-xl"></div>
                  </div>
                  <div className="space-y-3 p-6 bg-starlight/10 rounded-xl">
                    <div className="h-4 bg-starlight/20 rounded"></div>
                    <div className="h-4 bg-starlight/20 rounded w-5/6"></div>
                    <div className="h-4 bg-starlight/20 rounded w-4/6"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
