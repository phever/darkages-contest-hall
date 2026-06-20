import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The API is proxied so the browser only ever talks to the Vite origin in dev.
// This keeps the auth cookies first-party (SameSite=Lax) — mirroring the Vercel
// rewrite used in production (see frontend/vercel.json).
const API_TARGET = process.env.VITE_API_PROXY || 'http://localhost:8251'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true },
    },
  },
})
