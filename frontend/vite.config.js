import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // 允许外部访问（默认只允许 localhost）
    proxy: {
      '/socket.io': 'http://localhost:8000',
      '/download': 'http://localhost:8000'
    }
  },
  build: {
    outDir: '../frontend/dist'
  }
})

