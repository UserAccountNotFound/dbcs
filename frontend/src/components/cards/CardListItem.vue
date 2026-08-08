<script setup lang="ts">
import { ref } from 'vue';
import type { Card } from '../../types/card';
import { cardApi } from '../../api/cards';
import { downloadBlob } from '../../utils/download';

const props = defineProps<{ card: Card }>();
const emit = defineEmits(['updated', 'deleted', 'edit', 'show-qr', 'show-stats']);

const isDeleting = ref(false);
const isToggling = ref(false);

async function toggleActive() {
  isToggling.value = true;
  try {
    await cardApi.updateCard(props.card.id, { is_active: !props.card.is_active });
    emit('updated');
  } catch (e) {
    alert('Ошибка при изменении статуса');
  } finally {
    isToggling.value = false;
  }
}

async function deleteCard() {
  if (!confirm(`Удалить визитку "${props.card.title}"?`)) return;
  
  isDeleting.value = true;
  try {
    await cardApi.deleteCard(props.card.id);
    emit('deleted');
  } catch (e) {
    alert('Ошибка при удалении');
  } finally {
    isDeleting.value = false;
  }
}

async function downloadVCard() {
  try {
    const blob = await cardApi.getVCardBlob(props.card.id);
    downloadBlob(blob, `${props.card.slug}.vcf`);
  } catch (e) {
    alert('Ошибка при скачивании vCard');
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow p-4 flex flex-col gap-3 border border-gray-100 hover:shadow-md transition-shadow">
    <div class="flex justify-between items-start">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ card.title }}</h3>
        <p class="text-gray-600">{{ card.full_name }}</p>
        <p v-if="card.job_title" class="text-sm text-gray-500">{{ card.job_title }}</p>
      </div>
      <span 
        :class="[
          'px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap',
          card.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        ]"
      >
        {{ card.is_active ? 'Активна' : 'Отключена' }}
      </span>
    </div>

    <div class="text-sm text-gray-500 truncate">
      <a :href="card.public_url" target="_blank" class="text-primary hover:underline">{{ card.public_url }}</a>
    </div>

    <div class="flex flex-wrap gap-2 mt-2">
      <button @click="$emit('edit', card.id)" class="btn-primary">Редактировать</button>
      <button @click="$emit('show-qr', card.id)" class="btn-secondary">QR</button>
      <button @click="$emit('show-stats', card.id)" class="btn-secondary">📊</button>
      <button @click="downloadVCard" class="btn-secondary">vCard</button>
      <button @click="toggleActive" :disabled="isToggling" class="btn-secondary">
        {{ card.is_active ? 'Отключить' : 'Включить' }}
      </button>
      <button @click="deleteCard" :disabled="isDeleting" class="btn-danger ml-auto">Удалить</button>
    </div>
  </div>
</template>