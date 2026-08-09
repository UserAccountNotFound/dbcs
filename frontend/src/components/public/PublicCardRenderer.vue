<script setup lang="ts">
import { computed } from 'vue';
import type { PublicCard } from '../../types/publicCard';

const props = defineProps<{
  card: PublicCard;
}>();

// ============================================================
// ОБЪЕДИНЕНИЕ НАСТРОЕК ШАБЛОНА И ТЕМЫ
// ============================================================

const schema = computed(() => props.card.template_schema);
const theme = computed(() => props.card.theme);

// Вычисляемые стили: тема переопределяет шаблон
const styles = computed(() => {
  const s = schema.value;
  const t = theme.value;
  
  return {
    // Цвета
    primaryColor: t.accent_color || s?.primary_color || '#0f766e',
    secondaryColor: s?.secondary_color || '#f3f4f6',
    textColor: s?.text_color || '#111827',
    
    // Layout: тема переопределяет шаблон
    layout: t.layout || s?.layout_type || 'classic',
    
    // Шрифт
    font: t.font || s?.heading_font || 'inter',
    
    // Флаги: тема переопределяет шаблон
    showPhoto: t.show_photo,
    showQr: t.show_qr,
    showLogo: s?.show_logo || false,
    
    // Декорации из шаблона
    borderRadius: `${s?.border_radius ?? 16}px`,
    shadow: s?.shadow !== false,
    gradientHeader: s?.gradient_header || false,
    photoPosition: s?.photo_position || 'left',
  };
});

// CSS-переменные для стилизации
const cssVars = computed(() => ({
  '--primary': styles.value.primaryColor,
  '--secondary': styles.value.secondaryColor,
  '--text': styles.value.textColor,
  '--radius': styles.value.borderRadius,
  '--font': getFontFamily(styles.value.font),
}));

// Маппинг шрифтов на системные стеки
function getFontFamily(font: string): string {
  const fonts: Record<string, string> = {
    inter: "'Inter', system-ui, sans-serif",
    roboto: "'Roboto', system-ui, sans-serif",
    open_sans: "'Open Sans', system-ui, sans-serif",
  };
  return fonts[font] || fonts.inter;
}

// Инициалы для аватара
const initials = computed(() => {
  return props.card.full_name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
});

// URL QR-кода
const qrUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL}/public/cards/${props.card.slug}/qrcode.svg`;
});

function resolveMediaUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;

  const apiBase = String(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
  if (url.startsWith('/api/')) {
    const origin = apiBase.replace(/\/api\/v1$/, '');
    return `${origin}${url}`;
  }
  if (url.startsWith('/')) {
    const origin = apiBase.replace(/\/api\/v1$/, '');
    return `${origin}${url}`;
  }
  return `${apiBase}/${url}`;
}

const avatarUrl = computed(() => resolveMediaUrl(props.card.avatar_url));
const logoUrl = computed(() => resolveMediaUrl(props.card.logo_url));

// Форматирование сайта (убираем протокол)
function formatWebsite(url: string | null): string {
  if (!url) return '';
  return url.replace(/^https?:\/\//, '');
}

// Класс layout для CSS
const layoutClass = computed(() => `layout-${styles.value.layout}`);

// Класс позиции фото
const photoPositionClass = computed(() => `photo-${styles.value.photoPosition}`);
</script>

<template>
  <div 
    class="card-renderer"
    :class="[layoutClass, photoPositionClass]"
    :style="cssVars"
  >
    <!-- Шапка с градиентом -->
    <div 
      v-if="styles.gradientHeader"
      class="card-header"
      :style="{ background: `linear-gradient(135deg, var(--primary), var(--secondary))` }"
    >
      <div class="header-decoration"></div>
    </div>
    
    <!-- Основной контент -->
    <div class="card-body">
      
      <!-- Логотип компании (если есть) -->
      <div v-if="styles.showLogo && logoUrl" class="card-logo">
        <img :src="logoUrl" :alt="card.company || 'Logo'" />
      </div>
      
      <!-- Фото -->
      <div v-if="styles.showPhoto" class="card-photo">
        <img 
          v-if="avatarUrl" 
          :src="avatarUrl" 
          :alt="card.full_name"
          class="photo-image"
        />
        <div v-else class="photo-placeholder">
          {{ initials }}
        </div>
      </div>
      
      <!-- Текстовая информация -->
      <div class="card-info">
        <h1 class="card-name">{{ card.full_name }}</h1>
        <p v-if="card.job_title" class="card-title">{{ card.job_title }}</p>
        <p v-if="card.department" class="card-department">{{ card.department }}</p>
        
        <div v-if="card.company" class="card-company">
          <span class="company-badge">{{ card.company }}</span>
        </div>
        
        <!-- Контакты -->
        <div class="card-contacts">
          <a v-if="card.phone" :href="`tel:${card.phone}`" class="contact-item">
            <span class="contact-icon">📱</span>
            <span class="contact-value">{{ card.phone }}</span>
          </a>
          
          <a v-if="card.email" :href="`mailto:${card.email}`" class="contact-item">
            <span class="contact-icon">✉️</span>
            <span class="contact-value">{{ card.email }}</span>
          </a>
          
          <a v-if="card.website" :href="card.website" target="_blank" rel="noopener noreferrer" class="contact-item">
            <span class="contact-icon">🌐</span>
            <span class="contact-value">{{ formatWebsite(card.website) }}</span>
          </a>
          
          <div v-if="card.address" class="contact-item">
            <span class="contact-icon">📍</span>
            <span class="contact-value">{{ card.address }}</span>
          </div>
        </div>
        
        <!-- Заметка -->
        <div v-if="card.note" class="card-note">
          {{ card.note }}
        </div>
      </div>
      
      <!-- QR-код -->
      <div v-if="styles.showQr" class="card-qr">
        <img :src="qrUrl" alt="QR код визитки" loading="lazy" />
        <p class="qr-label">Сканируйте для сохранения</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card-renderer {
  position: relative;
  background: var(--secondary);
  border-radius: var(--radius);
  color: var(--text);
  font-family: var(--font);
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: v-bind('styles.shadow ? "0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)" : "none"');
}

.card-renderer:hover {
  transform: translateY(-2px);
  box-shadow: v-bind('styles.shadow ? "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)" : "none"');
}

/* Шапка с градиентом */
.card-header {
  height: 80px;
  position: relative;
  overflow: hidden;
}

.header-decoration {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

/* Основной контент */
.card-body {
  padding: 24px;
  display: flex;
  gap: 20px;
  position: relative;
}

/* ============================================================
   ФОТО
   ============================================================ */
.card-photo {
  flex-shrink: 0;
}

.photo-image,
.photo-placeholder {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.photo-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  color: white;
  font-size: 32px;
  font-weight: bold;
}

/* ============================================================
   ИНФОРМАЦИЯ
   ============================================================ */
.card-info {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px 0;
  line-height: 1.2;
}

.card-title {
  font-size: 16px;
  opacity: 0.85;
  margin: 0 0 2px 0;
}

.card-department {
  font-size: 14px;
  opacity: 0.7;
  margin: 0 0 8px 0;
}

.card-company {
  margin-bottom: 16px;
}

.company-badge {
  display: inline-block;
  padding: 4px 12px;
  background: var(--primary);
  color: white;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

/* Контакты */
.card-contacts {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  font-size: 14px;
  padding: 6px 8px;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.contact-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.contact-icon {
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.contact-value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Заметка */
.card-note {
  margin-top: 16px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.8;
}

/* ============================================================
   QR-КОД
   ============================================================ */
.card-qr {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.card-qr img {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  background: white;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.qr-label {
  margin-top: 6px;
  font-size: 10px;
  opacity: 0.5;
  text-align: center;
}

/* ============================================================
   ЛОГОТИП
   ============================================================ */
.card-logo {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
}

.card-logo img {
  height: 32px;
  width: auto;
  object-fit: contain;
}

/* ============================================================
   LAYOUT VARIATIONS
   ============================================================ */

/* Classic: фото слева, текст справа */
.layout-classic .card-body {
  flex-direction: row;
  align-items: flex-start;
}

/* Modern: фото сверху по центру */
.layout-modern .card-body {
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.layout-modern .card-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.layout-modern .card-contacts {
  align-items: center;
}

.layout-modern .card-qr {
  margin-top: 16px;
}

/* Compact: без фото, минималистично */
.layout-compact .card-body {
  flex-direction: column;
  padding: 20px;
}

.layout-compact .card-photo {
  display: none;
}

.layout-compact .card-name {
  font-size: 20px;
}

.layout-compact .card-qr {
  align-self: flex-end;
}

/* Corporate: строгий стиль, фото справа */
.layout-corporate .card-body {
  flex-direction: row-reverse;
  align-items: center;
  background: white;
}

.layout-corporate .card-info {
  border-right: 2px solid var(--primary);
  padding-right: 20px;
}

.layout-corporate .company-badge {
  background: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
}

/* Creative: градиенты, необычная компоновка */
.layout-creative .card-body {
  flex-direction: column-reverse;
  align-items: center;
  text-align: center;
  background: linear-gradient(180deg, var(--secondary) 0%, var(--primary) 200%);
}

.layout-creative .card-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.layout-creative .card-name {
  font-size: 28px;
  background: linear-gradient(90deg, var(--primary), var(--text));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.layout-creative .card-contacts {
  align-items: center;
}

.layout-creative .company-badge {
  border-radius: 4px;
  transform: rotate(-2deg);
}

/* ============================================================
   PHOTO POSITION VARIATIONS
   ============================================================ */

.photo-top .card-body {
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.photo-right .card-body {
  flex-direction: row-reverse;
}

/* ============================================================
   АДАПТИВНОСТЬ
   ============================================================ */
@media (max-width: 480px) {
  .card-body {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .card-info {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .card-contacts {
    align-items: center;
  }
  
  .card-qr {
    margin-top: 16px;
  }
}
</style>