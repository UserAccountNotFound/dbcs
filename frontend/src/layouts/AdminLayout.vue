<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../stores/auth';
import { systemApi } from '../api/system';
import LanguageSwitcher from '../components/common/LanguageSwitcher.vue';

const { t } = useI18n();
const authStore = useAuthStore();
const isSuperAdmin = computed(() => authStore.user?.role === 'SUPERADMIN');

const frontendVersion = import.meta.env.VITE_APP_VERSION;
const apiVersion = ref<string | null>(null);

async function loadApiVersion() {
  try {
    const health = await systemApi.getHealth();
    apiVersion.value = health.version;
  } catch {
    apiVersion.value = null;
  }
}

onMounted(() => {
  void loadApiVersion();
});

const menuItems = computed(() => {
  const items = [
    { name: 'admin-dashboard', labelKey: 'admin.dashboard', icon: '📊' },
    { name: 'admin-users', labelKey: 'admin.users', icon: '👥' },
    { name: 'admin-cards', labelKey: 'admin.cards', icon: '💳' },
    { name: 'admin-templates', labelKey: 'admin.templates', icon: '🎨' },
    { name: 'admin-audit', labelKey: 'admin.audit', icon: '📋' },
  ];
  if (isSuperAdmin.value) {
    items.push(
      { name: 'admin-backup', labelKey: 'admin.backup', icon: '💾' },
      { name: 'admin-settings', labelKey: 'admin.settings', icon: '⚙️' },
    );
  }
  return items;
});
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex">
    <aside class="w-64 bg-gray-900 text-white flex flex-col h-screen sticky top-0 shrink-0">
      <div class="p-6 border-b border-gray-800 shrink-0">
        <h1 class="text-xl font-bold mb-2">{{ t('admin.title') }}</h1>
        <p class="text-[11px] text-gray-500 font-mono tabular-nums">
          API
          <span class="text-gray-300">{{ apiVersion ?? '…' }}</span>
          <span class="mx-1" aria-hidden="true">·</span>
          Frontend
          <span class="text-gray-300">{{ frontendVersion }}</span>
        </p>
        <div class="mt-2">
          <LanguageSwitcher compact />
        </div>
      </div>

      <nav class="flex-1 min-h-0 overflow-y-auto p-4 space-y-1">
        <router-link 
          v-for="item in menuItems" 
          :key="item.name"
          :to="{ name: item.name }"
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="$route.name === item.name ? 'bg-primary text-white' : 'text-gray-300 hover:bg-gray-800'"
        >
          <span>{{ item.icon }}</span>
          <span>{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>

      <div class="p-4 border-t border-gray-800 shrink-0 mt-auto">
        <router-link to="/" class="block px-4 py-2 text-gray-300 hover:text-white transition-colors">
          {{ t('admin.backToDashboard') }}
        </router-link>
        <button @click="authStore.logout()" class="w-full mt-2 px-4 py-2 text-left text-red-400 hover:text-red-300 transition-colors">
          {{ t('auth.logout') }}
        </button>
      </div>
    </aside>

    <main class="flex-1 min-w-0 p-8">
      <router-view />
    </main>
  </div>
</template>
