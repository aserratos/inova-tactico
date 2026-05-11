import Dexie, { type EntityTable } from 'dexie';

export interface SyncTask {
  id?: number;
  url: string;
  method: string;
  payload: any;
  isFormData?: boolean;
  timestamp: string;
  status: 'pending' | 'failed';
  retryCount: number;
}

export interface CachedReport {
  id: number;
  template_id: number;
  nombre: string;
  status: string;
  porcentaje_avance: number;
  comentarios: string;
  data_json: string;
  updated_at: string;
  fecha_actualizacion?: string;
  asignado?: string;
  asignado_iniciales?: string;
  has_compiled_file?: boolean;
  template_name?: string;
  customer_id?: number | null;
  text_vars?: string[];
  image_vars?: string[];
}

export interface CachedTemplate {
  id: number;
  nombre: string;
  variables_json: string;
}

export interface CachedCustomer {
  id: number;
  nombre_empresa: string;
  rfc: string | null;
  contacto_principal: string | null;
  erp_source: string | null;
}

const db = new Dexie('InovaTacticoDB') as Dexie & {
  syncQueue: EntityTable<SyncTask, 'id'>;
  cachedReports: EntityTable<CachedReport, 'id'>;
  cachedTemplates: EntityTable<CachedTemplate, 'id'>;
  cachedCustomers: EntityTable<CachedCustomer, 'id'>;
};

// Declaración del esquema de la base de datos local
db.version(2).stores({
  syncQueue: '++id, status, timestamp',
  cachedReports: 'id, template_id, status, updated_at',
  cachedTemplates: 'id',
  cachedCustomers: 'id'
}).upgrade(tx => {
  // Manejo de migración desde v1
});

export { db };
