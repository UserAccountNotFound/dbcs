<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { adminApi } from '../../api/admin';
import type { TemplateMeta } from '../../types/template';
import { getAxiosErrorMessage } from '../../utils/apiError';

const { t } = useI18n();

defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'created'): void;
}>();

const isSubmitting = ref(false);
const error = ref('');
const cssFile = ref<File | null>(null);
const cssInput = ref<HTMLInputElement | null>(null);

const form = reactive({
  code: '',
  name: '',
  description: '',
  is_active: true,
  default_accent: '#0f766e',
  default_scheme: 'light' as 'light' | 'dark',
  effect: '' as '' | 'polygon',
});

function resetForm() {
  form.code = '';
  form.name = '';
  form.description = '';
  form.is_active = true;
  form.default_accent = '#0f766e';
  form.default_scheme = 'light';
  form.effect = '';
  cssFile.value = null;
  error.value = '';
  if (cssInput.value) cssInput.value.value = '';
}

function close() {
  if (isSubmitting.value) return;
  resetForm();
  emit('close');
}

function onCssChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  if (file && !file.name.endsWith('.css')) {
    error.value = t('errors.cssRequired');
    input.value = '';
    cssFile.value = null;
    return;
  }
  error.value = '';
  cssFile.value = file;
}

function normalizeCode(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9_-]/g, '');
}

async function handleSubmit() {
  error.value = '';
  const code = normalizeCode(form.code);
  if (!code || code.length < 2) {
    error.value = t('template.codeInvalid');
    return;
  }
  if (!form.name.trim()) {
    error.value = t('template.nameRequired');
    return;
  }

  const meta: TemplateMeta = {
    version: 2,
    default_accent: form.default_accent,
    default_scheme: form.default_scheme,
    effect: form.effect || null,
  };

  isSubmitting.value = true;
  try {
    const created = await adminApi.createTemplate({
      code,
      name: form.name.trim(),
      description: form.description.trim() || null,
      is_active: form.is_active,
      meta,
    });

    if (cssFile.value && created?.id) {
      await adminApi.uploadTemplateCss(created.id, cssFile.value);
    }

    resetForm();
    emit('created');
    emit('close');
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.templateCreate'));
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
    @click.self="close"
  >
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden max-h-[90vh] flex flex-col">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between shrink-0">
        <h3 class="text-lg font-semibold text-gray-900">{{ t('template.newTitle') }}</h3>
        <button
          type="button"
          class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          :disabled="isSubmitting"
          @click="close"
        >
          ×
        </button>
      </div>

      <form class="px-6 py-5 space-y-4 overflow-y-auto flex-1" @submit.prevent="handleSubmit">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ t('template.code') }}</label>
            <input
              v-model="form.code"
              type="text"
              placeholder="my-theme"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary font-mono text-sm"
              @blur="form.code = normalizeCode(form.code)"
            />
            <p class="mt-1 text-xs text-gray-500">{{ t('template.codeHint') }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ t('template.name') }}</label>
            <input
              v-model="form.name"
              type="text"
              :placeholder="t('template.namePlaceholder')"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700">{{ t('template.description') }}</label>
          <textarea
            v-model="form.description"
            rows="2"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ t('template.accent') }}</label>
            <input
              v-model="form.default_accent"
              type="color"
              class="mt-1 h-10 w-full p-1 border border-gray-300 rounded-md cursor-pointer"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ t('template.scheme') }}</label>
            <select
              v-model="form.default_scheme"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
            >
              <option value="light">{{ t('cardForm.light') }}</option>
              <option value="dark">{{ t('cardForm.dark') }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ t('template.effect') }}</label>
            <select
              v-model="form.effect"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
            >
              <option value="">{{ t('template.none') }}</option>
              <option value="polygon">Polygon</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700">{{ t('template.cssFile') }}</label>
          <input
            ref="cssInput"
            type="file"
            accept=".css,text/css"
            class="mt-1 block w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:bg-teal-50 file:text-primary file:font-medium"
            @change="onCssChange"
          />
          <p class="mt-1 text-xs text-gray-500">
            {{ t('template.cssOptional') }}
            <code class="font-mono">.tpl-{{ form.code || 'code' }}</code>.
          </p>
        </div>

        <label class="inline-flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
          <input
            v-model="form.is_active"
            type="checkbox"
            class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          {{ t('template.activeOnCreate') }}
        </label>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

        <div class="flex justify-end gap-3 pt-2">
          <button type="button" class="btn-secondary" :disabled="isSubmitting" @click="close">
            {{ t('common.cancel') }}
          </button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? t('common.creating') : t('common.create') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
