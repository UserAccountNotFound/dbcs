<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { fileApi } from '../../api/files';

const props = defineProps<{
  modelValue: string | null;  // file_id
  label: string;
  aspectRatio?: 'square' | 'wide';
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | null): void;
}>();

const isUploading = ref(false);
const previewUrl = ref<string | null>(null);
const error = ref('');

// Создаем preview URL для существующего файла
watch(() => props.modelValue, (newId) => {
  if (newId) {
    previewUrl.value = fileApi.getFileUrl(newId);
  } else {
    previewUrl.value = null;
  }
}, { immediate: true });

const aspectClass = computed(() => {
  return props.aspectRatio === 'wide' 
    ? 'aspect-video' 
    : 'aspect-square';
});

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (!file) return;
  
  // Валидация на клиенте
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
  
  try {
    // Создаем локальный preview
    const localPreview = URL.createObjectURL(file);
    previewUrl.value = localPreview;
    
    // Загружаем на сервер
    const uploaded = await fileApi.upload(file);
    
    // Если был предыдущий файл - удаляем
    if (props.modelValue) {
      try {
        await fileApi.delete(props.modelValue);
      } catch (e) {
        console.warn('Failed to delete old file', e);
      }
    }
    
    // Отдаем новый file_id родителю
    emit('update:modelValue', uploaded.id);
    
    // Освобождаем локальный preview (теперь используем серверный URL)
    URL.revokeObjectURL(localPreview);
    previewUrl.value = fileApi.getFileUrl(uploaded.id);
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка при загрузке файла';
    previewUrl.value = null;
    emit('update:modelValue', null);
  } finally {
    isUploading.value = false;
    target.value = '';  // Сбрасываем input для возможности повторной загрузки того же файла
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
  previewUrl.value = null;
  emit('update:modelValue', null);
}
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
          v-if="previewUrl" 
          :src="previewUrl" 
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
          {{ previewUrl ? 'Заменить' : 'Загрузить' }}
          <input 
            type="file" 
            accept="image/jpeg,image/png,image/webp"
            class="hidden"
            @change="handleFileSelect"
            :disabled="isUploading"
          />
        </label>
        
        <button 
          v-if="previewUrl"
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