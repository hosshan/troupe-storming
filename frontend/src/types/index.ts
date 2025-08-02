export interface World {
  id: number;
  name: string;
  description: string;
  background: string;
  created_at: string;
  updated_at?: string;
}

export interface Character {
  id: number;
  name: string;
  description: string;
  personality: string;
  background: string;
  tinytroupe_config: any;
  world_id: number;
  created_at: string;
  updated_at?: string;
}

export interface Discussion {
  id: number;
  theme: string;
  description: string;
  world_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  created_at: string;
  updated_at?: string;
}

export interface CreateWorldRequest {
  name: string;
  description: string;
  background: string;
}

export interface CreateCharacterRequest {
  name: string;
  description: string;
  personality: string;
  background: string;
  world_id: number;
  tinytroupe_config?: any;
}

export interface CreateDiscussionRequest {
  theme: string;
  description: string;
  world_id: number;
}