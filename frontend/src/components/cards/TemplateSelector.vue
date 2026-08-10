<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { templateApi } from '../../api/templates';
import type { Template } from '../../types/template';
import TemplatePreview from './TemplatePreview.vue';
import TemplatePreviewModal from './TemplatePreviewModal.vue';

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
const previewTemplate = ref<Template | null>(null);

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

function openPreview(template: Template) {
  previewTemplate.value = template;
}

function selectTemplate(template: Template) {
  emit('update:modelValue', template.id);
  emit('template-selected', template);
  previewTemplate.value = null;
}

function clearSelection() {
  emit('update:modelValue', null);
  emit('template-selected', null);
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between gap-3 mb-3">
      <label class="block text-sm font-medium text-gray-700">
        Шаблон дизайна
        <span class="text-gray-400 font-normal">(необязательно)</span>
      </label>
      <button
        v-if="modelValue"
        type="button"
        class="text-xs text-gray-500 hover:text-red-600"
        @click="clearSelection"
      >
        Сбросить выбор
      </button>
    </div>
    
    <div v-if="isLoading" class="flex justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
    
    <div v-else-if="error" class="text-red-600 text-sm py-4">
      {{ error }}
    </div>
    
    <div v-else-if="templates.length === 0" class="text-gray-500 text-sm py-4">
      Нет доступных шаблонов. Визитка будет использовать базовый стиль.
    </div>
    
    <div v-else class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 gap-3">
      <div 
        v-for="template in templates" 
        :key="template.id"
        class="relative"
        @click="openPreview(template)"
      >
        <TemplatePreview 
          :template="template"
          size="compact"
          :selected="modelValue === template.id"
        />
        
        <div class="mt-1.5 text-center px-0.5">
          <span 
            class="text-xs font-medium line-clamp-1"
            :class="modelValue === template.id ? 'text-primary' : 'text-gray-700'"
          >
            {{ template.name }}
          </span>
        </div>
        
        <div 
          v-if="modelValue === template.id"
          class="absolute top-1.5 right-1.5 w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center text-[10px] shadow-md"
        >
          ✓
        </div>
      </div>
    </div>

    <p class="mt-2 text-xs text-gray-400">Нажмите на плитку, чтобы открыть увеличенный просмотр.</p>

    <TemplatePreviewModal
      :template="previewTemplate"
      :selected="previewTemplate?.id === modelValue"
      show-select
      @close="previewTemplate = null"
      @select="selectTemplate"
    />
  </div>
</template>
