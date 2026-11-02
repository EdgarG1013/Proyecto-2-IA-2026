import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // En desarrollo, las peticiones a /api van al backend de FastAPI (uvicorn en el puerto 8000)
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
