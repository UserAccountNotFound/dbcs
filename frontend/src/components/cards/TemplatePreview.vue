<script setup lang="ts">
import { computed } from 'vue';
import type { Template } from '../../types/template';
import type { PublicCard } from '../../types/publicCard';
import PublicCardRenderer from '../public/PublicCardRenderer.vue';

const props = defineProps<{
  template: Template;
  selected?: boolean;
}>();

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
    company: 'Example Corp',
    phone: '+7 900 000-00-00',
    phone_additional: null,
    telegram: null,
    whatsapp: null,
    viber: null,
    wechat: null,
    messenger_max: null,
    discord: null,
    vk: null,
    email: 'ivan@example.com',
    website: 'https://example.com',
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
    :class="{ 'template-selected': selected }"
  >
    <PublicCardRenderer :card="previewCard" preview />
  </div>
</template>

<style scoped>
.template-preview-wrap {
  border: 2px solid transparent;
  border-radius: 16px;
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  cursor: pointer;
  min-height: 220px;
  background: #e5e7eb;
}

.template-preview-wrap:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.12);
}

.template-selected {
  border-color: #0f766e;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.2);
}
</style>
