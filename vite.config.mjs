import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
  build: {
    lib: {
      entry: './assets/main.js',
      name: 'KniffelApp',
      fileName: 'bundle',
      formats: ['iife']
    },
    outDir: 'static',
    emptyOutDir: false,
    rollupOptions: {
      output: {
        entryFileNames: 'bundle.js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'style.css') {
            return 'styles.css'
          }
          return assetInfo.name
        }
      }
    }
  }
})
