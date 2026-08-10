<script setup lang="ts">
import { computed } from 'vue';
import type { Template } from '../../types/template';
import type { PublicCard } from '../../types/publicCard';
import PublicCardRenderer from '../public/PublicCardRenderer.vue';

const props = withDefaults(
  defineProps<{
    template: Template;
    selected?: boolean;
    /** compact — плитка в сетке; large — увеличенный превью в модалке */
    size?: 'compact' | 'large';
  }>(),
  {
    selected: false,
    size: 'compact',
  },
);

const previewCard = computed<PublicCard>(() => {
  const meta = props.template.meta || props.template.schema_data;
  const accent = meta?.default_accent || '#0f766e';
  const scheme = meta?.default_scheme || 'light';

  return {
    slug: 'preview',
    title: 'Preview',
    full_name: 'Иван Петров',
    job_title: 'Senior Developer',
    department: null,
    company: 'DBCS Corp',
    phone: '+7 123 456-78-90',
    phone_additional: null,
    telegram: null,
    whatsapp: null,
    viber: null,
    wechat: null,
    messenger_max: null,
    discord: null,
    vk: null,
    email: 'ivan@dbcs.example',
    website: 'https://dbcs.example',
    address: null,
    note: null,
    theme: {
      color_scheme: scheme,
      layout: 'classic',
      font: 'inter',
      accent_color: accent,
      show_photo: true,
      show_qr: false,
    },
    template_code: props.template.code,
    css_url: props.template.css_url,
    template_effect: meta?.effect || null,
    avatar_url: null,
    logo_url: null,
    public_url: '#',
  };
});
</script>

<template>
  <div
    class="template-preview-wrap"
    :class="{
      'template-selected': selected,
      'size-compact': size === 'compact',
      'size-large': size === 'large',
    }"
  >
    <PublicCardRenderer :card="previewCard" preview />
  </div>
</template>

<style scoped>
.template-preview-wrap {
  border: 2px solid transparent;
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  background: #e5e7eb;
}

.size-compact {
  cursor: pointer;
  min-height: 120px;
  max-height: 140px;
}

.size-compact :deep(.dbcs-preview) {
  min-height: 120px;
}

.size-compact :deep(.dbcs-preview .dbcs-content) {
  padding: 10px 8px !important;
  transform: scale(0.72);
  transform-origin: top center;
}

.size-compact :deep(.dbcs-preview .dbcs-name) {
  font-size: 0.8rem !important;
}

.size-compact :deep(.dbcs-preview .dbcs-avatar img),
.size-compact :deep(.dbcs-preview .dbcs-avatar) {
  width: 36px !important;
  height: 36px !important;
  font-size: 14px !important;
}

.size-compact:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.1);
}

.size-large {
  min-height: 420px;
  border-radius: 16px;
  cursor: default;
}

.size-large :deep(.dbcs-preview) {
  min-height: 420px;
}

.size-large :deep(.dbcs-preview .dbcs-content) {
  padding: 28px 20px !important;
  transform: scale(1);
}

.size-large :deep(.dbcs-preview .dbcs-name) {
  font-size: 1.35rem !important;
}

.size-large :deep(.dbcs-preview .dbcs-avatar img),
.size-large :deep(.dbcs-preview .dbcs-avatar) {
  width: 88px !important;
  height: 88px !important;
}

.template-selected {
  border-color: #0f766e;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.2);
}
</style>
