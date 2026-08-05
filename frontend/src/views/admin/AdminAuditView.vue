<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { adminApi } from '../../api/admin';
import type { AuditLog } from '../../types/admin';

const logs = ref<AuditLog[]>([]);
const total = ref(0);
const limit = ref(50);
const offset = ref(0);
const isLoading = ref(true);

async function loadLogs() {
  isLoading.value = true;
  try {
    const response = await adminApi.getAuditLogs(limit.value, offset.value);
    logs.value = response.items;
    total.value = response.total;
  } catch (e) {
    console.error('Failed to load audit logs', e);
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadLogs);

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('ru-RU');
}

function getActionBadgeClass(action: string): string {
  if (action.includes('delete') || action.includes('deactivate')) return 'bg-red-100 text-red-800';
  if (action.includes('create')) return 'bg-green-100 text-green-800';
  if (action.includes('login') || action.includes('auth')) return 'bg-blue-100 text-blue-800';
  if (action.includes('admin')) return 'bg-purple-100 text-purple-800';
  return 'bg-gray-100 text-gray-800';
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 mb-6">Журнал аудита</h2>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Время</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Пользователь</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действие</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Объект</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-if="isLoading">
            <td colspan="4" class="px-6 py-12 text-center text-gray-500">Загрузка...</td>
          </tr>
          <tr v-else-if="logs.length === 0">
            <td colspan="4" class="px-6 py-12 text-center text-gray-500">Записи не найдены</td>
          </tr>
          <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">{{ formatDate(log.created_at) }}</td>
            <td class="px-6 py-4 text-sm text-gray-900">{{ log.actor_email || 'Система' }}</td>
            <td class="px-6 py-4">
              <span :class="['px-2 py-1 rounded-full text-xs font-medium', getActionBadgeClass(log.action)]">
                {{ log.action }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">
              <span v-if="log.entity_type">{{ log.entity_type }}: {{ log.entity_id }}</span>
              <span v-else>—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex justify-between items-center mt-4">
      <p class="text-sm text-gray-500">Всего записей: {{ total }}</p>
      <div class="flex gap-2">
        <button @click="offset -= limit; loadLogs()" :disabled="offset === 0" class="btn-secondary disabled:opacity-50">← Назад</button>
        <button @click="offset += limit; loadLogs()" :disabled="offset + limit >= total" class="btn-secondary disabled:opacity-50">Вперед →</button>
      </div>
    </div>
  </div>
</template>