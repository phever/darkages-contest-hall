import axios from 'axios';

// Relative base: requests go to the same origin and are proxied to Django
// (Vite proxy in dev, Vercel rewrite in prod). This keeps the httpOnly auth
// cookies first-party, so JavaScript never touches the tokens.
const api = axios.create({
  baseURL: '/api/',
  withCredentials: true,
});

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : null;
}

// Attach Django's CSRF token on unsafe methods (cookie auth needs CSRF defense).
api.interceptors.request.use((config) => {
  const method = (config.method || 'get').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const token = getCookie('csrftoken');
    if (token) config.headers['X-CSRFToken'] = token;
  }
  return config;
});

// Transparently refresh an expired access token once, then retry.
let refreshPromise = null;
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    const url = config?.url || '';
    const isAuthRoute = url.includes('auth/login') || url.includes('auth/refresh');

    if (response?.status === 401 && config && !config._retry && !isAuthRoute) {
      config._retry = true;
      try {
        refreshPromise = refreshPromise || api.post('auth/refresh/');
        await refreshPromise;
        refreshPromise = null;
        return api(config);
      } catch (refreshErr) {
        refreshPromise = null;
        return Promise.reject(refreshErr);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
