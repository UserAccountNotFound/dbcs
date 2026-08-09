import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true, // Обязательно! Позволяет отправлять HttpOnly cookies на бэкенд
  headers: {
    'Content-Type': 'application/json',
  },
});

// Флаг, чтобы не делать несколько одновременных запросов на refresh
let isRefreshing = false;
let failedQueue: Array<{ resolve: (value: unknown) => void; reject: (reason?: unknown) => void }> = [];

const AUTH_NO_REFRESH_PATHS = [
  '/auth/login',
  '/auth/logout',
  '/auth/register',
  '/auth/refresh',
];

function shouldSkipRefresh(url: string | undefined): boolean {
  if (!url) return true;
  return AUTH_NO_REFRESH_PATHS.some((path) => url.includes(path));
}

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

async function syncAccessToken(token: string) {
  localStorage.setItem('access_token', token);
  try {
    const { useAuthStore } = await import('../stores/auth');
    useAuthStore().setAccessToken(token);
  } catch {
    // store может быть ещё не инициализирован
  }
}

async function forceLogoutFromInterceptor() {
  localStorage.removeItem('access_token');
  try {
    const { useAuthStore } = await import('../stores/auth');
    await useAuthStore().forceLogout({ callApi: false });
  } catch {
    window.location.href = '/login';
  }
}

// Interceptor для добавления Access Token в заголовки
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Браузер сам выставит multipart boundary для FormData
    if (config.data instanceof FormData && config.headers) {
      delete config.headers['Content-Type'];
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor для обработки 401 и Silent Refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !shouldSkipRefresh(originalRequest.url)
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );

        const newAccessToken = data.access_token;
        await syncAccessToken(newAccessToken);

        processQueue(null, newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        await forceLogoutFromInterceptor();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
