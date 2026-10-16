import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev, proxy API calls to a locally running backend so the browser
// only ever talks to relative /api URLs (same as Nginx and Ingress in prod).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ready': 'http://localhost:8000',
    },
  },
})
