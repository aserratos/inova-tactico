import { useEffect, useState } from 'react';
import { db } from '../lib/db';

export function SyncEngine() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      processSyncQueue();
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial check just in case we started online with pending items
    if (navigator.onLine) {
      processSyncQueue();
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const processSyncQueue = async () => {
    if (isSyncing) return;
    setIsSyncing(true);

    try {
      const pendingTasks = await db.syncQueue.where('status').equals('pending').toArray();
      
      if (pendingTasks.length > 0) {
        console.log(`[SyncEngine] Encontradas ${pendingTasks.length} tareas pendientes.`);
        
        for (const task of pendingTasks) {
          try {
            let bodyData: BodyInit | null = null;
            let headers: Record<string, string> = {};

            if (task.isFormData) {
              const fd = new FormData();
              Object.keys(task.payload).forEach(key => {
                fd.append(key, task.payload[key]);
              });
              bodyData = fd;
              // No set Content-Type header so browser sets multipart/form-data with boundary
            } else {
              bodyData = JSON.stringify(task.payload);
              headers['Content-Type'] = 'application/json';
            }

            const response = await fetch(task.url, {
              method: task.method,
              headers: headers,
              body: bodyData,
              credentials: 'include'
            });

            if (response.ok) {
              // Delete task on success
              if (task.id) await db.syncQueue.delete(task.id);
              console.log(`[SyncEngine] Tarea ${task.id} completada.`);
            } else {
              console.error(`[SyncEngine] Error HTTP ${response.status} en tarea ${task.id}`);
              if (task.id) await db.syncQueue.update(task.id, { retryCount: task.retryCount + 1 });
            }
          } catch (err) {
            console.error(`[SyncEngine] Fallo de red al sincronizar tarea ${task.id}`, err);
            // Will retry later
          }
        }
      }
    } catch (err) {
      console.error('[SyncEngine] Error procesando cola:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  if (!isOnline) {
    return (
      <div className="fixed top-0 left-0 w-full bg-red-500 text-white text-xs text-center py-1 z-50 flex items-center justify-center gap-2 shadow-md">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
        Estás trabajando sin conexión. Los reportes se guardarán en tu dispositivo.
      </div>
    );
  }

  if (isSyncing) {
    return (
      <div className="fixed top-0 left-0 w-full bg-blue-500 text-white text-xs text-center py-1 z-50 flex items-center justify-center gap-2 shadow-md animate-pulse">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
        Sincronizando reportes pendientes...
      </div>
    );
  }

  return null; // Don't render anything if online and not syncing
}
