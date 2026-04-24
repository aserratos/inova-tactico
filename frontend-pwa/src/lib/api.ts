export const apiFetch = async (url: string, options: RequestInit = {}) => {
  let headers: Record<string, string> = { ...(options.headers as any) };
  if ((window as any).Clerk && (window as any).Clerk.session) {
    const token = await (window as any).Clerk.session.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return fetch(url, { ...options, headers });
};
