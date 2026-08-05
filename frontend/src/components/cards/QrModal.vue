<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import { cardApi } from '../../api/cards';

const props = defineProps<{ cardId: string | null }>();
const emit = defineEmits(['close']);

const qrUrl = ref<string | null>(null);
const isLoading = ref(false);

watch(() => props.cardId, async (newId) => {
  // Очищаем предыдущий blob URL
  if (qrUrl.value) {
    window.URL.revokeObjectURL(qrUrl.value);
    qrUrl.value = null;
  }

  if (newId) {
    isLoading.value = true;
    try {
      const blob = await cardApi.getQrCodeBlob(newId);
      qrUrl.value = window.URL.createObjectURL(blob);
    } catch (e) {
      alert('Ошибка при загрузке QR-кода');
    } finally {
      isLoading.value = false;
    }
  }
}, { immediate: true });

onUnmounted(() => {
  if (qrUrl.value) {
    window.URL.revokeObjectURL(qrUrl.value);
  }
});
</script>

<template>
  <div v-if="cardId" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-lg p-6 max-w-sm w-full shadow-xl">
      <h3 class="text-lg font-bold mb-4 text-center">QR-код визитки</h3>
      
      <div class="flex justify-center items-center min-h-[200px]">
        <div v-if="isLoading" class="animate-pulse text-gray-500">Загрузка...</div>
        <img v-else-if="qrUrl" :src="qrUrl" alt="QR Code" class="w-64 h-64 object-contain" />
        <div v-else class="text-red-500">Не удалось загрузить QR</div>
      </div>

      <div class="mt-6 flex gap-3">
        <button @click="$emit('close')" class="btn-secondary flex-1">Закрыть</button>
        <a v-if="qrUrl" :href="qrUrl" download="qr-code.svg" class="btn-primary flex-1 text-center">Скачать SVG</a>
      </div>
    </div>
  </div>
</template>