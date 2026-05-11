import { db } from './db';
import { apiFetch } from './api';

export const processSyncQueue = async () => {
  if (!navigator.onLine) return;

  const tasks = await db.syncQueue.where('status').equals('pending').toArray();
  
  if (tasks.length === 0) return;

  console.log(`Iniciando sincronización de ${tasks.length} tareas pendientes...`);

  for (const task of tasks) {
    try {
      let body: any = task.payload;

      // Si es FormData, reconstruir el objeto FormData desde el payload de IndexedDB
      if (task.isFormData) {
        const formData = new FormData();
        Object.keys(task.payload).forEach(key => {
          formData.append(key, task.payload[key]);
        });
        body = formData;
      }

      const response = await apiFetch(task.url, {
        method: task.method,
        body: task.isFormData ? body : JSON.stringify(body),
        headers: task.isFormData ? undefined : {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (response.ok) {
        // Tarea exitosa, eliminar de la cola
        await db.syncQueue.delete(task.id!);
        console.log(`Tarea ${task.id} sincronizada correctamente.`);
      } else {
        // Error de servidor (no red)
        await db.syncQueue.update(task.id!, { 
          retryCount: task.retryCount + 1,
          status: task.retryCount >= 3 ? 'failed' : 'pending'
        });
      }
    } catch (error) {
      console.error(`Error sincronizando tarea ${task.id}:`, error);
      // Mantener en pending
    }
  }
};
