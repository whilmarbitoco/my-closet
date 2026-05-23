import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'My Closet — AI Virtual Try-On',
  description: 'Upload your photo and digitally try on clothes with AI',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
