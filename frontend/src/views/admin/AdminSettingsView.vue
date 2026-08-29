<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { adminApi } from '../../api/admin';
import type { DocsSettings, SmtpSettings } from '../../types/admin';
import { getAxiosErrorMessage } from '../../utils/apiError';
import { useAuthStore } from '../../stores/auth';

const { t } = useI18n();
const auth = useAuthStore();
const isSuperAdmin = computed(() => auth.user?.role === 'SUPERADMIN');

const settings = ref<SmtpSettings | null>(null);
const docsSettings = ref<DocsSettings | null>(null);
const isLoading = ref(true);
const isSaving = ref(false);
const isSavingDocs = ref(false);
const isTesting = ref(false);
const message = ref<string | null>(null);
const error = ref<string | null>(null);
const testToEmail = ref('');

const form = ref({
  enabled: false,
  host: 'smtp.gmail.com',
  port: 587,
  use_tls: true,
  use_ssl: false,
  username: '',
  password: '',
  from_email: '',
  from_name: 'DBCS',
});

const docsForm = ref({
  docs_enabled: true,
  redoc_enabled: true,
});

function applySettings(s: SmtpSettings) {
  settings.value = s;
  form.value = {
    enabled: s.enabled,
    host: s.host,
    port: s.port,
    use_tls: s.use_tls,
    use_ssl: s.use_ssl,
    username: s.username,
    password: '',
    from_email: s.from_email,
    from_name: s.from_name,
  };
  if (!testToEmail.value) {
    testToEmail.value = auth.user?.email || s.from_email || '';
  }
}

function applyDocsSettings(s: DocsSettings) {
  docsSettings.value = s;
  docsForm.value = {
    docs_enabled: s.docs_enabled,
    redoc_enabled: s.redoc_enabled,
  };
}

async function loadSettings() {
  if (!isSuperAdmin.value) {
    isLoading.value = false;
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    const [smtp, docs] = await Promise.all([
      adminApi.getSmtpSettings(),
      adminApi.getDocsSettings(),
    ]);
    applySettings(smtp);
    applyDocsSettings(docs);
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.loadSettings'));
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadSettings);

function applyGoogleDefaults() {
  form.value.host = 'smtp.gmail.com';
  form.value.port = 587;
  form.value.use_tls = true;
  form.value.use_ssl = false;
}

function applyYandexDefaults() {
  form.value.host = 'smtp.yandex.ru';
  form.value.port = 465;
  form.value.use_tls = false;
  form.value.use_ssl = true;
}

function onPortPreset() {
  if (form.value.port === 465) {
    form.value.use_ssl = true;
    form.value.use_tls = false;
  } else if (form.value.port === 587) {
    form.value.use_tls = true;
    form.value.use_ssl = false;
  }
}

async function saveDocsSettings() {
  isSavingDocs.value = true;
  message.value = null;
  error.value = null;
  try {
    const s = await adminApi.updateDocsSettings({
      docs_enabled: docsForm.value.docs_enabled,
      redoc_enabled: docsForm.value.redoc_enabled,
    });
    applyDocsSettings(s);
    message.value = t('admin.docsSaved');
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.saveDocs'));
  } finally {
    isSavingDocs.value = false;
  }
}

async function saveSettings() {
  isSaving.value = true;
  message.value = null;
  error.value = null;
  try {
    const payload: Record<string, unknown> = {
      enabled: form.value.enabled,
      host: form.value.host.trim(),
      port: form.value.port,
      use_tls: form.value.use_tls,
      use_ssl: form.value.use_ssl,
      username: form.value.username.trim(),
      from_email: form.value.from_email.trim(),
      from_name: form.value.from_name.trim() || 'DBCS',
    };
    if (form.value.password.trim()) {
      payload.password = form.value.password;
    }
    const s = await adminApi.updateSmtpSettings(payload);
    applySettings(s);
    message.value = t('admin.smtpSaved');
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.saveFailed'));
  } finally {
    isSaving.value = false;
  }
}

async function testSmtp() {
  isTesting.value = true;
  message.value = null;
  error.value = null;
  try {
    const payload: Record<string, unknown> = {
      to_email: testToEmail.value.trim() || undefined,
      host: form.value.host.trim(),
      port: form.value.port,
      use_tls: form.value.use_tls,
      use_ssl: form.value.use_ssl,
      username: form.value.username.trim(),
      from_email: form.value.from_email.trim(),
      from_name: form.value.from_name.trim() || 'DBCS',
    };
    if (form.value.password.trim()) {
      payload.password = form.value.password;
    }
    const result = await adminApi.testSmtpSettings(payload);
    message.value = result.detail;
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.smtpTest'));
  } finally {
    isTesting.value = false;
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">{{ t('admin.settings') }}</h2>
        <p class="text-sm text-gray-500 mt-1">{{ t('admin.settingsSubtitle') }}</p>
      </div>
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
        <div class="mb-6">
          <h3 class="text-lg font-semibold text-gray-900">{{ t('admin.docsTitle') }}</h3>
          <p class="text-sm text-gray-500 mt-1">
            {{ t('admin.docsHint') }}
          </p>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between gap-4 py-2 border-b border-gray-100">
            <div>
              <p class="text-sm font-medium text-gray-900">Swagger UI</p>
              <p class="text-xs text-gray-500 mt-0.5">/api/docs</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                v-model="docsForm.docs_enabled"
                type="checkbox"
                class="sr-only peer"
              />
              <span
                class="relative w-11 h-6 bg-gray-200 rounded-full peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"
              />
            </label>
          </div>

          <div class="flex items-center justify-between gap-4 py-2">
            <div>
              <p class="text-sm font-medium text-gray-900">ReDoc</p>
              <p class="text-xs text-gray-500 mt-0.5">/api/redoc</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                v-model="docsForm.redoc_enabled"
                type="checkbox"
                class="sr-only peer"
              />
              <span
                class="relative w-11 h-6 bg-gray-200 rounded-full peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"
              />
            </label>
          </div>
        </div>

        <div class="mt-6">
          <button
            type="button"
            class="btn-primary"
            :disabled="isSavingDocs || isSaving"
            @click="saveDocsSettings"
          >
            {{ isSavingDocs ? t('common.saving') : t('common.save') }}
          </button>
        </div>
      </section>

      <section class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div class="flex flex-wrap items-start justify-between gap-3 mb-6">
          <div>
            <h3 class="text-lg font-semibold text-gray-900">{{ t('admin.smtpTitle') }}</h3>
            <p class="text-sm text-gray-500 mt-1">
              {{ t('admin.smtpHint') }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button type="button" class="btn-secondary text-sm" @click="applyGoogleDefaults">
              {{ t('admin.presetGoogle') }}
            </button>
            <button type="button" class="btn-secondary text-sm" @click="applyYandexDefaults">
              {{ t('admin.presetYandex') }}
            </button>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="flex items-center gap-3 md:col-span-2">
            <input v-model="form.enabled" type="checkbox" class="rounded border-gray-300 text-primary focus:ring-primary" />
            <span class="text-sm font-medium text-gray-800">{{ t('admin.smtpEnable') }}</span>
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.host') }}</span>
            <input
              v-model="form.host"
              type="text"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="smtp.gmail.com"
            />
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.port') }}</span>
            <input
              v-model.number="form.port"
              type="number"
              min="1"
              max="65535"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              @change="onPortPreset"
            />
          </label>

          <label class="flex items-center gap-3">
            <input v-model="form.use_tls" type="checkbox" class="rounded border-gray-300 text-primary focus:ring-primary" />
            <span class="text-sm text-gray-800">{{ t('admin.startTls') }}</span>
          </label>

          <label class="flex items-center gap-3">
            <input v-model="form.use_ssl" type="checkbox" class="rounded border-gray-300 text-primary focus:ring-primary" />
            <span class="text-sm text-gray-800">{{ t('admin.sslTls') }}</span>
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.username') }}</span>
            <input
              v-model="form.username"
              type="text"
              autocomplete="off"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="user@gmail.com"
            />
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">Password</span>
            <input
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              :placeholder="settings?.password_set ? t('admin.passwordPlaceholderKeep') : t('admin.passwordPlaceholder')"
            />
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">From email</span>
            <input
              v-model="form.from_email"
              type="email"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="noreply@example.com"
            />
          </label>

          <label class="block">
            <span class="text-sm font-medium text-gray-700">From name</span>
            <input
              v-model="form.from_name"
              type="text"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="DBCS"
            />
          </label>
          <label class="block md:col-span-2">
            <span class="text-sm font-medium text-gray-700">{{ t('admin.testRecipient') }}</span>
            <input
              v-model="testToEmail"
              type="email"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="you@example.com"
            />
          </label>
        </div>

        <div class="mt-6 flex flex-wrap gap-3">
          <button type="button" class="btn-primary" :disabled="isSaving || isTesting" @click="saveSettings">
            {{ isSaving ? t('common.saving') : t('common.save') }}
          </button>
          <button type="button" class="btn-secondary" :disabled="isSaving || isTesting" @click="testSmtp">
            {{ isTesting ? t('admin.testSending') : t('admin.testSend') }}
          </button>
        </div>
      </section>
    </template>
  </div>
</template>
