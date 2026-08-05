<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { adminApi } from '../../api/admin';
import type { AdminUser, AdminUserCreate, AdminUserUpdate } from '../../types/admin';
import UserFormModal from '../../components/admin/UserFormModal.vue';

const users = ref<AdminUser[]>([]);
const total = ref(0);
const limit = ref(20);
const offset = ref(0);
const search = ref('');
const isLoading = ref(true);
const searchTimeout = ref<number>();

// Состояние модального окна
const isModalOpen = ref(false);
const editingUser = ref<AdminUser | null>(null);

async function loadUsers() {
  isLoading.value = true;
  try {
    const response = await adminApi.getUsers(limit.value, offset.value, search.value);
    users.value = response.items;
    total.value = response.total;
  } catch (e) {
    console.error('Failed to load users', e);
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadUsers);

watch(search, () => {
  clearTimeout(searchTimeout.value);
  searchTimeout.value = window.setTimeout(() => {
    offset.value = 0;
    loadUsers();
  }, 500);
});

function openCreateModal() {
  editingUser.value = null;
  isModalOpen.value = true;
}

function openEditModal(user: AdminUser) {
  editingUser.value = user;
  isModalOpen.value = true;
}

async function handleFormSubmit(payload: AdminUserCreate | AdminUserUpdate) {
  try {
    if (editingUser.value) {
      await adminApi.updateUser(editingUser.value.id, payload as AdminUserUpdate);
    } else {
      await adminApi.createUser(payload as AdminUserCreate);
    }
    isModalOpen.value = false;
    await loadUsers();
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Ошибка при сохранении');
  }
}

async function deleteUser(user: AdminUser) {
  if (!confirm(`Удалить пользователя "${user.email}"? Это действие нельзя отменить.`)) return;
  
  try {
    await adminApi.deleteUser(user.id);
    await loadUsers();
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Ошибка при удалении');
  }
}

async function toggleActive(user: AdminUser) {
  try {
    await adminApi.updateUser(user.id, { is_active: !user.is_active });
    user.is_active = !user.is_active;
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Ошибка при обновлении');
  }
}

async function changeRole(user: AdminUser, role: string) {
  try {
    await adminApi.updateUser(user.id, { role: role as any });
    user.role = role as any;
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Ошибка при смене роли');
  }
}

const totalPages = computed(() => Math.ceil(total.value / limit.value));
const currentPage = computed(() => Math.floor(offset.value / limit.value) + 1);

function nextPage() {
  if (currentPage.value < totalPages.value) {
    offset.value += limit.value;
    loadUsers();
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    offset.value -= limit.value;
    loadUsers();
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900">Пользователи</h2>
      <div class="flex gap-3">
        <input 
          v-model="search"
          type="text"
          placeholder="Поиск по email или имени..."
          class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary w-64"
        />
        <button @click="openCreateModal" class="btn-primary">
          + Создать
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Пользователь</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Роль</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Визиток</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-if="isLoading">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500">Загрузка...</td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500">Пользователи не найдены</td>
          </tr>
          <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
            <td class="px-6 py-4">
              <div class="font-medium text-gray-900">{{ user.full_name }}</div>
              <div class="text-sm text-gray-500">{{ user.email }}</div>
            </td>
            <td class="px-6 py-4">
              <select 
                :value="user.role"
                @change="changeRole(user, ($event.target as HTMLSelectElement).value)"
                class="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="USER">USER</option>
                <option value="ADMIN">ADMIN</option>
                <option value="SUPERADMIN">SUPERADMIN</option>
              </select>
            </td>
            <td class="px-6 py-4 text-gray-600">{{ user.cards_count }}</td>
            <td class="px-6 py-4">
              <span 
                :class="[
                  'px-2 py-1 rounded-full text-xs font-medium',
                  user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                ]"
              >
                {{ user.is_active ? 'Активен' : 'Отключен' }}
              </span>
            </td>
            <td class="px-6 py-4">
              <div class="flex gap-2">
                <button 
                  @click="openEditModal(user)"
                  class="text-sm text-blue-600 hover:bg-blue-50 px-2 py-1 rounded transition-colors"
                  title="Редактировать"
                >
                  ✏️
                </button>
                <button 
                  @click="toggleActive(user)"
                  :class="[
                    'text-sm px-2 py-1 rounded transition-colors',
                    user.is_active ? 'text-orange-600 hover:bg-orange-50' : 'text-green-600 hover:bg-green-50'
                  ]"
                  :title="user.is_active ? 'Деактивировать' : 'Активировать'"
                >
                  {{ user.is_active ? '🔒' : '🔓' }}
                </button>
                <button 
                  @click="deleteUser(user)"
                  class="text-sm text-red-600 hover:bg-red-50 px-2 py-1 rounded transition-colors"
                  title="Удалить"
                >
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Пагинация -->
    <div class="flex justify-between items-center mt-4">
      <p class="text-sm text-gray-500">
        Всего: {{ total }} | Страница {{ currentPage }} из {{ totalPages }}
      </p>
      <div class="flex gap-2">
        <button @click="prevPage" :disabled="currentPage === 1" class="btn-secondary disabled:opacity-50">← Назад</button>
        <button @click="nextPage" :disabled="currentPage === totalPages" class="btn-secondary disabled:opacity-50">Вперед →</button>
      </div>
    </div>

    <!-- Модальное окно -->
    <UserFormModal 
      :user="editingUser"
      :is-open="isModalOpen"
      @close="isModalOpen = false"
      @submit="handleFormSubmit"
    />
  </div>
</template>