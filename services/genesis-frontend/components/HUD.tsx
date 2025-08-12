'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, Settings } from 'lucide-react'

export default function HUD() {
  const [isSearchFocused, setIsSearchFocused] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  
  return (
    <div className="fixed top-0 left-0 right-0 z-30 p-4">
      <div className="flex items-center justify-between">
        {/* 左上角标题 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="holographic-glass px-4 py-2 rounded-lg"
        >
          <h1 className="text-xl font-orbitron font-bold text-cyber-blue">
            思想星系
          </h1>
          <p className="text-xs text-starlight/60 font-roboto-mono">
            Project Genesis v1.0
          </p>
        </motion.div>
        
        {/* 中央搜索栏 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="flex-1 max-w-md mx-8"
        >
          <div className={`relative transition-all duration-300 ${
            isSearchFocused ? 'scale-105' : ''
          }`}>
            <input
              type="text"
              placeholder="语义搜索信标 - 输入概念或问题..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setIsSearchFocused(false)}
              className="w-full px-4 py-2 pl-10 bg-deep-space/60 border border-cyber-blue/30 
                       rounded-lg text-starlight placeholder-starlight/50 font-roboto-mono
                       focus:border-cyber-blue focus:outline-none focus:ring-2 
                       focus:ring-cyber-blue/20 transition-all duration-300"
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-cyber-blue" />
            
            {isSearchFocused && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="absolute top-full left-0 right-0 mt-2 holographic-glass rounded-lg p-3"
              >
                <p className="text-xs text-starlight/70 font-roboto-mono">
                  💡 提示: 尝试输入 "自注意力机制" 或 "图神经网络的最新进展"
                </p>
              </motion.div>
            )}
          </div>
        </motion.div>
        
        {/* 右上角控制面板 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="flex items-center space-x-2"
        >
          {/* 设置 */}
          <button
            className="p-2 holographic-glass rounded-lg hover:bg-cyber-blue/20 transition-colors"
            title="系统设置"
          >
            <Settings className="w-5 h-5 text-starlight" />
          </button>
        </motion.div>
      </div>
      
      {/* 状态栏 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="mt-4 flex justify-center"
      >
        <div className="holographic-glass px-3 py-1 rounded-full">
          <div className="flex items-center space-x-4 text-xs font-roboto-mono">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-electric-green rounded-full animate-pulse"></div>
              <span className="text-starlight/80">系统在线</span>
            </div>
            <div className="text-starlight/60">|</div>
            <div className="text-starlight/80">
              知识节点: <span className="text-cyber-blue font-semibold">2,847</span>
            </div>
            <div className="text-starlight/60">|</div>
            <div className="text-starlight/80">
              引用关系: <span className="text-neon-pink font-semibold">15,392</span>
            </div>
            <div className="text-starlight/60">|</div>
            <div className="text-starlight/80 text-xs">
              🖱️ 拖拽平移 | 🔍 滚轮/双指缩放
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
