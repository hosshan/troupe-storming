import axios from "axios";
import {
  World,
  Character,
  Discussion,
  CreateWorldRequest,
  CreateCharacterRequest,
  CreateDiscussionRequest,
} from "../types";

const API_BASE_URL = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const worldsApi = {
  getAll: (): Promise<World[]> => api.get("/worlds").then((res) => res.data),
  getById: (id: number): Promise<World> =>
    api.get(`/worlds/${id}`).then((res) => res.data),
  create: (world: CreateWorldRequest): Promise<World> =>
    api.post("/worlds", world).then((res) => res.data),
  update: (id: number, world: Partial<World>): Promise<World> =>
    api.put(`/worlds/${id}`, world).then((res) => res.data),
  delete: (id: number): Promise<void> =>
    api.delete(`/worlds/${id}`).then((res) => res.data),
  generate: (request: {
    keywords: string;
    generate_characters?: boolean;
    character_count?: number;
  }): Promise<{
    world: World;
    characters: Character[];
    generated_by: string;
    keywords: string;
  }> => api.post("/worlds/generate", request).then((res) => res.data),
  generateStream: (
    request: {
      keywords: string;
      generate_characters?: boolean;
      character_count?: number;
    },
    onProgress: (message: string, progress: number) => void,
    onComplete: (result: any) => void,
    onError: (error: string) => void
  ) => {
    const eventSource = new EventSource(
      `${API_BASE_URL}/worlds/generate-stream?keywords=${encodeURIComponent(
        request.keywords
      )}&generate_characters=${request.generate_characters}&character_count=${
        request.character_count
      }`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.completed) {
          eventSource.close();
          if (data.error) {
            onError(data.error);
          } else {
            onComplete(data.result);
          }
        } else {
          onProgress(data.message, data.progress);
        }
      } catch (error) {
        console.error("Error parsing SSE data:", error);
        eventSource.close();
        onError("データの解析に失敗しました");
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE connection error:", error);
      eventSource.close();
      onError("接続エラーが発生しました");
    };

    return eventSource;
  },
};

export const charactersApi = {
  getAll: (worldId?: number): Promise<Character[]> => {
    const params = worldId ? { world_id: worldId } : {};
    return api.get("/characters", { params }).then((res) => res.data);
  },
  getById: (id: number): Promise<Character> =>
    api.get(`/characters/${id}`).then((res) => res.data),
  create: (character: CreateCharacterRequest): Promise<Character> =>
    api.post("/characters", character).then((res) => res.data),
  update: (id: number, character: Partial<Character>): Promise<Character> =>
    api.put(`/characters/${id}`, character).then((res) => res.data),
  delete: (id: number): Promise<void> =>
    api.delete(`/characters/${id}`).then((res) => res.data),
};

export const discussionsApi = {
  getAll: (worldId?: number): Promise<Discussion[]> => {
    const params = worldId ? { world_id: worldId } : {};
    return api.get("/discussions", { params }).then((res) => res.data);
  },
  getById: (id: number): Promise<Discussion> =>
    api.get(`/discussions/${id}`).then((res) => res.data),
  create: (discussion: CreateDiscussionRequest): Promise<Discussion> =>
    api.post("/discussions", discussion).then((res) => res.data),
  start: (id: number): Promise<{ message: string; discussion_id: number }> =>
    api.post(`/discussions/${id}/start`).then((res) => res.data),
  update: (id: number, discussion: Partial<Discussion>): Promise<Discussion> =>
    api.put(`/discussions/${id}`, discussion).then((res) => res.data),
};
