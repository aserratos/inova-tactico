export const apiFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
  let headers: Record<string, string> = { ...(options.headers as any) };
  
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  console.debug(`[apiFetch] ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, { ...options, headers });
    
    // Si el servidor responde 401, el token expiró — limpiarlo automáticamente
    if (response.status === 401) {
      console.warn('[apiFetch] 401 recibido — token inválido o expirado. Cerrando sesión.');
      localStorage.removeItem('auth_token');
      // Disparar evento para que AuthContext reaccione
      window.dispatchEvent(new Event('auth:logout'));
    }
    
    return response;
  } catch (err: any) {
    // Captura errores de red (CORS real, servidor caído, timeout)
    console.error(`[apiFetch] Error de red en ${url}:`, err.message, err);
    throw err;
  }
};
