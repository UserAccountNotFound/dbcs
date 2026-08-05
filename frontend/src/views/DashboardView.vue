<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { cardApi } from '../api/cards';
import type { Card } from '../types/card';
import CardListItem from '../components/cards/CardListItem.vue';
import QrModal from '../components/cards/QrModal.vue';

const router = useRouter();
const authStore = useAuthStore();

const cards = ref<Card[]>([]);
const isLoading = ref(true);
const error = ref('');
const qrCardId = ref<string | null>(null);

async function loadCards() {
  isLoading.value = true;
  error.value = '';
  try {
    const response = await cardApi.getCards();
    cards.value = response.items;
  } catch (e: any) {
    error.value = 'Не удалось загрузить визитки';
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadCards);

function handleEdit(cardId: string) {
  router.push(`/cards/${cardId}`);
}

function handleShowQr(cardId: string) {
  qrCardId.value = cardId;
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">Мои визитки</h1>
        <div class="flex items-center gap-4">
          <span class="text-gray-600">{{ authStore.user?.full_name }}</span>
          <button @click="authStore.logout()" class="text-sm text-red-600 hover:text-red-800 font-medium">
            Выйти
          </button>
        </div>
      </div>
    </header>
    
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-xl font-semibold text-gray-800">Список визиток</h2>
        <router-link to="/cards/new" class="btn-primary">+ Создать визитку</router-link>
      </div>

      <div v-if="isLoading" class="flex justify-center items-center h-64">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="error" class="text-center text-red-600 py-12">{{ error }}</div>

      <div v-else-if="cards.length === 0" class="text-center py-12 bg-white rounded-lg shadow">
        <p class="text-gray-500 mb-4">У вас пока нет визиток</p>
        <router-link to="/cards/new" class="btn-primary inline-block">Создать первую визитку</router-link>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <CardListItem 
          v-for="card in cards" 
          :key="card.id"
          :card="card"
          @edit="handleEdit"
          @show-qr="handleShowQr"
          @updated="loadCards"
          @deleted="loadCards"
        />
      </div>
    </main>

    <QrModal :card-id="qrCardId" @close="qrCardId = null" />
  </div>
</template>