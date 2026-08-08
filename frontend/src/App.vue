<script setup lang="ts">
import { RouterView } from 'vue-router'
import InstallPrompt from './components/pwa/InstallPrompt.vue'
</script>

<template>
  <RouterView />
  <InstallPrompt />
</template>