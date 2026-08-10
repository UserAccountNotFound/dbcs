import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const appVersion = JSON.parse(
  readFileSync(path.join(__dirname, 'package.json'), 'utf-8'),
).version as string

export default defineConfig({
  define: {
    'import.meta.env.VITE_APP_VERSION': JSON.stringify(appVersion),
  },
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png'],
      manifest: {
        name: 'Digital Business Cards Service',
        short_name: 'DBCS',
        description: 'Сервис электронных визиток',
        theme_color: '#0f766e',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          }
        ]
      },
      workbox: {
        // Кэшируем статические файлы при сборке
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        
        // SPA fallback: все навигационные запросы ведут на index.html
        navigateFallback: '/index.html',
        
        // Не перехватываем API-запросы как навигацию
        navigateFallbackAllowlist: [/^(?!\/api).*/],
        
        // Быстрое обновление Service Worker
        skipWaiting: true,
        clientsClaim: true,
        
        // Стратегии кэширования в runtime
        runtimeCaching: [
          {
            // Статические ресурсы (JS, CSS, шрифты)
            urlPattern: /\.(?:js|css|woff2?)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'static-resources',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 30 * 24 * 60 * 60 // 30 дней
              }
            }
          },
          {
            // API: список визиток пользователя (offline-просмотр)
            urlPattern: /\/api\/v1\/cards(\?.*)?$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'user-cards-cache',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 7 * 24 * 60 * 60 // 7 дней
              }
            }
          },
          {
            // API: публичные визитки (offline-просмотр после первого визита)
            urlPattern: /\/api\/v1\/public\/cards\/[^/]+$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'public-cards-cache',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 30 * 24 * 60 * 60 // 30 дней
              }
            }
          },
          {
            // Изображения (QR-коды, аватары)
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 30 * 24 * 60 * 60
              }
            }
          }
        ]
      }
    })
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})