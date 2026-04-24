import { useState } from 'react';
import { startRegistration } from '@simplewebauthn/browser';
import { ShieldCheck, Fingerprint, Lock } from 'lucide-react';

export default function SecuritySettings() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const registerDevice = async () => {
    setLoading(true);
    setMessage({ text: '', type: '' });

    try {
      // 1. Get registration options from server
      const resOptions = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/webauthn/register/generate-options`, {
        method: 'POST',
        credentials: 'include'
      });
      
      const options = await resOptions.json();
      if (!resOptions.ok) throw new Error(options.error || 'No se pudieron generar las opciones biométricas');

      // 2. Invoke native scanner
      const attResp = await startRegistration(options);

      // 3. Send response to server to save credential
      const resVerify = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/webauthn/register/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(attResp),
        credentials: 'include'
      });

      const verification = await resVerify.json();

      if (resVerify.ok && verification.status === 'ok') {
        setMessage({ text: '¡Dispositivo registrado exitosamente! Ya puedes usar FaceID o tu huella para entrar.', type: 'success' });
      } else {
        throw new Error(verification.error || 'Error al verificar la huella en el servidor');
      }

    } catch (err: any) {
      console.error(err);
      setMessage({ text: 'No se pudo registrar el dispositivo. Asegúrate de tener configurado un PIN, Huella o FaceID en tu equipo.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ShieldCheck className="text-corporate-blue" />
          Ajustes de Seguridad
        </h2>
        <p className="text-gray-500 mt-1">Administra los métodos de acceso a tu cuenta.</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex flex-col md:flex-row gap-6 items-start md:items-center">
          <div className="bg-blue-50 p-4 rounded-full flex-shrink-0">
            <Fingerprint size={32} className="text-corporate-blue" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">Login Biométrico (Passkeys)</h3>
            <p className="text-sm text-gray-600 mt-1">
              Vincula este dispositivo (celular o computadora) a tu cuenta usando FaceID, TouchID o Windows Hello. 
              Esto te permitirá entrar de forma instantánea sin escribir contraseñas ni códigos MFA.
            </p>
          </div>
          <button
            onClick={registerDevice}
            disabled={loading}
            className="w-full md:w-auto bg-black hover:bg-gray-800 text-white font-medium py-2 px-6 rounded-lg shadow-md transition-all disabled:opacity-50 flex items-center justify-center gap-2 flex-shrink-0"
          >
            {loading ? 'Activando...' : 'Registrar este Dispositivo'}
          </button>
        </div>

        {message.text && (
          <div className={`p-4 text-sm font-medium ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {message.text}
          </div>
        )}

        <div className="p-6 bg-gray-50 flex flex-col md:flex-row gap-6 items-start md:items-center opacity-70">
          <div className="bg-gray-200 p-4 rounded-full flex-shrink-0">
            <Lock size={32} className="text-gray-500" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">Autenticador (MFA Clásico)</h3>
            <p className="text-sm text-gray-600 mt-1">
              La autenticación en dos pasos mediante la aplicación (Google Authenticator) está habilitada por defecto como método de respaldo.
            </p>
          </div>
          <button disabled className="w-full md:w-auto bg-gray-300 text-gray-500 font-medium py-2 px-6 rounded-lg cursor-not-allowed flex-shrink-0">
            Configurado
          </button>
        </div>
      </div>
    </div>
  );
}
