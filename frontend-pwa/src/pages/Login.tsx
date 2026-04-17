import { useState } from 'react';

export default function Login() {
  const [step, setStep] = useState<'password' | 'mfa'>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const res = await fetch('http://localhost:8001/auth/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include'
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.message || 'Error al iniciar sesión');
      
      if (data.requires_mfa) {
        setStep('mfa');
      } else {
        window.location.href = '/';
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const res = await fetch('http://localhost:8001/auth/api/mfa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: mfaCode }),
        credentials: 'include'
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.message || 'Código inválido');
      
      // Auth success, redirect to dashboard
      window.location.href = '/';
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-corporate-light flex flex-col justify-center items-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="p-8">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-corporate-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-center text-gray-900 mb-2">
            Centro de Comando
          </h2>
          <p className="text-center text-gray-500 mb-8 text-sm">
            {step === 'password' ? 'Ingresa tus credenciales operativas' : 'Verificación de dos pasos requerida'}
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 rounded-lg text-sm text-center">
              {error}
            </div>
          )}

          {step === 'password' ? (
            <form onSubmit={handlePasswordSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Correo Electrónico</label>
                <input
                  type="email"
                  required
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-transparent transition-all outline-none"
                  placeholder="ejemplo@empresa.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
                <input
                  type="password"
                  required
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-transparent transition-all outline-none"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-corporate-blue hover:bg-blue-700 text-white font-medium py-3 rounded-lg shadow-md hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? 'Verificando...' : 'Acceder al Sistema'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleMfaSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 text-center">Código de Autenticador (MFA)</label>
                <input
                  type="text"
                  required
                  maxLength={6}
                  className="w-full px-4 py-4 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-transparent transition-all outline-none text-center text-2xl tracking-widest font-mono"
                  placeholder="000000"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                />
              </div>
              <button
                type="submit"
                disabled={loading || mfaCode.length !== 6}
                className="w-full bg-corporate-dark hover:bg-blue-900 text-white font-medium py-3 rounded-lg shadow-md transition-all disabled:opacity-50"
              >
                {loading ? 'Validando...' : 'Verificar Identidad'}
              </button>
              <button
                type="button"
                onClick={() => setStep('password')}
                className="w-full text-sm text-gray-500 hover:text-gray-700 mt-2"
              >
                Volver
              </button>
            </form>
          )}
        </div>
        <div className="bg-gray-50 px-8 py-4 text-center border-t border-gray-100">
          <p className="text-xs text-gray-400">Plataforma PWA Empresarial • v2.0</p>
        </div>
      </div>
    </div>
  );
}
