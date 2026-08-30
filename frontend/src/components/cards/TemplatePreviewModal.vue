<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Template } from '../../types/template';
import TemplatePreview from './TemplatePreview.vue';

defineProps<{
  template: Template | null;
  selected?: boolean;
  showSelect?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'select', template: Template): void;
}>();

const { t } = useI18n();
</script>

<template>
  <div
    v-if="template"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
    @click.self="emit('close')"
  >
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden max-h-[90vh] flex flex-col">
      <div class="px-5 py-4 border-b border-gray-100 flex items-start justify-between gap-3 shrink-0">
        <div class="min-w-0">
          <h3 class="text-lg font-semibold text-gray-900 truncate">{{ template.name }}</h3>
          <p class="text-xs text-gray-500 mt-0.5">code: {{ template.code }}</p>
          <p v-if="template.description" class="text-sm text-gray-600 mt-2">
            {{ template.description }}
          </p>
        </div>
        <button
          type="button"
          class="text-gray-400 hover:text-gray-600 text-2xl leading-none shrink-0"
          :aria-label="t('common.close')"
          @click="emit('close')"
        >
          ×
        </button>
      </div>

      <div class="p-4 overflow-y-auto flex-1 bg-gray-100">
        <TemplatePreview :template="template" size="large" :selected="selected" />
      </div>

      <div class="px-5 py-4 border-t border-gray-100 flex justify-end gap-3 shrink-0">
        <button type="button" class="btn-secondary" @click="emit('close')">
          {{ t('common.close') }}
        </button>
        <button
          v-if="showSelect"
          type="button"
          class="btn-primary"
          @click="emit('select', template)"
        >
          {{ selected ? t('template.selected') : t('template.select') }}
        </button>
      </div>
    </div>
  </div>
</template>
