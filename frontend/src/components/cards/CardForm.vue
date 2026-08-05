<script setup lang="ts">
import { reactive, watch } from 'vue';
import type { Card, CardCreatePayload, CardUpdatePayload, CardTheme } from '../../types/card';

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
  show_qr: true
};

const form = reactive<CardCreatePayload>({
  title: '',
  full_name: '',
  job_title: '',
  department: '',
  company: '',
  phone: '',
  email: '',
  website: '',
  address: '',
  note: '',
  template_id: null,
  theme: { ...defaultTheme }
});

// Заполнение формы при редактировании
watch(() => props.card, (newCard) => {
  if (newCard) {
    form.title = newCard.title;
    form.full_name = newCard.full_name;
    form.job_title = newCard.job_title || '';
    form.department = newCard.department || '';
    form.company = newCard.company || '';
    form.phone = newCard.phone || '';
    form.email = newCard.email || '';
    form.website = newCard.website || '';
    form.address = newCard.address || '';
    form.note = newCard.note || '';
    form.template_id = newCard.template_id;
    form.theme = { ...newCard.theme };
  }
}, { immediate: true });

function handleSubmit() {
  if (!form.title.trim() || !form.full_name.trim()) {
    alert('Заполните обязательные поля: Название и Полное имя');
    return;
  }

  // Копируем и очищаем пустые строки
  const payload = { ...form };
  Object.keys(payload).forEach(key => {
    const value = payload[key as keyof CardCreatePayload];
    if (value === '') {
      (payload as any)[key] = null;
    }
  });

  emit('submit', payload);
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">Название визитки *</label>
        <input v-model="form.title" type="text" required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Полное имя *</label>
        <input v-model="form.full_name" type="text" required class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Должность</label>
        <input v-model="form.job_title" type="text" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Отдел</label>
        <input v-model="form.department" type="text" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Компания</label>
        <input v-model="form.company" type="text" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Телефон</label>
        <input v-model="form.phone" type="tel" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Email</label>
        <input v-model="form.email" type="email" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Сайт</label>
        <input v-model="form.website" type="url" placeholder="https://example.com" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700">Адрес</label>
        <input v-model="form.address" type="text" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary" />
      </div>
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700">Заметка</label>
        <textarea v-model="form.note" rows="3" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"></textarea>
      </div>
    </div>

    <!-- Настройки дизайна -->
    <div class="border-t pt-4">
      <h3 class="text-lg font-medium text-gray-900 mb-3">Дизайн визитки</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Цветовая схема</label>
          <select v-model="form.theme.color_scheme" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary">
            <option value="light">Светлая</option>
            <option value="dark">Темная</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Раскладка</label>
          <select v-model="form.theme.layout" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary">
            <option value="classic">Классическая</option>
            <option value="modern">Современная</option>
            <option value="compact">Компактная</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Акцентный цвет</label>
          <input v-model="form.theme.accent_color" type="color" class="mt-1 block w-full h-10 p-1 border border-gray-300 rounded-md cursor-pointer" />
        </div>
      </div>
      <div class="mt-4 flex items-center gap-6">
        <label class="flex items-center">
          <input v-model="form.theme.show_photo" type="checkbox" class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded" />
          <span class="ml-2 text-sm text-gray-700">Показывать фото</span>
        </label>
        <label class="flex items-center">
          <input v-model="form.theme.show_qr" type="checkbox" class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded" />
          <span class="ml-2 text-sm text-gray-700">Показывать QR на визитке</span>
        </label>
      </div>
    </div>

    <div class="flex justify-end gap-3 pt-4 border-t">
      <router-link to="/" class="btn-secondary">Отмена</router-link>
      <button type="submit" :disabled="isSubmitting" class="btn-primary">
        {{ isSubmitting ? 'Сохранение...' : 'Сохранить' }}
      </button>
    </div>
  </form>
</template>