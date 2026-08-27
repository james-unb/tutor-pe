import axios from "axios"

const api = axios.create({
    baseURL: import.meta.env.VITE_BACKEND_URL
})

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('@TUTOR-PE-AUTH');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('@TUTOR-PE-AUTH');
            window.location.href = '/';
        }
        return Promise.reject(error);
    }
);

export default api