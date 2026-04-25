export const apiFetch = async (url: string, options: RequestInit = {}) => {
  let headers: Record<string, string> = { ...(options.headers as any) };
  
  // Esperar a que Clerk cargue si no está listo (hasta 2.5 segundos máximo)
  let retries = 25;
  while (!(window as any).Clerk?.session && retries > 0) {
      await new Promise(r => setTimeout(r, 100));
      retries--;
  }
  
  if ((window as any).Clerk && (window as any).Clerk.session) {
    const token = await (window as any).Clerk.session.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  
  return fetch(url, { ...options, headers });
};
