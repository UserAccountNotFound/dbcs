<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { cardApi } from '../../api/cards';

const { t } = useI18n();

const props = defineProps<{ cardId: string | null }>();
const emit = defineEmits(['close']);

const qrUrl = ref<string | null>(null);
const isLoading = ref(false);
let requestId = 0;

watch(() => props.cardId, async (newId) => {
  const currentRequest = ++requestId;

  if (qrUrl.value) {
    window.URL.revokeObjectURL(qrUrl.value);
    qrUrl.value = null;
  }

  if (newId) {
    isLoading.value = true;
    try {
      const blob = await cardApi.getQrCodeBlob(newId);
      if (currentRequest !== requestId || props.cardId !== newId) {
        return;
      }
      qrUrl.value = window.URL.createObjectURL(blob);
    } catch (e) {
      if (currentRequest !== requestId) return;
      alert(t('errors.qrLoad'));
    } finally {
      if (currentRequest === requestId) {
        isLoading.value = false;
      }
    }
  }
}, { immediate: true });

onUnmounted(() => {
  requestId += 1;
  if (qrUrl.value) {
    window.URL.revokeObjectURL(qrUrl.value);
  }
});
</script>

<template>
  <div v-if="cardId" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-lg p-6 max-w-sm w-full shadow-xl">
      <h3 class="text-lg font-bold mb-4 text-center">{{ t('cards.qrTitle') }}</h3>
      
      <div class="flex justify-center items-center min-h-[200px]">
        <div v-if="isLoading" class="animate-pulse text-gray-500">{{ t('common.loadingShort') }}</div>
        <img v-else-if="qrUrl" :src="qrUrl" alt="QR Code" class="w-64 h-64 object-contain" />
        <div v-else class="text-red-500">{{ t('errors.qrLoadShort') }}</div>
      </div>

      <div class="mt-6 flex gap-3">
        <button @click="$emit('close')" class="btn-secondary flex-1">{{ t('common.close') }}</button>
        <a v-if="qrUrl" :href="qrUrl" download="qr-code.svg" class="btn-primary flex-1 text-center">{{ t('cards.downloadSvg') }}</a>
      </div>
    </div>
  </div>
</template>
