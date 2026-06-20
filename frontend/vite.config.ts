import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      usePolling: process.env.CHOKIDAR_USEPOLLING === 'true',
      interval: Number(process.env.CHOKIDAR_INTERVAL || 100),
    },
  },
})
