import axios from "axios";

export const api = axios.create({
    // Use Vercel environment variable in production (VITE_API_BASE_URL). When not set, default to same origin under /api.
    baseURL: import.meta.env.VITE_API_BASE_URL || `${window.location.origin}/api`,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem("itas_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});
