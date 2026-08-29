<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { adminApi } from '../../api/admin';
import type { BackupFile, BackupSettings } from '../../types/admin';
import { getAxiosErrorMessage } from '../../utils/apiError';
import { useAuthStore } from '../../stores/auth';

const auth = useAuthStore();
const router = useRouter();
const isSuperAdmin = computed(() => auth.user?.role === 'SUPERADMIN');

const settings = ref<BackupSettings | null>(null);
const files = ref<BackupFile[]>([]);
const isLoading = ref(true);
const isSaving = ref(false);
const isRunning = ref(false);
const restoringName = ref<string | null>(null);
const message = ref<string | null>(null);
const error = ref<string | null>(null);

const form = ref({
  storage_path: '/var/lib/dbcs/backups',
  schedule: 'daily' as BackupSettings['schedule'],
  schedule_hour: 3,
  schedule_weekday: 0,
  retention_count: 7,
  enabled: true,
});

const weekdayLabels = [
  'Понедельник',
  'Вторник',
  'Среда',
  'Четверг',
  'Пятница',
  'Суббота',
  'Воскресенье',
];

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDt(value: string | null): string {
  if (!value) return '—';
  try {
    return new Date(value.endsWith('Z') ? value : `${value}Z`).toLocaleString('ru-RU');
  } catch {
    return value;
  }
}

function applySettings(s: BackupSettings) {
  settings.value = s;
  form.value = {
    storage_path: s.storage_path,
    schedule: s.schedule,
    schedule_hour: s.schedule_hour,
    schedule_weekday: s.schedule_weekday,
    retention_count: s.retention_count,
    enabled: s.enabled,
  };
}

async function loadAll() {
  if (!isSuperAdmin.value) {
    isLoading.value = false;
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    const results = await Promise.allSettled([
      adminApi.getBackupSettings(),
      adminApi.listBackupFiles(),
    ]);

    const settingsResult = results[0];
    const filesResult = results[1];
    const errors: string[] = [];

    if (settingsResult.status === 'fulfilled') {
      applySettings(settingsResult.value);
    } else {
      errors.push(getAxiosErrorMessage(settingsResult.reason, 'Не удалось загрузить настройки'));
    }

    if (filesResult.status === 'fulfilled') {
      files.value = filesResult.value.items;
    } else {
      errors.push(getAxiosErrorMessage(filesResult.reason, 'Не удалось загрузить список копий'));
    }

    if (errors.length) {
      error.value = errors.join(' · ');
    }
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadAll);

async function saveSettings() {
  isSaving.value = true;
  message.value = null;
  error.value = null;
  try {
    const s = await adminApi.updateBackupSettings({
      storage_path: form.value.storage_path.trim(),
      schedule: form.value.schedule,
      schedule_hour: form.value.schedule_hour,
      schedule_weekday: form.value.schedule_weekday,
      retention_count: form.value.retention_count,
      enabled: form.value.schedule !== 'off',
    });
    applySettings(s);
    message.value = 'Настройки сохранены.';
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, 'Ошибка сохранения');
  } finally {
    isSaving.value = false;
  }
}

async function runBackup() {
  if (!confirm('Создать резервную копию сейчас?')) return;
  isRunning.value = true;
  message.value = null;
  error.value = null;
  try {
    const result = await adminApi.runBackup();
    message.value = `Создано: ${result.filename} (${formatBytes(result.size_bytes)})`;
    await loadAll();
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, 'Ошибка создания копии');
  } finally {
    isRunning.value = false;
  }
}

async function restoreBackup(file: BackupFile) {
  const ok = confirm(
    `Восстановить из «${file.filename}»?\n\nТекущая база и uploads будут перезаписаны. Действие необратимо.\nПосле восстановления потребуется повторный вход.`,
  );
  if (!ok) return;
  const ok2 = confirm('Подтвердите ещё раз: восстановить систему из этой копии?');
  if (!ok2) return;

  restoringName.value = file.filename;
  message.value = null;
  error.value = null;
  try {
    const result = await adminApi.restoreBackup(file.filename);
    message.value = result.detail;
    alert(`${result.detail}\n\nСейчас откроется страница входа.`);
    await auth.forceLogout({ callApi: false });
    await router.push('/login');
  } catch (e: unknown) {
    // Nginx/прокси мог оборвать ответ после успешного restore — сессии уже сброшены.
    const status = (e as { response?: { status?: number } })?.response?.status;
    const isNetwork = !(e as { response?: unknown })?.response;
    if (isNetwork || status === 502 || status === 504) {
      alert(
        'Связь с сервером прервалась во время восстановления.\nПроверьте данные и войдите заново.',
      );
      await auth.forceLogout({ callApi: false });
      await router.push('/login');
      return;
    }
    error.value = getAxiosErrorMessage(e, 'Ошибка восстановления');
  } finally {
    restoringName.value = null;
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900">Резервное копирование</h2>
    </div>

    <div
      v-if="!isSuperAdmin"
      class="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl px-4 py-3"
    >
      Раздел доступен только супер-администратору.
    </div>

    <div v-else-if="isLoading" class="text-gray-500">Загрузка…</div>

    <template v-else>
      <div
        v-if="message"
        class="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-900"
      >
        {{ message }}
      </div>
      <div
        v-if="error"
        class="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800"
      >
        {{ error }}
      </div>

      <section class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-1">Резервное копирование</h3>
        <p class="text-sm text-gray-500 mb-6">
          Копия включает дамп базы данных и каталог загрузок (uploads).
        </p>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="block md:col-span-2">
            <span class="text-sm font-medium text-gray-700">Путь хранения</span>
            <input
              v-model="form.storage_path"
              type="text"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="/var/lib/dbcs/backups"
            />
            <span class="mt-1 block text-xs text-gray-500">
              Только внутри /var/lib/dbcs или /opt/dbcs/backups
            </span>
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">Периодичность</span>
            <select
              v-model="form.schedule"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="off">Выключено</option>
              <option value="hourly">Каждый час</option>
              <option value="daily">Ежедневно</option>
              <option value="weekly">Еженедельно</option>
            </select>
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">Хранить копий</span>
            <input
              v-model.number="form.retention_count"
              type="number"
              min="1"
              max="100"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </label>

          <label v-if="form.schedule === 'daily' || form.schedule === 'weekly'" class="block">
            <span class="text-sm font-medium text-gray-700">Час запуска (UTC)</span>
            <input
              v-model.number="form.schedule_hour"
              type="number"
              min="0"
              max="23"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </label>

          <label v-if="form.schedule === 'weekly'" class="block">
            <span class="text-sm font-medium text-gray-700">День недели</span>
            <select
              v-model.number="form.schedule_weekday"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option v-for="(label, idx) in weekdayLabels" :key="idx" :value="idx">
                {{ label }}
              </option>
            </select>
          </label>
        </div>

        <div
          v-if="settings"
          class="mt-6 grid gap-2 text-sm text-gray-600 md:grid-cols-2 bg-gray-50 rounded-lg p-4"
        >
          <div>Последний запуск: <span class="text-gray-900">{{ formatDt(settings.last_run_at) }}</span></div>
          <div>Статус: <span class="text-gray-900">{{ settings.last_status || '—' }}</span></div>
          <div class="md:col-span-2">Сообщение: <span class="text-gray-900">{{ settings.last_message || '—' }}</span></div>
          <div class="md:col-span-2">Файл: <span class="font-mono text-gray-900">{{ settings.last_backup_file || '—' }}</span></div>
        </div>

        <div class="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            class="btn-primary"
            :disabled="isSaving"
            @click="saveSettings"
          >
            {{ isSaving ? 'Сохранение…' : 'Сохранить настройки' }}
          </button>
          <button
            type="button"
            class="btn-secondary"
            :disabled="isRunning"
            @click="runBackup"
          >
            {{ isRunning ? 'Создание…' : 'Создать копию сейчас' }}
          </button>
        </div>
      </section>

      <section class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-900">Доступные копии</h3>
        </div>
        <div v-if="files.length === 0" class="px-6 py-8 text-gray-500 text-sm">
          Пока нет файлов резервных копий.
        </div>
        <table v-else class="w-full text-left text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="px-6 py-3 font-medium">Файл</th>
              <th class="px-6 py-3 font-medium">Размер</th>
              <th class="px-6 py-3 font-medium">Дата</th>
              <th class="px-6 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="file in files" :key="file.filename" class="border-t border-gray-100">
              <td class="px-6 py-3 font-mono text-xs text-gray-900">{{ file.filename }}</td>
              <td class="px-6 py-3 text-gray-700">{{ formatBytes(file.size_bytes) }}</td>
              <td class="px-6 py-3 text-gray-700">{{ formatDt(file.created_at) }}</td>
              <td class="px-6 py-3 text-right">
                <button
                  type="button"
                  class="text-red-600 hover:text-red-700 font-medium disabled:opacity-50"
                  :disabled="restoringName !== null"
                  @click="restoreBackup(file)"
                >
                  {{ restoringName === file.filename ? 'Восстановление…' : 'Восстановить' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </div>
</template>
