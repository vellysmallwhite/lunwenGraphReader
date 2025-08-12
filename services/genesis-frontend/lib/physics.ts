import * as d3 from 'd3-force'
import { Node, Link } from './store'

export class PhysicsEngine {
  private simulation: d3.Simulation<Node, Link>
  private nodes: Node[] = []
  private links: Link[] = []
  
  constructor() {
    this.simulation = d3.forceSimulation<Node>()
      .force('link', d3.forceLink<Node, Link>().id(d => d.id).distance(100).strength(0.5))
      .force('charge', d3.forceManyBody().strength(-300).theta(0.9)) // 增加theta以提高性能
      .force('center', d3.forceCenter(0, 0).strength(0.05))
      .force('collision', d3.forceCollide().radius(30).iterations(1)) // 减少碰撞检测迭代
      .alphaDecay(0.02)
      .velocityDecay(0.8)
  }
  
  updateData(nodes: Node[], links: Link[]) {
    this.nodes = nodes
    this.links = links
    
    this.simulation
      .nodes(this.nodes)
      .force<d3.ForceLink<Node, Link>>('link')?.links(this.links)
    
    this.simulation.alpha(0.5).restart()
  }
  
  onTick(callback: (nodes: Node[], links: Link[]) => void) {
    this.simulation.on('tick', () => {
      callback(this.nodes, this.links)
    })
  }
  
  onEnd(callback: () => void) {
    this.simulation.on('end', callback)
  }
  
  centerNode(nodeId: string) {
    const node = this.nodes.find(n => n.id === nodeId)
    if (node) {
      node.fx = 0
      node.fy = 0
      this.simulation.alpha(0.3).restart()
      
      // 短暂固定后释放
      setTimeout(() => {
        if (node) {
          node.fx = null
          node.fy = null
        }
      }, 1000)
    }
  }
  
  highlightConnections(nodeId: string) {
    const connectedIds = new Set<string>()
    this.links.forEach(link => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      
      if (sourceId === nodeId) connectedIds.add(targetId)
      if (targetId === nodeId) connectedIds.add(sourceId)
    })
    
    return connectedIds
  }
  
  stop() {
    this.simulation.stop()
  }
  
  restart() {
    this.simulation.restart()
  }
}
