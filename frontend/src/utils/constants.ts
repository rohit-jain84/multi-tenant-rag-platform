export const ROUTES = {
  DOCUMENTS: '/documents',
  QUERY: '/query',
  EVAL: '/eval',
  TENANTS: '/tenants',
  HEALTH: '/health',
} as const;

export const DEFAULTS = {
  TOP_K: 20,
  TOP_N: 5,
  PAGE_SIZE: 10,
  HEALTH_POLL_INTERVAL: 30000,
  STATUS_POLL_INTERVAL: 5000,
} as const;

export const CHUNKING_STRATEGIES = ['fixed', 'semantic', 'parent_child'] as const;
export type ChunkingStrategy = (typeof CHUNKING_STRATEGIES)[number];
