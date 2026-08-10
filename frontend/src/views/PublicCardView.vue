<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { publicCardApi } from '../api/publicCards';
import type { PublicCard } from '../types/publicCard';
import PublicCardRenderer from '../components/public/PublicCardRenderer.vue';

const route = useRoute();
const card = ref<PublicCard | null>(null);
const isLoading = ref(true);
const error = ref('');

// Состояние модального окна шаринга
const showShareModal = ref(false);
const copyStatus = ref<'idle' | 'success' | 'error'>('idle');

const slug = computed(() => route.params.slug as string);
const vcardUrl = computed(() => publicCardApi.getVCardUrl(slug.value));

onMounted(async () => {
  try {
    card.value = await publicCardApi.getPublicCard(slug.value);
  } catch (e: any) {
    if (e.response?.status === 404) {
      error.value = 'Визитка не найдена или была отключена владельцем.';
    } else {
      error.value = 'Не удалось загрузить визитку. Попробуйте позже.';
    }
  } finally {
    isLoading.value = false;
  }
});

// ============================================================
// ШАРИНГ
// ============================================================

// Проверяем, доступен ли Web Share API (работает только по HTTPS и на мобильных)
const canUseNativeShare = computed(() => {
  return typeof navigator !== 'undefined' && 
         typeof navigator.share === 'function' &&
         window.isSecureContext; // HTTPS или localhost
});

async function handleShare() {
  if (!card.value) return;

  // Если доступен нативный шаринг — используем его
  if (canUseNativeShare.value) {
    try {
      await navigator.share({
        title: card.value.full_name,
        text: `Визитка: ${card.value.full_name}${card.value.company ? ` • ${card.value.company}` : ''}`,
        url: card.value.public_url,
      });
      return; // Успешно поделились
    } catch (err: any) {
      // Пользователь отменил — не показываем модалку
      if (err.name === 'AbortError') return;
      // Другая ошибка — показываем fallback-модалку
      console.warn('Native share failed, using fallback:', err);
    }
  }

  // Fallback: показываем модалку с вариантами шаринга
  showShareModal.value = true;
}

// Копирование ссылки в буфер обмена
async function copyLink() {
  if (!card.value) return;
  
  try {
    await navigator.clipboard.writeText(card.value.public_url);
    copyStatus.value = 'success';
    setTimeout(() => (copyStatus.value = 'idle'), 2000);
  } catch (err) {
    // Fallback для старых браузеров
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

// URL для шаринга в соцсетях
const shareUrls = computed(() => {
  if (!card.value) return {};
  
  const url = encodeURIComponent(card.value.public_url);
  const text = encodeURIComponent(
    `Визитка: ${card.value.full_name}${card.value.company ? ` • ${card.value.company}` : ''}`
  );

  return {
    telegram: `https://t.me/share/url?url=${url}&text=${text}`,
    whatsapp: `https://wa.me/?text=${text}%20${url}`,
    email: `mailto:?subject=${encodeURIComponent('Электронная визитка')}&body=${text}%0A%0A${url}`,
    sms: `sms:?body=${text}%20${url}`,
  };
});

// Закрытие модалки по клику на фон
function closeShareModal(event: MouseEvent) {
  if ((event.target as HTMLElement).dataset.modalBg === 'true') {
    showShareModal.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Загрузка -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center bg-slate-950">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-400"></div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center bg-slate-950 p-4">
      <div class="text-center max-w-md text-slate-100">
        <div class="text-6xl mb-6">🔒</div>
        <h2 class="text-2xl font-bold mb-2">Визитка недоступна</h2>
        <p class="text-slate-400 mb-8">{{ error }}</p>
        <router-link
          to="/"
          class="inline-block px-6 py-3 bg-teal-600 text-white rounded-full hover:bg-teal-500 transition-colors font-medium"
        >
          На главную
        </router-link>
      </div>
    </div>

    <!-- Визитка: каркас + CSS шаблона -->
    <div v-else-if="card" class="flex-1 flex flex-col min-h-screen">
      <PublicCardRenderer
        class="flex-1"
        :card="card"
        show-actions
        :vcard-url="vcardUrl"
        @share="handleShare"
      />
    </div>

    <!-- ============================================================ -->
    <!-- МОДАЛЬНОЕ ОКНО ШАРИНГА -->
    <!-- ============================================================ -->
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
          <!-- Шапка -->
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">Поделиться визиткой</h3>
            <button
              @click="showShareModal = false"
              class="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 transition-colors"
            >
              ✕
            </button>
          </div>

          <!-- Превью ссылки -->
          <div class="px-6 py-4 bg-gray-50">
            <p class="text-xs text-gray-500 mb-1">Ссылка на визитку:</p>
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
                Ссылка скопирована в буфер обмена
              </p>
              <p v-else-if="copyStatus === 'error'" class="text-xs text-red-600 mt-2">
                Не удалось скопировать. Выделите ссылку вручную.
              </p>
            </Transition>
          </div>

          <!-- Кнопки соцсетей -->
          <div class="p-6">
            <p class="text-sm text-gray-600 mb-4">Или отправьте через:</p>
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