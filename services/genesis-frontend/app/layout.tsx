import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: '思想星系 - Project Genesis',
  description: 'An immersive AI research paper knowledge graph visualization',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body>
        <div className="nebula-bg" />
        {children}
      </body>
    </html>
  )
}
