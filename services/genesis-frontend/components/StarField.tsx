'use client'

import { useRef, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

function Stars({ count = 1000 }) {
  const mesh = useRef<THREE.Points>(null)
  
  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)
  
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 2000
    positions[i * 3 + 1] = (Math.random() - 0.5) * 2000
    positions[i * 3 + 2] = (Math.random() - 0.5) * 2000
    
    const color = new THREE.Color()
    color.setHSL(Math.random() * 0.2 + 0.5, 0.55, Math.random() * 0.25 + 0.55)
    colors[i * 3] = color.r
    colors[i * 3 + 1] = color.g
    colors[i * 3 + 2] = color.b
  }
  
  useFrame((state) => {
    if (mesh.current) {
      mesh.current.rotation.x = state.clock.elapsedTime * 0.01
      mesh.current.rotation.y = state.clock.elapsedTime * 0.015
    }
  })
  
  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={count}
          array={colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={2}
        sizeAttenuation={true}
        vertexColors={true}
        transparent={true}
        opacity={0.8}
      />
    </points>
  )
}

export default function StarField() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0">
      <Canvas camera={{ position: [0, 0, 1], fov: 60 }}>
        <Stars />
      </Canvas>
    </div>
  )
}
