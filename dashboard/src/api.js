import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export const fetchSignals = () => api.get('/signals').then(res => res.data);
export const fetchRisk = () => api.get('/risk').then(res => res.data);
export const fetchTrades = () => api.get('/trades').then(res => res.data);
export const fetchPositions = () => api.get('/positions').then(res => res.data);
export const fetchPerformance = () => api.get('/performance').then(res => res.data);
