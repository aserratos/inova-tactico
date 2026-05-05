export const apiFetch = async (url: string, options: RequestInit = {}) => {
  let headers: Record<string, string> = { ...(options.headers as any) };
  
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return fetch(url, { ...options, headers });
};
