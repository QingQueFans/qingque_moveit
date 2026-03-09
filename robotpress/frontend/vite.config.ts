import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite' // ✅ v4 必须要有！

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(), // ✅ v4 必须要有！
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})