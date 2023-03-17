import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte({compilerOptions: {hydratable: true}})],
  // plugins: [svelte()],
  base: "/static/svelte",
  build: {
    outDir: "../impact/static/svelte",
    manifest: true,
    emptyOutDir: true,
    rollupOptions: {
      input: "front/src/main.js"
    }
  },
  server: {
    origin: "http://localhost:5173"
  }
})
