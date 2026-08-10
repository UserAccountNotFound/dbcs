<script setup lang="ts">
import { ref, watch } from 'vue';
import { cardApi, type CardImportResult } from '../../api/cards';

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'imported'): void;
}>();

type TransferFormat = 'json' | 'csv';

const mode = ref<'export' | 'import'>('export');
const format = ref<TransferFormat>('json');
const isBusy = ref(false);
const error = ref('');
const importResult = ref<CardImportResult | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);

watch(
  () => props.open,
  (open) => {
    if (open) {
      error.value = '';
      importResult.value = null;
      selectedFile.value = null;
      if (fileInput.value) fileInput.value.value = '';
    }
  },
);

function close() {
  if (isBusy.value) return;
  emit('close');
}

async function handleExport() {
  isBusy.value = true;
  error.value = '';
  try {
    const blob = await cardApi.exportCards(format.value);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = format.value === 'csv' ? 'dbcs-cards.csv' : 'dbcs-cards.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error(e);
    error.value = 'Не удалось экспортировать визитки.';
  } finally {
    isBusy.value = false;
  }
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
  importResult.value = null;
  error.value = '';
}

async function handleImport() {
  if (!selectedFile.value) {
    error.value = 'Выберите файл для импорта.';
    return;
  }

  isBusy.value = true;
  error.value = '';
  importResult.value = null;
  try {
    const result = await cardApi.importCards(selectedFile.value, format.value);
    importResult.value = result;
    if (result.created > 0) {
      emit('imported');
    }
  } catch (e: unknown) {
    console.error(e);
    const detail =
      (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    error.value = typeof detail === 'string' ? detail : 'Не удалось импортировать визитки.';
  } finally {
    isBusy.value = false;
  }
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
    @click.self="close"
  >
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900">Экспорт / импорт</h3>
        <button
          type="button"
          class="text-gray-400 hover:text-gray-600 text-xl leading-none"
          :disabled="isBusy"
          @click="close"
        >
          ×
        </button>
      </div>

      <div class="px-6 py-5 space-y-5">
        <div class="flex rounded-lg bg-gray-100 p-1 gap-1">
          <button
            type="button"
            class="flex-1 py-2 text-sm font-medium rounded-md transition-colors"
            :class="mode === 'export' ? 'bg-white shadow text-gray-900' : 'text-gray-500'"
            @click="mode = 'export'; importResult = null; error = ''"
          >
            Экспорт
          </button>
          <button
            type="button"
            class="flex-1 py-2 text-sm font-medium rounded-md transition-colors"
            :class="mode === 'import' ? 'bg-white shadow text-gray-900' : 'text-gray-500'"
            @click="mode = 'import'; importResult = null; error = ''"
          >
            Импорт
          </button>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Формат</label>
          <div class="flex gap-4">
            <label class="inline-flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input v-model="format" type="radio" value="json" class="text-primary focus:ring-primary" />
              JSON
            </label>
            <label class="inline-flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input v-model="format" type="radio" value="csv" class="text-primary focus:ring-primary" />
              CSV
            </label>
          </div>
        </div>

        <template v-if="mode === 'export'">
          <p class="text-sm text-gray-500">
            Будут выгружены все ваши визитки (без аватаров и логотипов). Ссылки и QR при импорте создаются заново.
          </p>
          <button
            type="button"
            class="btn-primary w-full"
            :disabled="isBusy"
            @click="handleExport"
          >
            {{ isBusy ? 'Подготовка…' : `Скачать ${format.toUpperCase()}` }}
          </button>
        </template>

        <template v-else>
          <p class="text-sm text-gray-500">
            Загрузите файл, ранее экспортированный из DBCS. Новые визитки добавятся к существующим.
          </p>
          <div>
            <input
              ref="fileInput"
              type="file"
              class="block w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:bg-teal-50 file:text-primary file:font-medium hover:file:bg-teal-100"
              :accept="format === 'csv' ? '.csv,text/csv' : '.json,application/json'"
              @change="onFileChange"
            />
            <p v-if="selectedFile" class="mt-2 text-xs text-gray-500">
              Выбран файл: {{ selectedFile.name }}
            </p>
          </div>
          <button
            type="button"
            class="btn-primary w-full"
            :disabled="isBusy || !selectedFile"
            @click="handleImport"
          >
            {{ isBusy ? 'Импорт…' : 'Импортировать' }}
          </button>

          <div
            v-if="importResult"
            class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm"
          >
            <p class="text-gray-800">
              Создано: <span class="font-semibold text-teal-700">{{ importResult.created }}</span>,
              ошибок: <span class="font-semibold" :class="importResult.failed ? 'text-red-600' : 'text-gray-700'">{{ importResult.failed }}</span>
            </p>
            <ul
              v-if="importResult.errors.length"
              class="mt-2 space-y-1 text-xs text-red-600 max-h-32 overflow-y-auto"
            >
              <li v-for="(item, idx) in importResult.errors" :key="idx">
                #{{ item.index }}: {{ item.error }}
              </li>
            </ul>
          </div>
        </template>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      </div>
    </div>
  </div>
</template>
