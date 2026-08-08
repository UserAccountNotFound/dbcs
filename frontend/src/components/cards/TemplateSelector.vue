<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { templateApi } from '../../api/templates';
import type { Template } from '../../types/template';
import TemplatePreview from './TemplatePreview.vue';

const props = defineProps<{
  modelValue: string | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | null): void;
  (e: 'template-selected', template: Template | null): void;
}>();

const templates = ref<Template[]>([]);
const isLoading = ref(true);
const error = ref('');

onMounted(async () => {
  try {
    const response = await templateApi.getTemplates();
    templates.value = response.items;
  } catch (e) {
    error.value = 'Не удалось загрузить шаблоны';
  } finally {
    isLoading.value = false;
  }
});

function selectTemplate(template: Template) {
  // Повторный клик по выбранному шаблону снимает выбор
  if (props.modelValue === template.id) {
    emit('update:modelValue', null);
    emit('template-selected', null);
  } else {
    emit('update:modelValue', template.id);
    emit('template-selected', template);
  }
}
</script>

<template>
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-3">
      Шаблон дизайна
      <span class="text-gray-400 font-normal">(необязательно)</span>
    </label>
    
    <div v-if="isLoading" class="flex justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
    
    <div v-else-if="error" class="text-red-600 text-sm py-4">
      {{ error }}
    </div>
    
    <div v-else-if="templates.length === 0" class="text-gray-500 text-sm py-4">
      Нет доступных шаблонов. Визитка будет использовать базовый стиль.
    </div>
    
    <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <div 
        v-for="template in templates" 
        :key="template.id"
        @click="selectTemplate(template)"
        class="relative cursor-pointer"
      >
        <TemplatePreview 
          :schema="template.schema_data"
          :template-name="template.name"
          :selected="modelValue === template.id"
        />
        
        <div class="mt-2 text-center">
          <span 
            class="text-sm font-medium"
            :class="modelValue === template.id ? 'text-primary' : 'text-gray-700'"
          >
            {{ template.name }}
          </span>
          <p v-if="template.description" class="text-xs text-gray-500 mt-1 line-clamp-2">
            {{ template.description }}
          </p>
        </div>
        
        <!-- Индикатор выбора -->
        <div 
          v-if="modelValue === template.id"
          class="absolute top-2 right-2 w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-sm shadow-md"
        >
          ✓
        </div>
      </div>
    </div>
  </div>
</template>