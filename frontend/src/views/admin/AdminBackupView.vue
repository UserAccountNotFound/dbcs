<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { adminApi } from '../../api/admin';
import type { BackupFile, BackupSettings } from '../../types/admin';
import { getAxiosErrorMessage } from '../../utils/apiError';
import { useAuthStore } from '../../stores/auth';
import { useLocaleDate } from '../../composables/useLocaleDate';

const { t, tm } = useI18n();
const { formatDateTime } = useLocaleDate();
const auth = useAuthStore();
const router = useRouter();
const isSuperAdmin = computed(() => auth.user?.role === 'SUPERADMIN');

/** JS getDay(): 0=вс … 6=сб → ISO: 0=пн … 6=вс */
function jsDayToIso(jsDay: number): number {
  return (jsDay + 6) % 7;
}

function utcScheduleToLocal(utcHour: number, utcWeekday: number): { hour: number; weekday: number } {
  const d = new Date();
  d.setUTCHours(utcHour, 0, 0, 0);
  const currentUtcWd = jsDayToIso(d.getUTCDay());
  d.setUTCDate(d.getUTCDate() + (utcWeekday - currentUtcWd));
  return { hour: d.getHours(), weekday: jsDayToIso(d.getDay()) };
}

function localScheduleToUtc(localHour: number, localWeekday: number): { hour: number; weekday: number } {
  const d = new Date();
  d.setHours(localHour, 0, 0, 0);
  const currentLocalWd = jsDayToIso(d.getDay());
  d.setDate(d.getDate() + (localWeekday - currentLocalWd));
  return { hour: d.getUTCHours(), weekday: jsDayToIso(d.getUTCDay()) };
}

function timezoneLabel(): string {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
  const offsetMin = -new Date().getTimezoneOffset();
  const sign = offsetMin >= 0 ? '+' : '-';
  const abs = Math.abs(offsetMin);
  const hh = String(Math.floor(abs / 60)).padStart(2, '0');
  const mm = String(abs % 60).padStart(2, '0');
  const utc = `UTC${sign}${hh}:${mm}`;
  return tz ? `${tz} (${utc})` : utc;
}

const hourOptions = Array.from({ length: 24 }, (_, h) => ({
  value: h,
  label: `${String(h).padStart(2, '0')}:00`,
}));

const localTimezone = timezoneLabel();
const defaultLocal = utcScheduleToLocal(3, 0);

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
  schedule_hour: defaultLocal.hour,
  schedule_weekday: defaultLocal.weekday,
  retention_count: 7,
  enabled: true,
});

const weekdayLabels = computed(() => tm('admin.weekdays') as string[]);

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDt(value: string | null): string {
  return formatDateTime(value);
}

function applySettings(s: BackupSettings) {
  settings.value = s;
  const local = utcScheduleToLocal(s.schedule_hour, s.schedule_weekday);
  form.value = {
    storage_path: s.storage_path,
    schedule: s.schedule,
    schedule_hour: local.hour,
    schedule_weekday: local.weekday,
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
      errors.push(getAxiosErrorMessage(settingsResult.reason, t('errors.loadSettings')));
    }

    if (filesResult.status === 'fulfilled') {
      files.value = filesResult.value.items;
    } else {
      errors.push(getAxiosErrorMessage(filesResult.reason, t('errors.loadBackupList')));
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
    const utc = localScheduleToUtc(form.value.schedule_hour, form.value.schedule_weekday);
    const s = await adminApi.updateBackupSettings({
      storage_path: form.value.storage_path.trim(),
      schedule: form.value.schedule,
      schedule_hour: utc.hour,
      schedule_weekday: utc.weekday,
      retention_count: form.value.retention_count,
      enabled: form.value.schedule !== 'off',
    });
    applySettings(s);
    message.value = t('admin.backupSaved');
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.saveFailed'));
  } finally {
    isSaving.value = false;
  }
}

async function runBackup() {
  if (!confirm(t('admin.backupConfirm'))) return;
  isRunning.value = true;
  message.value = null;
  error.value = null;
  try {
    const result = await adminApi.runBackup();
    message.value = t('admin.backupCreated', { filename: result.filename, size: formatBytes(result.size_bytes) });
    await loadAll();
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.backupCreate'));
  } finally {
    isRunning.value = false;
  }
}

async function restoreBackup(file: BackupFile) {
  const ok = confirm(t('admin.restoreConfirm', { filename: file.filename }));
  if (!ok) return;
  const ok2 = confirm(t('admin.restoreConfirm2'));
  if (!ok2) return;

  restoringName.value = file.filename;
  message.value = null;
  error.value = null;
  try {
    const result = await adminApi.restoreBackup(file.filename);
    message.value = result.detail;
    alert(t('admin.restoreSuccess', { detail: result.detail }));
    await auth.forceLogout({ callApi: false });
    await router.push('/login');
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status;
    const isNetwork = !(e as { response?: unknown })?.response;
    if (isNetwork || status === 502 || status === 504) {
      alert(t('admin.restoreConnectionLost'));
      await auth.forceLogout({ callApi: false });
      await router.push('/login');
      return;
    }
    error.value = getAxiosErrorMessage(e, t('errors.backupRestore'));
  } finally {
    restoringName.value = null;
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900">{{ t('admin.backup') }}</h2>
    </div>

    <div
      v-if="!isSuperAdmin"
      class="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl px-4 py-3"
    >
      {{ t('admin.superAdminOnly') }}
    </div>

    <div v-else-if="isLoading" class="text-gray-500">{{ t('common.loading') }}</div>

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
        <h3 class="text-lg font-semibold text-gray-900 mb-1">{{ t('admin.backup') }}</h3>
        <p class="text-sm text-gray-500 mb-6">
          {{ t('admin.backupHint') }}
        </p>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="block md:col-span-2">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.storagePath') }}</span>
            <input
              v-model="form.storage_path"
              type="text"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="/var/lib/dbcs/backups"
            />
            <span class="mt-1 block text-xs text-gray-500">
              {{ t('admin.storagePathHint') }}
            </span>
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.schedule') }}</span>
            <select
              v-model="form.schedule"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="off">{{ t('admin.scheduleOff') }}</option>
              <option value="hourly">{{ t('admin.scheduleHourly') }}</option>
              <option value="daily">{{ t('admin.scheduleDaily') }}</option>
              <option value="weekly">{{ t('admin.scheduleWeekly') }}</option>
            </select>
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.retention') }}</span>
            <input
              v-model.number="form.retention_count"
              type="number"
              min="1"
              max="100"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </label>

          <label v-if="form.schedule === 'daily' || form.schedule === 'weekly'" class="block">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.runHour') }}</span>
            <select
              v-model.number="form.schedule_hour"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option v-for="opt in hourOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
            <span class="mt-1 block text-xs text-gray-500">
              {{ t('admin.runHourHint', { tz: localTimezone }) }}
            </span>
          </label>

          <label v-if="form.schedule === 'weekly'" class="block">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.weekday') }}</span>
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
          <div>{{ t('admin.lastRun') }} <span class="text-gray-900">{{ formatDt(settings.last_run_at) }}</span></div>
          <div>{{ t('admin.status') }} <span class="text-gray-900">{{ settings.last_status || t('common.dash') }}</span></div>
          <div class="md:col-span-2">{{ t('admin.message') }} <span class="text-gray-900">{{ settings.last_message || t('common.dash') }}</span></div>
          <div class="md:col-span-2">{{ t('admin.file') }} <span class="font-mono text-gray-900">{{ settings.last_backup_file || t('common.dash') }}</span></div>
        </div>

        <div class="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            class="btn-primary"
            :disabled="isSaving"
            @click="saveSettings"
          >
            {{ isSaving ? t('common.saving') : t('admin.saveSettings') }}
          </button>
          <button
            type="button"
            class="btn-secondary"
            :disabled="isRunning"
            @click="runBackup"
          >
            {{ isRunning ? t('admin.running') : t('admin.runNow') }}
          </button>
        </div>
      </section>

      <section class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-900">{{ t('admin.availableBackups') }}</h3>
        </div>
        <div v-if="files.length === 0" class="px-6 py-8 text-gray-500 text-sm">
          {{ t('admin.noBackups') }}
        </div>
        <table v-else class="w-full text-left text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="px-6 py-3 font-medium">{{ t('admin.fileColumn') }}</th>
              <th class="px-6 py-3 font-medium">{{ t('admin.sizeColumn') }}</th>
              <th class="px-6 py-3 font-medium">{{ t('admin.dateColumn') }}</th>
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
                  {{ restoringName === file.filename ? t('admin.restoring') : t('admin.restore') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </div>
</template>
