import axios from 'axios';
import { World, Character, Discussion, CreateWorldRequest, CreateCharacterRequest, CreateDiscussionRequest } from '../types';

const API_BASE_URL = 'http://localhost:8003/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const worldsApi = {
  getAll: (): Promise<World[]> => api.get('/worlds').then(res => res.data),
  getById: (id: number): Promise<World> => api.get(`/worlds/${id}`).then(res => res.data),
  create: (world: CreateWorldRequest): Promise<World> => api.post('/worlds', world).then(res => res.data),
  update: (id: number, world: Partial<World>): Promise<World> => api.put(`/worlds/${id}`, world).then(res => res.data),
  delete: (id: number): Promise<void> => api.delete(`/worlds/${id}`).then(res => res.data),
};

export const charactersApi = {
  getAll: (worldId?: number): Promise<Character[]> => {
    const params = worldId ? { world_id: worldId } : {};
    return api.get('/characters', { params }).then(res => res.data);
  },
  getById: (id: number): Promise<Character> => api.get(`/characters/${id}`).then(res => res.data),
  create: (character: CreateCharacterRequest): Promise<Character> => api.post('/characters', character).then(res => res.data),
  update: (id: number, character: Partial<Character>): Promise<Character> => api.put(`/characters/${id}`, character).then(res => res.data),
  delete: (id: number): Promise<void> => api.delete(`/characters/${id}`).then(res => res.data),
};

export const discussionsApi = {
  getAll: (worldId?: number): Promise<Discussion[]> => {
    const params = worldId ? { world_id: worldId } : {};
    return api.get('/discussions', { params }).then(res => res.data);
  },
  getById: (id: number): Promise<Discussion> => api.get(`/discussions/${id}`).then(res => res.data),
  create: (discussion: CreateDiscussionRequest): Promise<Discussion> => api.post('/discussions', discussion).then(res => res.data),
  start: (id: number): Promise<{ message: string; discussion_id: number }> => api.post(`/discussions/${id}/start`).then(res => res.data),
  update: (id: number, discussion: Partial<Discussion>): Promise<Discussion> => api.put(`/discussions/${id}`, discussion).then(res => res.data),
};