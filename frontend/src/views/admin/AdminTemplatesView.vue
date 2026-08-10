<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { adminApi } from '../../api/admin';
import type { AdminTemplate } from '../../types/admin';
import TemplatePreview from '../../components/cards/TemplatePreview.vue';
import TemplatePreviewModal from '../../components/cards/TemplatePreviewModal.vue';
import TemplateCreateModal from '../../components/admin/TemplateCreateModal.vue';
import { getAxiosErrorMessage } from '../../utils/apiError';

const templates = ref<AdminTemplate[]>([]);
const total = ref(0);
const limit = ref(20);
const offset = ref(0);
const search = ref('');
const isLoading = ref(true);
const searchTimeout = ref<number>();
const uploadingId = ref<string | null>(null);
const previewTemplate = ref<AdminTemplate | null>(null);
const createOpen = ref(false);

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

function openPreview(template: AdminTemplate) {
  previewTemplate.value = template;
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6 gap-4 flex-wrap">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Шаблоны визиток</h2>
        <p class="text-sm text-gray-500 mt-1">Визуал задаётся CSS-файлами на диске</p>
      </div>
      <div class="flex gap-3 flex-wrap">
        <input
          v-model="search"
          type="text"
          placeholder="Поиск по названию или коду..."
          class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary w-64"
        />
        <button type="button" class="btn-primary" @click="createOpen = true">
          + Добавить шаблон
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="templates.length === 0" class="text-center py-12 text-gray-500">
      Шаблоны не найдены
      <div class="mt-4">
        <button type="button" class="btn-primary" @click="createOpen = true">
          Создать первый шаблон
        </button>
      </div>
    </div>

    <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <div
        v-for="template in templates"
        :key="template.id"
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-3"
        :class="{ 'opacity-60': !template.is_active }"
      >
        <div @click="openPreview(template)">
          <TemplatePreview :template="template" size="compact" :selected="false" />
        </div>

        <div class="mt-3">
          <div class="flex justify-between items-start gap-2 mb-1">
            <div class="min-w-0">
              <h3 class="font-semibold text-gray-900 text-sm truncate">{{ template.name }}</h3>
              <p class="text-[11px] text-gray-500 font-mono truncate">{{ template.code }}</p>
            </div>
            <span
              :class="[
                'px-1.5 py-0.5 rounded-full text-[10px] font-medium shrink-0',
                template.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800',
              ]"
            >
              {{ template.is_active ? 'ON' : 'OFF' }}
            </span>
          </div>

          <div class="flex justify-between items-center text-xs text-gray-500 mb-2">
            <span>{{ template.cards_count }} виз.</span>
            <span :class="template.has_css ? 'text-green-600' : 'text-orange-600'">
              {{ template.has_css ? 'CSS' : 'нет CSS' }}
            </span>
          </div>

          <div class="flex flex-col gap-1.5">
            <button type="button" class="btn-secondary text-xs w-full" @click="openPreview(template)">
              Просмотр
            </button>
            <label class="btn-secondary text-xs text-center cursor-pointer">
              <span v-if="uploadingId === template.id">Загрузка…</span>
              <span v-else>CSS</span>
              <input
                type="file"
                accept=".css,text/css"
                class="hidden"
                :disabled="uploadingId === template.id"
                @change="onCssSelected(template, $event)"
              />
            </label>
            <div class="flex gap-1.5">
              <button @click="toggleActive(template)" class="btn-secondary flex-1 text-xs">
                {{ template.is_active ? 'Выкл.' : 'Вкл.' }}
              </button>
              <button
                @click="deleteTemplate(template)"
                class="btn-danger text-xs px-2"
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

    <TemplatePreviewModal
      :template="previewTemplate"
      @close="previewTemplate = null"
    />

    <TemplateCreateModal
      :open="createOpen"
      @close="createOpen = false"
      @created="loadTemplates"
    />
  </div>
</template>
