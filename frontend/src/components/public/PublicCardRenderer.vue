<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import type { PublicCard } from '../../types/publicCard';
import type { CardTheme } from '../../types/card';
import {
  buildMessengerHref,
  type MessengerKind,
} from '../../utils/messengerLinks';
import PolygonNetworkBackground from './PolygonNetworkBackground.vue';

const props = withDefaults(
  defineProps<{
    card: PublicCard;
    /** Режим превью (уменьшенный каркас) */
    preview?: boolean;
    /** Показать блок CTA внутри каркаса */
    showActions?: boolean;
    vcardUrl?: string;
  }>(),
  {
    preview: false,
    showActions: false,
    vcardUrl: '',
  },
);

const emit = defineEmits<{
  (e: 'share'): void;
}>();

const theme = computed<CardTheme>(() => props.card.theme);
const templateCode = computed(() => props.card.template_code || 'classic');
const cssUrl = computed(() => props.card.css_url);
const enablePolygon = computed(() => props.card.template_effect === 'polygon');

const fontStacks: Record<string, string> = {
  inter: "'Inter', system-ui, sans-serif",
  roboto: "'Roboto', system-ui, sans-serif",
  open_sans: "'Open Sans', system-ui, sans-serif",
};

const rootClass = computed(() => {
  const t = theme.value;
  return [
    'dbcs-card',
    `tpl-${templateCode.value}`,
    t.color_scheme === 'dark' ? 'scheme-dark' : 'scheme-light',
    t.show_photo ? '' : 'no-photo',
    t.show_qr ? '' : 'no-qr',
    props.preview ? 'dbcs-preview' : '',
  ].filter(Boolean);
});

const cssVars = computed(() => ({
  '--dbcs-accent': theme.value.accent_color || '#0f766e',
  '--dbcs-scheme': theme.value.color_scheme || 'light',
  '--dbcs-font': fontStacks[theme.value.font] || fontStacks.inter,
}));

const initials = computed(() =>
  props.card.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2),
);

function resolveMediaUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;
  const apiBase = String(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
  if (url.startsWith('/api/')) {
    return `${apiBase.replace(/\/api\/v1$/, '')}${url}`;
  }
  if (url.startsWith('/')) {
    return `${apiBase.replace(/\/api\/v1$/, '')}${url}`;
  }
  return `${apiBase}/${url}`;
}

const avatarUrl = computed(() => resolveMediaUrl(props.card.avatar_url));
const logoUrl = computed(() => resolveMediaUrl(props.card.logo_url));

const qrUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL}/public/cards/${props.card.slug}/qrcode.svg`;
});

function formatWebsite(url: string | null): string {
  if (!url) return '';
  return url.replace(/^https?:\/\//, '');
}

type LinkItem = {
  key: string;
  label: string;
  href: string | null;
  icon: string;
  external?: boolean;
};

const MESSENGER_LINKS: Array<{
  key: MessengerKind;
  label: string;
  icon: string;
  getValue: (c: PublicCard) => string | null | undefined;
}> = [
  { key: 'telegram', label: 'Telegram', icon: '✈️', getValue: (c) => c.telegram },
  { key: 'whatsapp', label: 'WhatsApp', icon: '💬', getValue: (c) => c.whatsapp },
  { key: 'viber', label: 'Viber', icon: '🟣', getValue: (c) => c.viber },
  { key: 'wechat', label: 'WeChat', icon: '🟢', getValue: (c) => c.wechat },
  { key: 'messenger_max', label: 'Max', icon: '🔵', getValue: (c) => c.messenger_max },
  { key: 'discord', label: 'Discord', icon: '🎮', getValue: (c) => c.discord },
  { key: 'vk', label: 'VK', icon: '🔷', getValue: (c) => c.vk },
];

const linkItems = computed<LinkItem[]>(() => {
  const items: LinkItem[] = [];
  const c = props.card;
  if (c.phone) items.push({ key: 'phone', label: c.phone, href: `tel:${c.phone}`, icon: '📱' });
  if (c.phone_additional) {
    items.push({
      key: 'phone_additional',
      label: c.phone_additional,
      href: `tel:${c.phone_additional}`,
      icon: '☎️',
    });
  }
  if (c.email) items.push({ key: 'email', label: c.email, href: `mailto:${c.email}`, icon: '✉️' });
  if (c.website) {
    items.push({
      key: 'website',
      label: formatWebsite(c.website),
      href: c.website,
      icon: '🔗',
      external: true,
    });
  }
  if (c.address) {
    items.push({
      key: 'address',
      label: c.address,
      href: `https://maps.google.com/?q=${encodeURIComponent(c.address)}`,
      icon: '📍',
      external: true,
    });
  }
  for (const m of MESSENGER_LINKS) {
    const raw = m.getValue(c);
    if (!raw) continue;
    const href = buildMessengerHref(m.key, raw);
    items.push({
      key: m.key,
      label: `${m.label}: ${raw}`,
      href,
      icon: m.icon,
      external: Boolean(href),
    });
  }
  return items;
});

const subtitle = computed(() => {
  const parts = [props.card.job_title, props.card.department].filter(Boolean);
  return parts.join(' • ');
});

/** Подключение CSS шаблона через <link> */
const linkEl = ref<HTMLLinkElement | null>(null);

function attachCss(url: string | null) {
  detachCss();
  if (!url) return;
  const el = document.createElement('link');
  el.rel = 'stylesheet';
  el.href = url;
  el.dataset.dbcsTemplateCss = templateCode.value;
  document.head.appendChild(el);
  linkEl.value = el;
}

function detachCss() {
  if (linkEl.value) {
    linkEl.value.remove();
    linkEl.value = null;
  }
  document
    .querySelectorAll('link[data-dbcs-template-css]')
    .forEach((n) => {
      if ((n as HTMLLinkElement).dataset.dbcsTemplateCss === templateCode.value) {
        n.remove();
      }
    });
}

onMounted(() => attachCss(cssUrl.value));
onUnmounted(() => detachCss());
watch(cssUrl, (url) => attachCss(url));
</script>

<template>
  <div :class="rootClass" :style="cssVars" :data-effect="enablePolygon ? 'polygon' : undefined">
    <PolygonNetworkBackground :active="enablePolygon && !preview" />

    <div class="dbcs-content">
      <div v-if="logoUrl" class="dbcs-logo">
        <img :src="logoUrl" :alt="card.company || 'Logo'" />
      </div>

      <div class="dbcs-avatar">
        <img v-if="avatarUrl" :src="avatarUrl" :alt="card.full_name" />
        <div v-else class="dbcs-avatar-fallback">{{ initials }}</div>
      </div>

      <h1 class="dbcs-name">{{ card.full_name }}</h1>
      <p v-if="subtitle" class="dbcs-title">{{ subtitle }}</p>
      <p v-if="card.company" class="dbcs-company">{{ card.company }}</p>
      <p v-if="card.note" class="dbcs-bio">{{ card.note }}</p>

      <div v-if="linkItems.length" class="dbcs-links">
        <component
          :is="item.href ? 'a' : 'div'"
          v-for="item in linkItems"
          :key="item.key"
          class="dbcs-link"
          :href="item.href || undefined"
          :target="item.external ? '_blank' : undefined"
          :rel="item.external ? 'noopener noreferrer' : undefined"
        >
          <span class="dbcs-link-icon">{{ item.icon }}</span>
          <span class="dbcs-link-label">{{ item.label }}</span>
        </component>
      </div>

      <div class="dbcs-qr">
        <img :src="qrUrl" alt="QR код визитки" loading="lazy" />
        <p class="dbcs-qr-label">Сканируйте для сохранения</p>
      </div>
    </div>

    <div v-if="showActions" class="dbcs-actions">
      <a
        v-if="vcardUrl"
        class="dbcs-action dbcs-action-primary"
        :href="vcardUrl"
        download
      >
        📇 Добавить в контакты
      </a>
      <button
        type="button"
        class="dbcs-action dbcs-action-secondary"
        @click="emit('share')"
      >
        🔗 Поделиться
      </button>
    </div>

    <div v-if="showActions" class="dbcs-footer">DBCS • Электронные визитки</div>
  </div>
</template>

<style scoped>
/* Минимальный каркас без визуала шаблона (fallback) */
.dbcs-card {
  position: relative;
  isolation: isolate;
  min-height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  font-family: var(--dbcs-font, system-ui, sans-serif);
  color: #111827;
  background: #f3f4f6;
}

.dbcs-preview {
  min-height: 220px;
  border-radius: 16px;
  overflow: hidden;
}

.dbcs-preview .dbcs-content {
  padding: 16px 12px !important;
  transform: scale(0.92);
  transform-origin: top center;
}

.dbcs-preview .dbcs-name {
  font-size: 1rem !important;
}

.dbcs-preview .dbcs-avatar img,
.dbcs-preview .dbcs-avatar-fallback {
  width: 48px !important;
  height: 48px !important;
  font-size: 18px !important;
}

.dbcs-preview .dbcs-qr,
.dbcs-preview .dbcs-actions,
.dbcs-preview .dbcs-footer {
  display: none !important;
}
</style>
