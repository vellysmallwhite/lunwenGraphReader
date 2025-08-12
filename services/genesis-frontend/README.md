# 思想星系 - Project Genesis Frontend

一个沉浸式的AI论文知识图谱可视化界面，基于Next.js和Three.js构建。

## 🚀 特性

- **沉浸式3D星空背景** - 基于Three.js的WebGL渲染
- **物理引擎驱动的图谱** - 使用D3-Force实现真实的力导向布局
- **全息玻璃UI设计** - 赛博朋克风格的用户界面
- **渐进式数据加载** - 避免一次性加载整个图谱
- **AI洞察分析** - 集成RAG系统的深度论文分析
- **纯视觉体验** - 专注于视觉效果，无音频依赖

## 🛠 技术栈

- **前端框架**: Next.js 14 + React 18
- **3D渲染**: Three.js + React Three Fiber
- **物理引擎**: D3-Force
- **动画**: Framer Motion
- **状态管理**: Zustand
- **样式**: Tailwind CSS
- **类型**: TypeScript

## 📦 安装

```bash
cd services/genesis-frontend
npm install
```

## 🚀 开发

```bash
npm run dev
```

访问 http://localhost:3000

## 📁 项目结构

```
genesis-frontend/
├── app/                    # Next.js App Router
│   ├── globals.css        # 全局样式
│   ├── layout.tsx         # 根布局
│   └── page.tsx          # 主页面
├── components/            # React组件
│   ├── LoadingScreen.tsx  # 加载界面
│   ├── StarField.tsx      # 星空背景
│   ├── GraphCanvas.tsx    # 图谱画布
│   ├── InfoPanel.tsx      # 信息面板
│   └── HUD.tsx           # 平视显示器
├── lib/                   # 工具库
│   ├── store.ts          # Zustand状态管理
│   ├── api.ts            # API调用
│   └── physics.ts        # 物理引擎
└── public/               # 静态资源
```

## 🎨 设计理念

### 思想星系隐喻
- **论文节点** = 恒星：大小和亮度反映影响力
- **引用关系** = 引力航线：信息传承的能量流动
- **研究领域** = 星云：不同颜色的宇宙空域
- **用户视角** = 探索者飞船：沉浸式的太空探索体验

### 视觉语言
- **深空蓝** (#0C0C1E) - 主背景色
- **赛博蓝** (#00F6FF) - 主要交互色
- **霓虹粉** (#FF00E5) - 强调色
- **电光绿** (#39FF14) - 状态指示色

## 🌟 使用说明

1. **启动体验**: 页面加载时会显示创世大爆炸动画
2. **探索图谱**: 
   - 鼠标悬浮节点查看基本信息
   - 点击节点居中并展开关联节点
   - 双击节点打开详情面板
3. **深度分析**: 在详情面板点击"一键洞察"获取AI分析
4. **搜索功能**: 使用顶部搜索栏进行语义搜索

## 🔧 配置

在 `next.config.js` 中配置API代理：

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8080/api/:path*'
    }
  ]
}
```

## 🎯 性能优化

- **WebGL渲染**: GPU加速的高性能图形渲染
- **物理计算**: D3-Force的高效力导向算法
- **状态管理**: Zustand的轻量级状态管理
- **按需加载**: 节点展开时才加载相关数据

## 🚧 核心功能

- [x] 创世加载动画
- [x] 3D星空背景
- [x] 物理引擎图谱
- [x] 节点交互和展开
- [x] 全息信息面板
- [x] AI洞察生成
- [x] 打字机效果
- [x] 响应式设计

## 📝 注意事项

- 确保后端API服务 (localhost:8080) 正在运行
- 需要现代浏览器支持WebGL
- 推荐使用Chrome或Firefox最新版本
