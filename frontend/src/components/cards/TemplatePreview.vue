<script setup lang="ts">
import { computed } from 'vue';
import type { TemplateSchema } from '../../types/template';

const props = defineProps<{
  schema: TemplateSchema | null;
  templateName: string;
  selected?: boolean;
}>();

// Генерируем стили на основе схемы шаблона
const previewStyles = computed(() => {
  const s = props.schema;
  if (!s) return {};

  return {
    '--primary': s.primary_color,
    '--secondary': s.secondary_color,
    '--text': s.text_color,
    '--radius': `${s.border_radius}px`,
    '--font-heading': s.heading_font,
    '--font-body': s.body_font,
  };
});

const layoutClass = computed(() => {
  const type = props.schema?.layout_type || 'classic';
  return `layout-${type}`;
});
</script>

<template>
  <div 
    class="template-preview"
    :class="[layoutClass, { 'template-selected': selected }]"
    :style="previewStyles"
  >
    <!-- Шапка с градиентом (если включен) -->
    <div 
      v-if="schema?.gradient_header" 
      class="preview-header"
      :style="{ background: `linear-gradient(135deg, ${schema?.primary_color}, ${schema?.secondary_color})` }"
    ></div>
    
    <div class="preview-body" :class="{ 'photo-top': schema?.photo_position === 'top' }">
      <!-- Фото (если включено) -->
      <div v-if="schema?.show_photo" class="preview-photo">
        <div class="photo-placeholder">👤</div>
      </div>
      
      <!-- Текстовая часть -->
      <div class="preview-text">
        <div class="preview-name">Иван Петров</div>
        <div class="preview-title">Senior Developer</div>
        <div class="preview-company">Example Corp</div>
        <div class="preview-contacts">
          <div class="contact-line">📱 +7 900 000-00-00</div>
          <div class="contact-line">✉️ ivan@example.com</div>
        </div>
      </div>
      
      <!-- QR (если включен) -->
      <div v-if="schema?.show_qr" class="preview-qr">
        <div class="qr-placeholder">▦</div>
      </div>
    </div>
    
    <!-- Логотип (если включен) -->
    <div v-if="schema?.show_logo" class="preview-logo">
      <span>🏢</span>
    </div>
  </div>
</template>

<style scoped>
.template-preview {
  position: relative;
  background: var(--secondary, #f3f4f6);
  border-radius: var(--radius, 16px);
  padding: 12px;
  color: var(--text, #111827);
  font-family: var(--font-body, sans-serif);
  border: 2px solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.template-preview:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.template-selected {
  border-color: var(--primary, #0f766e);
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.2);
}

.preview-header {
  height: 40px;
  border-radius: calc(var(--radius) / 2);
  margin-bottom: 10px;
}

.preview-body {
  display: flex;
  gap: 10px;
  flex: 1;
}

.preview-body.photo-top {
  flex-direction: column;
}

.preview-photo {
  flex-shrink: 0;
}

.photo-placeholder {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--primary, #0f766e);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.preview-text {
  flex: 1;
  min-width: 0;
}

.preview-name {
  font-weight: bold;
  font-size: 14px;
  font-family: var(--font-heading, sans-serif);
  margin-bottom: 2px;
}

.preview-title {
  font-size: 11px;
  opacity: 0.8;
  margin-bottom: 2px;
}

.preview-company {
  font-size: 11px;
  color: var(--primary, #0f766e);
  font-weight: 600;
  margin-bottom: 6px;
}

.preview-contacts {
  font-size: 10px;
  opacity: 0.7;
}

.contact-line {
  margin-bottom: 1px;
}

.preview-qr {
  flex-shrink: 0;
}

.qr-placeholder {
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.preview-logo {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 16px;
}

/* Layout variations */
.layout-compact .preview-body {
  align-items: center;
}

.layout-corporate {
  background: white;
  border: 1px solid #e5e7eb;
}

.layout-creative .preview-body {
  flex-direction: column-reverse;
}
</style>