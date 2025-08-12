'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface LoadingScreenProps {
  onComplete: () => void
}

export default function LoadingScreen({ onComplete }: LoadingScreenProps) {
  const [loadingText, setLoadingText] = useState('正在连接思想星系')
  
  useEffect(() => {
    const texts = [
      '正在连接思想星系...',
      '解析知识节点...',
      '构建引用关系...',
      '初始化宇宙引擎...'
    ]
    
    let index = 0
    const interval = setInterval(() => {
      setLoadingText(texts[index])
      index = (index + 1) % texts.length
    }, 800)
    
    // 模拟加载过程
    const timer = setTimeout(() => {
      onComplete()
    }, 3200)
    
    return () => {
      clearInterval(interval)
      clearTimeout(timer)
    }
  }, [onComplete])
  
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-deep-space z-50">
      {/* 背景粒子 */}
      <div className="absolute inset-0 overflow-hidden">
        {Array.from({ length: 50 }).map((_, i) => (
          <div
            key={i}
            className="particle"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 8}s`,
              animationDuration: `${4 + Math.random() * 4}s`
            }}
          />
        ))}
      </div>
      
      {/* 中央星云 */}
      <motion.div
        className="relative"
        initial={{ scale: 0, rotate: 0 }}
        animate={{ scale: 1, rotate: 360 }}
        transition={{ duration: 2, ease: "easeOut" }}
      >
        {/* 星环加载动画 */}
        <div className="star-rings">
          <div className="star-ring"></div>
          <div className="star-ring"></div>
          <div className="star-ring"></div>
        </div>
        
        {/* 中心点 */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-4 h-4 bg-starlight rounded-full animate-pulse-glow" />
        </div>
      </motion.div>
      
      {/* 加载文字 */}
      <motion.div
        className="absolute bottom-32 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <h2 className="text-2xl font-orbitron font-bold text-cyber-blue mb-4">
          Project Genesis
        </h2>
        <p className="text-starlight font-roboto-mono">
          {loadingText}
        </p>
      </motion.div>
    </div>
  )
}
