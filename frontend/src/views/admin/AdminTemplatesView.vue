<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { adminApi } from '../../api/admin';
import type { AdminTemplate } from '../../types/admin';
import TemplatePreview from '../../components/cards/TemplatePreview.vue';
import { getAxiosErrorMessage } from '../../utils/apiError';

const templates = ref<AdminTemplate[]>([]);
const total = ref(0);
const limit = ref(20);
const offset = ref(0);
const search = ref('');
const isLoading = ref(true);
const searchTimeout = ref<number>();
const uploadingId = ref<string | null>(null);

async function loadTemplates() {
  isLoading.value = true;
  try {
    const response = await adminApi.getTemplates(limit.value, offset.value, search.value);
    templates.value = response.items;
    total.value = response.total;
  } catch (e) {
    console.error('Failed to load templates', e);
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadTemplates);

watch(search, () => {
  clearTimeout(searchTimeout.value);
  searchTimeout.value = window.setTimeout(() => {
    offset.value = 0;
    loadTemplates();
  }, 500);
});

async function toggleActive(template: AdminTemplate) {
  try {
    await adminApi.toggleTemplate(template.id);
    template.is_active = !template.is_active;
  } catch (e: unknown) {
    alert(getAxiosErrorMessage(e, 'Ошибка при изменении статуса'));
  }
}

async function deleteTemplate(template: AdminTemplate) {
  if (template.cards_count > 0) {
    alert(`Нельзя удалить: шаблон используется ${template.cards_count} визитками.`);
    return;
  }

  if (!confirm(`Удалить шаблон "${template.name}"?`)) return;

  try {
    await adminApi.deleteTemplate(template.id);
    await loadTemplates();
  } catch (e: unknown) {
    alert(getAxiosErrorMessage(e, 'Ошибка при удалении'));
  }
}

async function onCssSelected(template: AdminTemplate, event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (!file) return;

  if (!file.name.endsWith('.css')) {
    alert('Нужен файл .css');
    return;
  }

  uploadingId.value = template.id;
  try {
    const updated = await adminApi.uploadTemplateCss(template.id, file);
    Object.assign(template, updated);
    alert(`CSS для «${template.name}» загружен.`);
  } catch (e: unknown) {
    alert(getAxiosErrorMessage(e, 'Ошибка загрузки CSS'));
  } finally {
    uploadingId.value = null;
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Шаблоны визиток</h2>
        <p class="text-sm text-gray-500 mt-1">Визуал задаётся CSS-файлами на диске</p>
      </div>
      <div class="flex gap-3">
        <input
          v-model="search"
          type="text"
          placeholder="Поиск по названию или коду..."
          class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary w-64"
        />
      </div>
    </div>

    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="templates.length === 0" class="text-center py-12 text-gray-500">
      Шаблоны не найдены
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="template in templates"
        :key="template.id"
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-4"
        :class="{ 'opacity-60': !template.is_active }"
      >
        <TemplatePreview :template="template" :selected="false" />

        <div class="mt-4">
          <div class="flex justify-between items-start mb-2">
            <div>
              <h3 class="font-semibold text-gray-900">{{ template.name }}</h3>
              <p class="text-xs text-gray-500">code: {{ template.code }}</p>
            </div>
            <span
              :class="[
                'px-2 py-1 rounded-full text-xs font-medium',
                template.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800',
              ]"
            >
              {{ template.is_active ? 'Активен' : 'Отключен' }}
            </span>
          </div>

          <p class="text-sm text-gray-600 mb-3 line-clamp-2">
            {{ template.description || 'Без описания' }}
          </p>

          <div class="flex justify-between items-center text-sm text-gray-500 mb-3">
            <span>Визиток: {{ template.cards_count }}</span>
            <span :class="template.has_css ? 'text-green-600' : 'text-orange-600'">
              {{ template.has_css ? 'CSS есть' : 'Нет CSS' }}
            </span>
          </div>

          <div class="flex flex-col gap-2">
            <label class="btn-secondary flex-1 text-sm text-center cursor-pointer">
              <span v-if="uploadingId === template.id">Загрузка…</span>
              <span v-else>Загрузить CSS</span>
              <input
                type="file"
                accept=".css,text/css"
                class="hidden"
                :disabled="uploadingId === template.id"
                @change="onCssSelected(template, $event)"
              />
            </label>
            <div class="flex gap-2">
              <button @click="toggleActive(template)" class="btn-secondary flex-1 text-sm">
                {{ template.is_active ? 'Деактивировать' : 'Активировать' }}
              </button>
              <button
                @click="deleteTemplate(template)"
                class="btn-danger text-sm"
                :disabled="template.cards_count > 0"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex justify-between items-center mt-6">
      <p class="text-sm text-gray-500">Всего: {{ total }}</p>
    </div>
  </div>
</template>
