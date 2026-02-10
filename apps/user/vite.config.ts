
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    // Core React + router always loaded
                    'vendor-react': ['react', 'react-dom', 'react-router-dom'],
                    // Visualisation libs (heavy) — only loaded on /visuals
                    'vendor-viz': ['d3', 'reactflow'],
                    // Mobile components — lazy-loaded chunk
                    'mobile': [
                        './src/components/mobile/MobileQuickDash.tsx',
                        './src/components/mobile/JobSwipe.tsx',
                        './src/components/mobile/MobileCVUpload.tsx',
                    ],
                },
            },
        },
    },
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8500',
                changeOrigin: true,
            }
        }
    }
})
