<script setup lang="ts">
import { reactive, ref, watch } from 'vue';
import type { Card, CardCreatePayload, CardUpdatePayload, CardTheme } from '../../types/card';
import type { Template, TemplateMeta } from '../../types/template';
import ImageUploader from './ImageUploader.vue';
import TemplateSelector from './TemplateSelector.vue';

const props = defineProps<{
  card?: Card;
  isSubmitting: boolean;
}>();

const emit = defineEmits<{
  (e: 'submit', payload: CardCreatePayload | CardUpdatePayload): void;
}>();

const defaultTheme: CardTheme = {
  color_scheme: 'light',
  layout: 'classic',
  font: 'inter',
  accent_color: '#0f766e',
  show_photo: true,
  show_qr: true,
};

const form = reactive<CardCreatePayload>({
  title: '',
  full_name: '',
  job_title: '',
  department: '',
  company: '',
  phone: '',
  phone_additional: '',
  telegram: '',
  whatsapp: '',
  viber: '',
  wechat: '',
  messenger_max: '',
  discord: '',
  vk: '',
  email: '',
  website: '',
  address: '',
  note: '',
  template_id: null,
  theme: { ...defaultTheme },
  avatar_file_id: null,
  logo_file_id: null,
});

// Состояние для уведомления о применении шаблона
const templateApplied = ref(false);
const selectedTemplate = ref<Template | null>(null);
let appliedTimeout: number | undefined;

// Заполнение формы при редактировании существующей карточки
watch(
  () => props.card,
  (newCard) => {
    if (newCard) {
      form.title = newCard.title;
      form.full_name = newCard.full_name;
      form.job_title = newCard.job_title || '';
      form.department = newCard.department || '';
      form.company = newCard.company || '';
      form.phone = newCard.phone || '';
      form.phone_additional = newCard.phone_additional || '';
      form.telegram = newCard.telegram || '';
      form.whatsapp = newCard.whatsapp || '';
      form.viber = newCard.viber || '';
      form.wechat = newCard.wechat || '';
      form.messenger_max = newCard.messenger_max || '';
      form.discord = newCard.discord || '';
      form.vk = newCard.vk || '';
      form.email = newCard.email || '';
      form.website = newCard.website || '';
      form.address = newCard.address || '';
      form.note = newCard.note || '';
      form.template_id = newCard.template_id;
      form.theme = { ...newCard.theme };
      form.avatar_file_id = newCard.avatar_file_id || null;
      form.logo_file_id = newCard.logo_file_id || null;
    }
  },
  { immediate: true }
);

/**
 * Применяет дефолты из meta шаблона к CSS-переменным темы.
 */
function applyTemplateMeta(meta: TemplateMeta | null | undefined) {
  if (!meta) return;
  if (meta.default_accent) {
    form.theme.accent_color = meta.default_accent;
  }
  if (meta.default_scheme === 'light' || meta.default_scheme === 'dark') {
    form.theme.color_scheme = meta.default_scheme;
  }
}

/**
 * Обработчик выбора шаблона из TemplateSelector.
 */
function handleTemplateSelected(template: Template | null) {
  if (!template) return;

  selectedTemplate.value = template;
  applyTemplateMeta(template.meta || template.schema_data);

  templateApplied.value = true;
  if (appliedTimeout) clearTimeout(appliedTimeout);
  appliedTimeout = window.setTimeout(() => {
    templateApplied.value = false;
  }, 3000);
}

/**
 * Сброс темы к дефолтам выбранного шаблона.
 */
function resetThemeToTemplate() {
  if (!selectedTemplate.value) return;
  applyTemplateMeta(selectedTemplate.value.meta || selectedTemplate.value.schema_data);
  templateApplied.value = true;
  if (appliedTimeout) clearTimeout(appliedTimeout);
  appliedTimeout = window.setTimeout(() => {
    templateApplied.value = false;
  }, 3000);
}

function normalizeWebsite(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return '';
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}

function handleSubmit() {
  // Валидация обязательных полей
  if (!form.title.trim() || !form.full_name.trim()) {
    alert('Заполните обязательные поля: Название и Полное имя');
    return;
  }

  // Копируем форму и очищаем пустые строки → null
  const payload = { ...form };
  
  Object.keys(payload).forEach((key) => {
    const value = payload[key as keyof CardCreatePayload];
    if (value === '') {
      (payload as any)[key] = null;
    }
  });

  if (typeof payload.website === 'string' && payload.website) {
    payload.website = normalizeWebsite(payload.website);
  }

  // Гарантируем, что theme всегда присутствует
  if (!payload.theme) {
    payload.theme = { ...defaultTheme };
  }

  emit('submit', payload);
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <!-- ============================================================ -->
    <!-- ОСНОВНЫЕ ПОЛЯ -->
    <!-- ============================================================ -->
    <div>
      <h3 class="text-lg font-medium text-gray-900 mb-4">Основная информация</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">
            Название визитки <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.title"
            type="text"
            required
            placeholder="Например: Основная рабочая визитка"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">
            Полное имя <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.full_name"
            type="text"
            required
            placeholder="Иван Петров"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Должность</label>
          <input
            v-model="form.job_title"
            type="text"
            placeholder="Senior Software Engineer"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Отдел</label>
          <input
            v-model="form.department"
            type="text"
            placeholder="Platform Engineering"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Компания</label>
          <input
            v-model="form.company"
            type="text"
            placeholder="Example Corp"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Телефон</label>
          <input
            v-model="form.phone"
            type="tel"
            placeholder="+7 900 000-00-00"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700">Доп. телефон</label>
          <input
            v-model="form.phone_additional"
            type="tel"
            placeholder="+7 900 111-22-33"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Email</label>
          <input
            v-model="form.email"
            type="email"
            placeholder="ivan.petrov@example.com"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Сайт</label>
          <input
            v-model="form.website"
            type="url"
            placeholder="https://example.com"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-gray-700">Адрес</label>
          <input
            v-model="form.address"
            type="text"
            placeholder="Москва, ул. Пример, 1"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          />
        </div>
        
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-gray-700">Заметка</label>
          <textarea
            v-model="form.note"
            rows="3"
            placeholder="Дополнительная информация о вас или вашей деятельности"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          ></textarea>
        </div>
      </div>
    </div>

    <div class="border-t border-gray-200 pt-6">
      <h3 class="text-lg font-medium text-gray-900 mb-1">Мессенджеры</h3>
      <p class="text-sm text-gray-500 mb-4">
        Username, телефон или ссылка — на визитке появится кнопка перехода.
      </p>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Telegram</label>
          <input v-model="form.telegram" type="text" placeholder="@username" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">WhatsApp</label>
          <input v-model="form.whatsapp" type="text" placeholder="+7 900 000-00-00" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Viber</label>
          <input v-model="form.viber" type="text" placeholder="+7 900 000-00-00" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">WeChat</label>
          <input v-model="form.wechat" type="text" placeholder="WeChat ID" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Max</label>
          <input v-model="form.messenger_max" type="text" placeholder="username" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Discord</label>
          <input v-model="form.discord" type="text" placeholder="discord.gg/..." class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">VK</label>
          <input v-model="form.vk" type="text" placeholder="username" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- ИЗОБРАЖЕНИЯ -->
    <!-- ============================================================ -->
    <div class="border-t border-gray-200 pt-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">Изображения</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ImageUploader
          :model-value="form.avatar_file_id ?? null"
          @update:model-value="(val) => form.avatar_file_id = val"
          label="Аватар (фото)"
          aspect-ratio="square"
        />
        
        <ImageUploader
          :model-value="form.logo_file_id ?? null"
          @update:model-value="(val) => form.logo_file_id = val"
          label="Логотип компании"
          aspect-ratio="wide"
        />
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- ВЫБОР ШАБЛОНА -->
    <!-- ============================================================ -->
    <div class="border-t border-gray-200 pt-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">Шаблон визитки</h3>
      
      <!-- Уведомление о применении шаблона -->
      <transition
        enter-active-class="transition ease-out duration-300"
        enter-from-class="opacity-0 -translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-200"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-2"
      >
        <div
          v-if="templateApplied"
          class="mb-4 flex items-center gap-2 px-4 py-3 bg-teal-50 border border-teal-200 rounded-lg text-teal-800 text-sm"
        >
          <span class="text-lg">✨</span>
          <span>Настройки дизайна применены из шаблона. Вы можете скорректировать их ниже.</span>
        </div>
      </transition>
      
      <TemplateSelector
        :model-value="form.template_id ?? null"
        @update:model-value="(val) => form.template_id = val"
        @template-selected="handleTemplateSelected"
      />
    </div>

    <!-- ============================================================ -->
    <!-- НАСТРОЙКИ ТЕМЫ -->
    <!-- ============================================================ -->
    <div class="border-t border-gray-200 pt-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-medium text-gray-900">Дизайн и тема</h3>
        
        <!-- Кнопка сброса к настройкам шаблона -->
        <button
          v-if="form.template_id"
          type="button"
          @click="resetThemeToTemplate"
          class="text-sm text-primary hover:text-teal-800 font-medium"
        >
          ↺ Сбросить к настройкам шаблона
        </button>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Цветовая схема</label>
          <select
            v-model="form.theme.color_scheme"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          >
            <option value="light">Светлая</option>
            <option value="dark">Темная</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Шрифт</label>
          <select
            v-model="form.theme.font"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          >
            <option value="inter">Inter</option>
            <option value="roboto">Roboto</option>
            <option value="open_sans">Open Sans</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Акцентный цвет</label>
          <div class="mt-1 flex items-center gap-3">
            <input
              v-model="form.theme.accent_color"
              type="color"
              class="h-10 w-16 p-1 border border-gray-300 rounded-md cursor-pointer"
            />
            <span class="text-sm text-gray-500 font-mono">{{ form.theme.accent_color }}</span>
          </div>
        </div>
      </div>
      
      <div class="mt-4 flex flex-wrap items-center gap-6">
        <label class="flex items-center cursor-pointer">
          <input
            v-model="form.theme.show_photo"
            type="checkbox"
            class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          <span class="ml-2 text-sm text-gray-700">Показывать фото</span>
        </label>
        
        <label class="flex items-center cursor-pointer">
          <input
            v-model="form.theme.show_qr"
            type="checkbox"
            class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          <span class="ml-2 text-sm text-gray-700">Показывать QR-код</span>
        </label>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- КНОПКИ ДЕЙСТВИЙ -->
    <!-- ============================================================ -->
    <div class="flex justify-end gap-3 pt-6 border-t border-gray-200">
      <router-link to="/" class="btn-secondary">
        Отмена
      </router-link>
      
      <button
        type="submit"
        :disabled="isSubmitting"
        class="btn-primary min-w-[140px]"
      >
        <span v-if="isSubmitting" class="flex items-center justify-center gap-2">
          <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
              fill="none"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          Сохранение...
        </span>
        <span v-else>Сохранить</span>
      </button>
    </div>
  </form>
</template>