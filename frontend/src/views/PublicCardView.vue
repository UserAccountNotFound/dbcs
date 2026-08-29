<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { publicCardApi } from '../api/publicCards';
import type { PublicCard } from '../types/publicCard';
import PublicCardRenderer from '../components/public/PublicCardRenderer.vue';

const { t } = useI18n();
const route = useRoute();
const card = ref<PublicCard | null>(null);
const isLoading = ref(true);
const error = ref('');

const showShareModal = ref(false);
const copyStatus = ref<'idle' | 'success' | 'error'>('idle');

const slug = computed(() => route.params.slug as string);
const vcardUrl = computed(() => publicCardApi.getVCardUrl(slug.value));

function shareCompanySuffix(c: PublicCard): string {
  return c.company ? ` • ${c.company}` : '';
}

function shareText(c: PublicCard): string {
  return t('public.shareText', { name: c.full_name, company: shareCompanySuffix(c) });
}

onMounted(async () => {
  try {
    card.value = await publicCardApi.getPublicCard(slug.value);
  } catch (e: any) {
    if (e.response?.status === 404) {
      error.value = t('errors.publicNotFound');
    } else {
      error.value = t('errors.publicLoad');
    }
  } finally {
    isLoading.value = false;
  }
});

const canUseNativeShare = computed(() => {
  return typeof navigator !== 'undefined' &&
         typeof navigator.share === 'function' &&
         window.isSecureContext;
});

async function handleShare() {
  if (!card.value) return;

  if (canUseNativeShare.value) {
    try {
      await navigator.share({
        title: card.value.full_name,
        text: shareText(card.value),
        url: card.value.public_url,
      });
      return;
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.warn('Native share failed, using fallback:', err);
    }
  }

  showShareModal.value = true;
}

async function copyLink() {
  if (!card.value) return;

  try {
    await navigator.clipboard.writeText(card.value.public_url);
    copyStatus.value = 'success';
    setTimeout(() => (copyStatus.value = 'idle'), 2000);
  } catch (err) {
    const textArea = document.createElement('textarea');
    textArea.value = card.value.public_url;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      copyStatus.value = 'success';
      setTimeout(() => (copyStatus.value = 'idle'), 2000);
    } catch {
      copyStatus.value = 'error';
    }
    document.body.removeChild(textArea);
  }
}

const shareUrls = computed(() => {
  if (!card.value) return {};

  const url = encodeURIComponent(card.value.public_url);
  const text = encodeURIComponent(shareText(card.value));

  return {
    telegram: `https://t.me/share/url?url=${url}&text=${text}`,
    whatsapp: `https://wa.me/?text=${text}%20${url}`,
    email: `mailto:?subject=${encodeURIComponent(t('public.emailSubject'))}&body=${text}%0A%0A${url}`,
    sms: `sms:?body=${text}%20${url}`,
  };
});

function closeShareModal(event: MouseEvent) {
  if ((event.target as HTMLElement).dataset.modalBg === 'true') {
    showShareModal.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <div v-if="isLoading" class="flex-1 flex items-center justify-center bg-slate-950">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-400"></div>
    </div>

    <div v-else-if="error" class="flex-1 flex items-center justify-center bg-slate-950 p-4">
      <div class="text-center max-w-md text-slate-100">
        <div class="text-6xl mb-6">🔒</div>
        <h2 class="text-2xl font-bold mb-2">{{ t('public.unavailable') }}</h2>
        <p class="text-slate-400 mb-8">{{ error }}</p>
        <router-link
          to="/"
          class="inline-block px-6 py-3 bg-teal-600 text-white rounded-full hover:bg-teal-500 transition-colors font-medium"
        >
          {{ t('public.home') }}
        </router-link>
      </div>
    </div>

    <div v-else-if="card" class="flex-1 flex flex-col min-h-screen">
      <PublicCardRenderer
        class="flex-1"
        :card="card"
        show-actions
        :vcard-url="vcardUrl"
        @share="handleShare"
      />
    </div>

    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showShareModal && card"
        class="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-4"
        data-modal-bg="true"
        @click="closeShareModal"
      >
        <div class="bg-white rounded-t-3xl sm:rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">{{ t('public.shareTitle') }}</h3>
            <button
              @click="showShareModal = false"
              class="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 transition-colors"
            >
              ✕
            </button>
          </div>

          <div class="px-6 py-4 bg-gray-50">
            <p class="text-xs text-gray-500 mb-1">{{ t('public.linkLabel') }}</p>
            <div class="flex items-center gap-2">
              <code class="flex-1 text-sm text-gray-700 bg-white px-3 py-2 rounded-lg border border-gray-200 truncate">
                {{ card.public_url }}
              </code>
              <button
                @click="copyLink"
                class="flex-shrink-0 px-3 py-2 bg-primary text-white text-sm rounded-lg hover:bg-teal-800 transition-colors font-medium"
              >
                <span v-if="copyStatus === 'success'">✓</span>
                <span v-else-if="copyStatus === 'error'">✕</span>
                <span v-else>📋</span>
              </button>
            </div>
            <Transition name="fade">
              <p v-if="copyStatus === 'success'" class="text-xs text-green-600 mt-2">
                {{ t('public.copied') }}
              </p>
              <p v-else-if="copyStatus === 'error'" class="text-xs text-red-600 mt-2">
                {{ t('errors.copyFailed') }}
              </p>
            </Transition>
          </div>

          <div class="p-6">
            <p class="text-sm text-gray-600 mb-4">{{ t('public.shareVia') }}</p>
            <div class="grid grid-cols-4 gap-3">
              <a
                :href="shareUrls.telegram"
                target="_blank"
                rel="noopener noreferrer"
                class="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-blue-50 transition-colors"
              >
                <div class="w-12 h-12 rounded-full bg-[#0088cc] flex items-center justify-center text-white text-xl shadow-md">
                  ✈️
                </div>
                <span class="text-xs text-gray-700 font-medium">Telegram</span>
              </a>

              <a
                :href="shareUrls.whatsapp"
                target="_blank"
                rel="noopener noreferrer"
                class="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-green-50 transition-colors"
              >
                <div class="w-12 h-12 rounded-full bg-[#25D366] flex items-center justify-center text-white text-xl shadow-md">
                  💬
                </div>
                <span class="text-xs text-gray-700 font-medium">WhatsApp</span>
              </a>

              <a
                :href="shareUrls.email"
                class="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <div class="w-12 h-12 rounded-full bg-gray-700 flex items-center justify-center text-white text-xl shadow-md">
                  ✉️
                </div>
                <span class="text-xs text-gray-700 font-medium">Email</span>
              </a>

              <a
                :href="shareUrls.sms"
                class="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-blue-50 transition-colors"
              >
                <div class="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white text-xl shadow-md">
                  📱
                </div>
                <span class="text-xs text-gray-700 font-medium">SMS</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
