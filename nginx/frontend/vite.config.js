import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://100.106.132.15:8001',  // Correct port: 8001
        changeOrigin: true,
      }
    }
  }
})
