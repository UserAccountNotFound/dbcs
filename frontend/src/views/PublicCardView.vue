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
const copyStatus = ref('');

const slug = computed(() => route.params.slug as string);

// URL для скачивания vCard (публичный endpoint, без авторизации)
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

async function shareCard() {
  if (!card.value) return;

  if (navigator.share) {
    try {
      await navigator.share({
        title: card.value.full_name,
        text: `Визитка: ${card.value.full_name}`,
        url: card.value.public_url,
      });
    } catch (err) {
      // Пользователь отменил шаринг
      console.log('Share cancelled');
    }
  } else {
    // Fallback для десктопов: копирование ссылки
    try {
      await navigator.clipboard.writeText(card.value.public_url);
      copyStatus.value = 'Ссылка скопирована!';
      setTimeout(() => (copyStatus.value = ''), 2000);
    } catch (err) {
      console.error('Clipboard error', err);
    }
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <!-- Загрузка -->
    <div v-if="isLoading" class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>

    <!-- Ошибка / Визитка не найдена -->
    <div v-else-if="error" class="text-center max-w-md">
      <div class="text-6xl mb-6">🔒</div>
      <h2 class="text-2xl font-bold mb-2 text-gray-900">Визитка недоступна</h2>
      <p class="text-gray-600 mb-8">{{ error }}</p>
      <router-link
        to="/"
        class="inline-block px-6 py-3 bg-primary text-white rounded-xl hover:bg-teal-800 transition-colors font-medium"
      >
        Перейти на главную
      </router-link>
    </div>

    <!-- Визитка -->
    <div v-else-if="card" class="w-full max-w-lg">
      <!-- Рендер визитки по шаблону и теме -->
      <PublicCardRenderer :card="card" />

      <!-- Кнопки действий -->
      <div class="mt-8 flex gap-4">
        <a
          :href="vcardUrl"
          download
          class="flex-1 py-4 px-6 rounded-2xl font-semibold text-white text-center shadow-lg hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
          :style="{ backgroundColor: card.theme.accent_color }"
        >
          Добавить в контакты
        </a>

        <button
          @click="shareCard"
          class="px-6 py-4 rounded-2xl font-semibold border-2 border-gray-200 bg-white shadow-lg hover:bg-gray-50 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
        >
          {{ copyStatus || 'Поделиться' }}
        </button>
      </div>

      <!-- Техническая информация -->
      <div class="mt-8 text-center text-xs text-gray-400">
        DBCS • Электронные визитки
      </div>
    </div>
  </div>
</template>