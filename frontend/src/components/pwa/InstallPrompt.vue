<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

const { t } = useI18n();

const deferredPrompt = ref<BeforeInstallPromptEvent | null>(null);
const showInstallButton = ref(false);

function handleBeforeInstallPrompt(e: Event) {
  e.preventDefault();
  deferredPrompt.value = e as BeforeInstallPromptEvent;
  showInstallButton.value = true;
}

async function installApp() {
  if (!deferredPrompt.value) return;
  
  deferredPrompt.value.prompt();
  const { outcome } = await deferredPrompt.value.userChoice;
  
  if (outcome === 'accepted') {
    showInstallButton.value = false;
    deferredPrompt.value = null;
  }
}

onMounted(() => {
  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
});

onUnmounted(() => {
  window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
});
</script>

<template>
  <button 
    v-if="showInstallButton" 
    @click="installApp"
    class="fixed bottom-6 right-6 z-50 px-5 py-3 bg-primary text-white rounded-full shadow-xl hover:bg-teal-800 transition-all hover:scale-105 active:scale-95 flex items-center gap-2 font-medium"
  >
    <span>📲</span>
    {{ t('pwa.install') }}
  </button>
</template>
