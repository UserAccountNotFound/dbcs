<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../stores/auth';
import { cardApi } from '../api/cards';
import type { Card } from '../types/card';
import CardListItem from '../components/cards/CardListItem.vue';
import QrModal from '../components/cards/QrModal.vue';
import StatsModal from '../components/cards/StatsModal.vue';
import CardsTransferModal from '../components/cards/CardsTransferModal.vue';
import LanguageSwitcher from '../components/common/LanguageSwitcher.vue';

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();

const cards = ref<Card[]>([]);
const isLoading = ref(true);
const error = ref('');

const qrCardId = ref<string | null>(null);
const statsCardId = ref<string | null>(null);
const statsCardTitle = ref<string>('');
const transferOpen = ref(false);

async function loadCards() {
  isLoading.value = true;
  error.value = '';
  try {
    const response = await cardApi.getCards();
    cards.value = response.items;
  } catch (e: any) {
    error.value = t('errors.loadCards');
    console.error('Load cards error:', e);
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

function handleShowStats(cardId: string) {
  const card = cards.value.find(c => c.id === cardId);
  statsCardId.value = cardId;
  statsCardTitle.value = card?.title || '';
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm border-b border-gray-100">
      <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-lg shadow-md">
              D
            </div>
            <div>
              <h1 class="text-xl font-bold text-gray-900 leading-tight">DBCS</h1>
              <p class="text-xs text-gray-500">{{ t('dashboard.tagline') }}</p>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <LanguageSwitcher compact />
            <span class="text-gray-600 hidden sm:block text-sm font-medium">
              {{ authStore.user?.full_name }}
            </span>
            
            <router-link 
              v-if="authStore.isAdmin" 
              to="/admin" 
              class="text-sm text-primary hover:text-teal-800 font-medium px-3 py-1.5 rounded-lg hover:bg-teal-50 transition-colors"
            >
              {{ t('dashboard.adminPanel') }}
            </router-link>
            
            <button 
              @click="authStore.logout()" 
              class="text-sm text-red-600 hover:text-red-800 font-medium px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors"
            >
              {{ t('auth.logout') }}
            </button>
          </div>
        </div>
      </div>
    </header>
    
    <main class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center mb-8 gap-4 flex-wrap">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">{{ t('dashboard.myCards') }}</h2>
          <p class="text-gray-500 mt-1">{{ t('dashboard.subtitle') }}</p>
        </div>
        <div class="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            class="btn-secondary"
            @click="transferOpen = true"
          >
            {{ t('dashboard.exportImport') }}
          </button>
          <router-link to="/cards/new" class="btn-primary shadow-lg shadow-teal-700/20">
            {{ t('dashboard.createCard') }}
          </router-link>
        </div>
      </div>

      <div v-if="isLoading" class="flex justify-center items-center h-64">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="error" class="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-100">
        <div class="text-5xl mb-4">⚠️</div>
        <p class="text-red-600 mb-6">{{ error }}</p>
        <button @click="loadCards" class="btn-primary">
          {{ t('common.retry') }}
        </button>
      </div>

      <div v-else-if="cards.length === 0" class="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-100">
        <div class="text-6xl mb-6">💳</div>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ t('dashboard.emptyTitle') }}</h3>
        <p class="text-gray-500 mb-8 max-w-md mx-auto">
          {{ t('dashboard.emptyText') }}
        </p>
        <router-link to="/cards/new" class="btn-primary inline-block shadow-lg shadow-teal-700/20">
          {{ t('dashboard.createFirst') }}
        </router-link>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <CardListItem 
          v-for="card in cards" 
          :key="card.id"
          :card="card"
          @edit="handleEdit"
          @show-qr="handleShowQr"
          @show-stats="handleShowStats"
          @updated="loadCards"
          @deleted="loadCards"
        />
      </div>
    </main>

    <QrModal 
      :card-id="qrCardId" 
      @close="qrCardId = null" 
    />
    
    <StatsModal 
      :card-id="statsCardId" 
      :card-title="statsCardTitle" 
      @close="statsCardId = null" 
    />

    <CardsTransferModal
      :open="transferOpen"
      @close="transferOpen = false"
      @imported="loadCards"
    />
  </div>
</template>
