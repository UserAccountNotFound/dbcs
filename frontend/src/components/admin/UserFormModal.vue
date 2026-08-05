<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { AdminUser, AdminUserCreate, AdminUserUpdate } from '../../types/admin';

const props = defineProps<{
  user: AdminUser | null;  // null для создания нового
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', payload: AdminUserCreate | AdminUserUpdate): void;
}>();

const isEdit = computed(() => props.user !== null);

const form = ref({
  email: '',
  full_name: '',
  password: '',
  role: 'USER' as 'USER' | 'ADMIN' | 'SUPERADMIN',
});

const isSubmitting = ref(false);
const error = ref('');

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    error.value = '';
    if (props.user) {
      form.value = {
        email: props.user.email,
        full_name: props.user.full_name,
        password: '',  // пароль не заполняем при редактировании
        role: props.user.role,
      };
    } else {
      form.value = {
        email: '',
        full_name: '',
        password: '',
        role: 'USER',
      };
    }
  }
});

function handleSubmit() {
  error.value = '';
  
  if (!form.value.email || !form.value.full_name) {
    error.value = 'Заполните email и имя';
    return;
  }
  
  if (!isEdit.value && form.value.password.length < 12) {
    error.value = 'Пароль должен быть не менее 12 символов';
    return;
  }

  let payload: AdminUserCreate | AdminUserUpdate;
  
  if (isEdit.value) {
    // Формируем объект обновления без приведения типов
    const updatePayload: AdminUserUpdate = {
      email: form.value.email,
      full_name: form.value.full_name,
      role: form.value.role,
    };
    
    // Добавляем пароль только если он был введен
    if (form.value.password) {
      updatePayload.password = form.value.password;
    }
    
    payload = updatePayload;
  } else {
    // Для создания копируем все поля формы
    payload = { ...form.value };
  }

  emit('submit', payload);
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
      <h3 class="text-xl font-bold text-gray-900 mb-6">
        {{ isEdit ? 'Редактировать пользователя' : 'Создать пользователя' }}
      </h3>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email *</label>
          <input 
            v-model="form.email" 
            type="email" 
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Полное имя *</label>
          <input 
            v-model="form.full_name" 
            type="text" 
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Пароль {{ isEdit ? '(оставьте пустым, чтобы не менять)' : '*' }}
          </label>
          <input 
            v-model="form.password" 
            type="password" 
            :required="!isEdit"
            :minlength="isEdit ? undefined : 12"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Минимум 12 символов"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Роль</label>
          <select 
            v-model="form.role"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="USER">Пользователь</option>
            <option value="ADMIN">Администратор</option>
            <option value="SUPERADMIN">Суперадминистратор</option>
          </select>
        </div>

        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>

        <div class="flex gap-3 pt-4">
          <button type="button" @click="$emit('close')" class="btn-secondary flex-1">
            Отмена
          </button>
          <button type="submit" :disabled="isSubmitting" class="btn-primary flex-1">
            {{ isSubmitting ? 'Сохранение...' : (isEdit ? 'Сохранить' : 'Создать') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>