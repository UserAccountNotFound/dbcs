<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { fileApi } from '../../api/files';

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

// Флаг, чтобы не путать "локальный preview" и "server blob preview"
const localPreviewUrl = ref<string | null>(null);

// Освобождение object URL для предотвращения утечек памяти
function revokeUrl(url: string | null) {
  if (url && url.startsWith('blob:')) {
    URL.revokeObjectURL(url);
  }
}

// Загружаем blob при изменении file_id извне (например, при загрузке формы редактирования)
watch(
  () => props.modelValue,
  async (newFileId, oldFileId) => {
    // Если file_id не менялся — ничего не делаем
    if (newFileId === oldFileId) return;

    // Освобождаем предыдущий server preview (но не local — он сбрасывается отдельно)
    if (previewUrl.value) {
      revokeUrl(previewUrl.value);
      previewUrl.value = null;
    }

    if (!newFileId) {
      // Файл был удалён из формы
      return;
    }

    // Если localPreviewUrl уже есть (пользователь только что загрузил файл) — используем его
    if (localPreviewUrl.value) {
      return;
    }

    // Иначе загружаем blob через API
    try {
      const blob = await fileApi.getFileBlob(newFileId);
      previewUrl.value = URL.createObjectURL(blob);
    } catch (e) {
      console.error('Failed to load file preview:', e);
      previewUrl.value = null;
    }
  },
  { immediate: true }
);

// Финальный URL для отображения: приоритет у локального preview
const displayUrl = computed(() => localPreviewUrl.value || previewUrl.value);

const aspectClass = computed(() => {
  return props.aspectRatio === 'wide' ? 'aspect-video' : 'aspect-square';
});

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (!file) return;
  
  // Клиентская валидация
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

  // Освобождаем предыдущий локальный preview
  if (localPreviewUrl.value) {
    revokeUrl(localPreviewUrl.value);
    localPreviewUrl.value = null;
  }
  
  // Создаём локальный preview (мгновенное отображение)
  const localUrl = URL.createObjectURL(file);
  localPreviewUrl.value = localUrl;
  
  try {
    // Загружаем на сервер
    const uploaded = await fileApi.upload(file);
    
    // Удаляем предыдущий файл на сервере, если был
    if (props.modelValue) {
      try {
        await fileApi.delete(props.modelValue);
      } catch (e) {
        console.warn('Failed to delete old file', e);
      }
    }
    
    // Эмитим новый file_id родителю
    emit('update:modelValue', uploaded.id);
    
    // localPreviewUrl оставляем — он быстрее и уже отображается.
    // Server preview не нужен, т.к. local уже работает.
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка при загрузке файла';
    // Очищаем всё при ошибке
    revokeUrl(localPreviewUrl.value);
    localPreviewUrl.value = null;
    emit('update:modelValue', null);
  } finally {
    isUploading.value = false;
    target.value = '';
  }
}

async function removeImage() {
  if (props.modelValue) {
    try {
      await fileApi.delete(props.modelValue);
    } catch (e) {
      console.warn('Failed to delete file', e);
    }
  }
  
  revokeUrl(localPreviewUrl.value);
  revokeUrl(previewUrl.value);
  localPreviewUrl.value = null;
  previewUrl.value = null;
  
  emit('update:modelValue', null);
}

// Cleanup при unmount компонента
onUnmounted(() => {
  revokeUrl(localPreviewUrl.value);
  revokeUrl(previewUrl.value);
});
</script>

<template>
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-2">{{ label }}</label>
    
    <div class="flex items-start gap-4">
      <!-- Превью -->
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
      
      <!-- Кнопки -->
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