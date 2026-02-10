
import axios from 'axios';

const api = axios.create({
    baseURL: '/api', // Proxied by Vite to localhost:8500
    headers: {
        'Content-Type': 'application/json',
    },
});

export const getSystemHealth = async () => {
    try {
        const response = await api.get('/admin/system/health');
        return response.data;
    } catch (error) {
        console.error("Health Check Failed", error);
        return null;
    }
};

export default api;
