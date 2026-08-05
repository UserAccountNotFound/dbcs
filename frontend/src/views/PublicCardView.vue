<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { publicCardApi } from '../api/publicCards';
import type { PublicCard } from '../types/publicCard';

const route = useRoute();
const card = ref<PublicCard | null>(null);
const isLoading = ref(true);
const error = ref('');
const copyStatus = ref('');

const slug = computed(() => route.params.slug as string);

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

// Вычисляемые классы для цветовой схемы
const isDark = computed(() => card.value?.theme.color_scheme === 'dark');

const containerClasses = computed(() => {
  return isDark.value 
    ? 'min-h-screen bg-gray-900 text-gray-100' 
    : 'min-h-screen bg-gray-50 text-gray-900';
});

const cardClasses = computed(() => {
  return isDark.value 
    ? 'bg-gray-800 border-gray-700' 
    : 'bg-white border-gray-200';
});

const accentStyle = computed(() => {
  return { backgroundColor: card.value?.theme.accent_color || '#0f766e' };
});

const accentTextStyle = computed(() => {
  return { color: card.value?.theme.accent_color || '#0f766e' };
});

const qrUrl = computed(() => publicCardApi.getQrCodeUrl(slug.value));
const vcardUrl = computed(() => publicCardApi.getVCardUrl(slug.value));

// Генерация инициалов для аватара
const initials = computed(() => {
  if (!card.value) return '';
  return card.value.full_name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
});

async function shareCard() {
  if (!card.value) return;

  if (navigator.share) {
    try {
      await navigator.share({
        title: card.value.full_name,
        text: `Визитка: ${card.value.full_name}`,
        url: card.value.public_url
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
      setTimeout(() => copyStatus.value = '', 2000);
    } catch (err) {
      console.error('Clipboard error', err);
    }
  }
}

function getWebsiteDisplay(url: string | null): string {
  if (!url) return '';
  return url.replace(/^https?:\/\//, '');
}
</script>

<template>
  <div :class="containerClasses" class="flex items-center justify-center p-4 min-h-screen">
    <!-- Загрузка -->
    <div v-if="isLoading" class="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-400"></div>

    <!-- Ошибка / Визитка не найдена -->
    <div v-else-if="error" class="text-center max-w-md">
      <div class="text-6xl mb-6">🔒</div>
      <h2 class="text-2xl font-bold mb-2">Визитка недоступна</h2>
      <p class="opacity-70 mb-8">{{ error }}</p>
      <router-link to="/" class="px-6 py-3 bg-gray-200 text-gray-800 rounded-xl hover:bg-gray-300 transition-colors font-medium">
        Перейти на главную
      </router-link>
    </div>

    <!-- Визитка -->
    <div v-else-if="card" class="w-full max-w-md">
      <div :class="cardClasses" class="rounded-3xl shadow-2xl overflow-hidden border transition-all duration-300">
        
        <!-- Акцентная шапка -->
        <div :style="accentStyle" class="h-28 relative overflow-hidden">
          <!-- Декоративный круг -->
          <div class="absolute -right-6 -top-6 w-32 h-32 rounded-full bg-white/10"></div>
          <div class="absolute right-10 top-4 w-16 h-16 rounded-full bg-white/10"></div>
        </div>

        <div class="p-6 -mt-14">
          <!-- Аватар с инициалами -->
          <div class="w-24 h-24 rounded-2xl border-4 flex items-center justify-center text-3xl font-bold mb-5 shadow-lg"
               :class="isDark ? 'bg-gray-700 border-gray-800 text-white' : 'bg-white border-gray-50 text-gray-800'">
            {{ initials }}
          </div>

          <!-- Имя и должность -->
          <h1 class="text-2xl font-bold leading-tight">{{ card.full_name }}</h1>
          <p v-if="card.job_title" class="text-lg opacity-80 mt-1">{{ card.job_title }}</p>
          <p v-if="card.department" class="text-sm opacity-60">{{ card.department }}</p>
          
          <p v-if="card.company" class="text-sm font-semibold mt-2 inline-block px-3 py-1 rounded-full"
             :class="isDark ? 'bg-gray-700' : 'bg-gray-100'"
             :style="accentTextStyle">
            {{ card.company }}
          </p>

          <!-- Разделитель -->
          <div class="my-6 h-px w-full" :class="isDark ? 'bg-gray-700' : 'bg-gray-100'"></div>

          <!-- Контакты -->
          <div class="space-y-4">
            <a v-if="card.phone" :href="`tel:${card.phone}`" 
               class="flex items-center gap-4 p-3 rounded-xl transition-colors"
               :class="isDark ? 'hover:bg-gray-700/50' : 'hover:bg-gray-50'">
              <span class="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                    :style="accentStyle" style="color: white;">📱</span>
              <span class="font-medium">{{ card.phone }}</span>
            </a>

            <a v-if="card.email" :href="`mailto:${card.email}`" 
               class="flex items-center gap-4 p-3 rounded-xl transition-colors"
               :class="isDark ? 'hover:bg-gray-700/50' : 'hover:bg-gray-50'">
              <span class="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                    :style="accentStyle" style="color: white;">✉️</span>
              <span class="font-medium break-all">{{ card.email }}</span>
            </a>

            <a v-if="card.website" :href="card.website" target="_blank" rel="noopener noreferrer"
               class="flex items-center gap-4 p-3 rounded-xl transition-colors"
               :class="isDark ? 'hover:bg-gray-700/50' : 'hover:bg-gray-50'">
              <span class="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                    :style="accentStyle" style="color: white;">🌐</span>
              <span class="font-medium">{{ getWebsiteDisplay(card.website) }}</span>
            </a>

            <div v-if="card.address" class="flex items-center gap-4 p-3 rounded-xl">
              <span class="w-10 h-10 rounded-lg flex items-center justify-center text-lg opacity-80"
                    :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">📍</span>
              <span class="opacity-80">{{ card.address }}</span>
            </div>
          </div>

          <!-- Заметка -->
          <div v-if="card.note" class="mt-6 p-4 rounded-xl text-sm leading-relaxed"
               :class="isDark ? 'bg-gray-700/50 text-gray-300' : 'bg-gray-50 text-gray-600'">
            {{ card.note }}
          </div>

          <!-- QR-код -->
          <div v-if="card.theme.show_qr" class="mt-8 flex flex-col items-center">
            <p class="text-xs opacity-50 mb-3 uppercase tracking-wider">Сканируйте для сохранения</p>
            <div class="p-2 rounded-xl shadow-inner" :class="isDark ? 'bg-white' : 'bg-gray-50'">
              <img :src="qrUrl" alt="QR код визитки" class="w-36 h-36 object-contain" loading="lazy" />
            </div>
          </div>
        </div>
      </div>

      <!-- Кнопки действий -->
      <div class="mt-8 flex gap-4">
        <a :href="vcardUrl" download 
           class="flex-1 py-4 px-6 rounded-2xl font-semibold text-white text-center shadow-lg hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
           :style="accentStyle">
          Добавить в контакты
        </a>
        
        <button @click="shareCard" 
                class="px-6 py-4 rounded-2xl font-semibold border-2 shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
                :class="isDark ? 'border-gray-600 hover:bg-gray-800' : 'border-gray-200 hover:bg-white'">
          {{ copyStatus || 'Поделиться' }}
        </button>
      </div>

      <!-- Техническая информация -->
      <div class="mt-8 text-center text-xs opacity-40">
        DBCS • Электронные визитки
      </div>
    </div>
  </div>
</template>