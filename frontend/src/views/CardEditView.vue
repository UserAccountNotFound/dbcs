<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { cardApi } from '../api/cards';
import type { Card, CardCreatePayload, CardUpdatePayload } from '../types/card';
import CardForm from '../components/cards/CardForm.vue';
import { getAxiosErrorMessage } from '../utils/apiError';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const isNew = computed(() => route.name === 'card-new');
const cardId = computed(() => isNew.value ? null : route.params.id as string);

const card = ref<Card | undefined>();
const isSubmitting = ref(false);
const isLoading = ref(!isNew.value);
const error = ref('');
const notFound = ref(false);

onMounted(async () => {
  if (!isNew.value && cardId.value) {
    try {
      card.value = await cardApi.getCard(cardId.value);
    } catch (e) {
      error.value = t('errors.cardNotFound');
      notFound.value = true;
      setTimeout(() => router.push('/'), 2000);
    } finally {
      isLoading.value = false;
    }
  }
});

async function handleSubmit(payload: CardCreatePayload | CardUpdatePayload) {
  isSubmitting.value = true;
  error.value = '';
  try {
    if (isNew.value) {
      await cardApi.createCard(payload as CardCreatePayload);
    } else if (cardId.value) {
      await cardApi.updateCard(cardId.value, payload as CardUpdatePayload);
    }
    router.push('/');
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.saveCard'));
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-6">
        {{ isNew ? t('cards.createTitle') : t('cards.editTitle') }}
      </h1>

      <div v-if="isLoading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="notFound" class="bg-white rounded-lg shadow p-6">
        <p class="text-red-600">{{ error }}</p>
      </div>

      <div v-else class="bg-white rounded-lg shadow p-6">
        <p v-if="error" class="text-red-600 mb-4">{{ error }}</p>
        <CardForm 
          :card="card" 
          :is-submitting="isSubmitting"
          @submit="handleSubmit"
        />
      </div>
    </div>
  </div>
</template>
