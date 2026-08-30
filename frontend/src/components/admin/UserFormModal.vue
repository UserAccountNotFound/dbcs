<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { AdminUser, AdminUserCreate, AdminUserUpdate } from '../../types/admin';
import { useAuthStore } from '../../stores/auth';

const { t } = useI18n();
const auth = useAuthStore();
const isSuperAdmin = computed(() => auth.user?.role === 'SUPERADMIN');

const props = defineProps<{
  user: AdminUser | null;
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', payload: AdminUserCreate | AdminUserUpdate): void;
}>();

const isEdit = computed(() => props.user !== null);
const canAssignPrivilegedRoles = isSuperAdmin;

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
        password: '',
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
    error.value = t('admin.fillEmailName');
    return;
  }

  if (!isEdit.value && form.value.password.length < 12) {
    error.value = t('admin.passwordTooShort');
    return;
  }

  if (isEdit.value && form.value.password && form.value.password.length < 12) {
    error.value = t('admin.passwordTooShort');
    return;
  }

  if (
    !canAssignPrivilegedRoles.value
    && (form.value.role === 'ADMIN' || form.value.role === 'SUPERADMIN')
  ) {
    error.value = t('errors.roleChangeFailed');
    return;
  }

  isSubmitting.value = true;

  let payload: AdminUserCreate | AdminUserUpdate;

  if (isEdit.value) {
    const updatePayload: AdminUserUpdate = {
      email: form.value.email,
      full_name: form.value.full_name,
      role: form.value.role,
    };

    if (form.value.password) {
      updatePayload.password = form.value.password;
    }

    payload = updatePayload;
  } else {
    payload = { ...form.value };
  }

  emit('submit', payload);
  isSubmitting.value = false;
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
      <h3 class="text-xl font-bold text-gray-900 mb-6">
        {{ isEdit ? t('admin.editUser') : t('admin.createUserTitle') }}
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
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('admin.fullName') }}</label>
          <input
            v-model="form.full_name"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            {{ isEdit ? t('admin.passwordOptional') : t('admin.passwordRequired') }}
          </label>
          <input
            v-model="form.password"
            type="password"
            :required="!isEdit"
            :minlength="isEdit ? undefined : 12"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            :placeholder="t('admin.passwordMin')"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('admin.role') }}</label>
          <select
            v-model="form.role"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            :disabled="!canAssignPrivilegedRoles && (form.role === 'ADMIN' || form.role === 'SUPERADMIN')"
          >
            <option value="USER">{{ t('admin.roleUser') }}</option>
            <option v-if="canAssignPrivilegedRoles || form.role === 'ADMIN'" value="ADMIN">
              {{ t('admin.roleAdmin') }}
            </option>
            <option v-if="canAssignPrivilegedRoles || form.role === 'SUPERADMIN'" value="SUPERADMIN">
              {{ t('admin.roleSuperAdmin') }}
            </option>
          </select>
        </div>

        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>

        <div class="flex gap-3 pt-4">
          <button type="button" @click="$emit('close')" class="btn-secondary flex-1">
            {{ t('common.cancel') }}
          </button>
          <button type="submit" :disabled="isSubmitting" class="btn-primary flex-1">
            {{ isSubmitting ? t('common.savingDots') : (isEdit ? t('common.save') : t('common.create')) }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
