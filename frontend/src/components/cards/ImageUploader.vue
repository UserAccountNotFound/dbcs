<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { fileApi } from '../../api/files';
import { getAxiosErrorMessage } from '../../utils/apiError';

const props = defineProps<{
  modelValue: string | null;
  label: string;
  aspectRatio?: 'square' | 'wide';
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | null): void;
}>();

const isUploading = ref(false);
const previewUrl = ref<string | null>(null);
const error = ref('');
const localPreviewUrl = ref<string | null>(null);
let previewRequestId = 0;

function revokeUrl(url: string | null) {
  if (url && url.startsWith('blob:')) {
    URL.revokeObjectURL(url);
  }
}

watch(
  () => props.modelValue,
  async (newFileId, oldFileId) => {
    if (newFileId === oldFileId) return;

    if (previewUrl.value) {
      revokeUrl(previewUrl.value);
      previewUrl.value = null;
    }

    if (!newFileId) {
      return;
    }

    if (localPreviewUrl.value) {
      return;
    }

    const requestId = ++previewRequestId;
    try {
      const blob = await fileApi.getFileBlob(newFileId);
      if (requestId !== previewRequestId || props.modelValue !== newFileId) {
        return;
      }
      previewUrl.value = URL.createObjectURL(blob);
    } catch (e) {
      if (requestId !== previewRequestId) return;
      console.error('Failed to load file preview:', e);
      previewUrl.value = null;
    }
  },
  { immediate: true }
);

const displayUrl = computed(() => localPreviewUrl.value || previewUrl.value);

const aspectClass = computed(() => {
  return props.aspectRatio === 'wide' ? 'aspect-video' : 'aspect-square';
});

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (!file) return;

  const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!validTypes.includes(file.type)) {
    error.value = 'Допустимы только форматы JPG, PNG, WebP';
    target.value = '';
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    error.value = 'Размер файла не должен превышать 5 МБ';
    target.value = '';
    return;
  }

  error.value = '';
  isUploading.value = true;

  if (localPreviewUrl.value) {
    revokeUrl(localPreviewUrl.value);
    localPreviewUrl.value = null;
  }

  localPreviewUrl.value = URL.createObjectURL(file);

  try {
    // Не удаляем старый файл сразу: карточка ещё может на него ссылаться до save.
    const uploaded = await fileApi.upload(file);
    emit('update:modelValue', uploaded.id);
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, 'Ошибка при загрузке файла');
    revokeUrl(localPreviewUrl.value);
    localPreviewUrl.value = null;
  } finally {
    isUploading.value = false;
    target.value = '';
  }
}

function removeImage() {
  // Только локально: физическое удаление — после сохранения карточки / GC.
  revokeUrl(localPreviewUrl.value);
  revokeUrl(previewUrl.value);
  localPreviewUrl.value = null;
  previewUrl.value = null;
  emit('update:modelValue', null);
}

onUnmounted(() => {
  previewRequestId += 1;
  revokeUrl(localPreviewUrl.value);
  revokeUrl(previewUrl.value);
});
</script>

<template>
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-2">{{ label }}</label>
    
    <div class="flex items-start gap-4">
      <div 
        :class="['w-24 h-24 rounded-lg border-2 overflow-hidden relative bg-gray-50', aspectClass]"
        :style="aspectRatio === 'wide' ? 'width: 12rem' : ''"
      >
        <img 
          v-if="displayUrl" 
          :src="displayUrl" 
          :alt="label"
          class="w-full h-full object-cover"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-3xl">
          🖼️
        </div>
        
        <div v-if="isUploading" class="absolute inset-0 bg-white/80 flex items-center justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
      
      <div class="flex-1 space-y-2">
        <label class="btn-secondary inline-block cursor-pointer">
          {{ displayUrl ? 'Заменить' : 'Загрузить' }}
          <input 
            type="file" 
            accept="image/jpeg,image/png,image/webp"
            class="hidden"
            @change="handleFileSelect"
            :disabled="isUploading"
          />
        </label>
        
        <button 
          v-if="displayUrl"
          type="button"
          @click="removeImage"
          class="btn-danger block"
          :disabled="isUploading"
        >
          Удалить
        </button>
        
        <p class="text-xs text-gray-500">
          JPG, PNG или WebP. Макс. 5 МБ.
        </p>
        
        <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
      </div>
    </div>
  </div>
</template>
