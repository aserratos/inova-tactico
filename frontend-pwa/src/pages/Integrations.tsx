import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Save, Link as LinkIcon, Database, CheckCircle, XCircle, Loader, RefreshCw, AlertTriangle } from 'lucide-react';

type SaveStatus = 'idle' | 'saving' | 'success' | 'error';
type ConnStatus = 'unknown' | 'testing' | 'connected' | 'failed';

export default function Integrations() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const [saveMsg, setSaveMsg] = useState('');
  const [connStatus, setConnStatus] = useState<ConnStatus>('unknown');
  const [connMsg, setConnMsg] = useState('');
  const [connDetail, setConnDetail] = useState<string | null>(null); // detalles técnicos del error
  const [hasExistingKey, setHasExistingKey] = useState(false);
  const [formData, setFormData] = useState({
    erp_url: '',
    erp_db: '',
    erp_username: '',
    erp_api_key: ''
  });

  const API = import.meta.env.VITE_API_URL || 'http://localhost:8001';

  const fetchConfig = async () => {
    try {
      const res = await apiFetch(`${API}/api/admin/integrations/odoo`);
      if (!res.ok) return;
      const data = await res.json();
      if (data.config) {
        const cfg = data.config;
        setHasExistingKey(!!cfg.erp_api_key);
        setFormData({
          erp_url: cfg.erp_url || '',
          erp_db: cfg.erp_db || '',
          erp_username: cfg.erp_username || '',
          erp_api_key: '' // siempre vacío al cargar para no confundir
        });
        // Si hay datos guardados, mostrar como conectado si todo está lleno
        if (cfg.erp_url && cfg.erp_db && cfg.erp_username && cfg.erp_api_key) {
          setConnStatus('connected');
          setConnMsg('Credenciales guardadas. Prueba la conexión para verificar.');
        }
      }
    } catch (error) {
      console.error('Failed to fetch config', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus('saving');
    setSaveMsg('');
    try {
      // Validar que si hay key existente y no se ingresó nueva, dejamos la que está
      const payload: any = {
        erp_url: formData.erp_url.trim(),
        erp_db: formData.erp_db.trim(),
        erp_username: formData.erp_username.trim(),
      };
      // Solo incluir api_key si el usuario escribió algo nuevo
      if (formData.erp_api_key.trim()) {
        payload.erp_api_key = formData.erp_api_key.trim();
      } else if (!hasExistingKey) {
        setSaveStatus('error');
        setSaveMsg('La API Key es requerida.');
        return;
      }

      let res: Response;
      try {
        res = await apiFetch(`${API}/api/admin/integrations/odoo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } catch (netErr: any) {
        throw new Error(`Error de red: No se pudo conectar al servidor (${netErr.message}). Verifica que el backend esté activo en: ${API}`);
      }

      let data: any = {};
      try {
        data = await res.json();
      } catch {
        throw new Error(`El servidor respondió con HTTP ${res.status} pero la respuesta no es JSON válido.`);
      }

      if (!res.ok || data.error) {
        throw new Error(`[HTTP ${res.status}] ${data.error || data.message || 'Error al guardar'}`);
      }
      
      setSaveStatus('success');
      setSaveMsg('Configuración guardada exitosamente.');
      setHasExistingKey(true);
      setConnStatus('unknown');
      setConnDetail(null);
      // Auto-ocultar mensaje después de 4s
      setTimeout(() => setSaveStatus('idle'), 4000);
    } catch (error: any) {
      setSaveStatus('error');
      setSaveMsg(error.message || 'Error inesperado al guardar.');
    }
  };

  const handleTestConnection = async () => {
    setConnStatus('testing');
    setConnMsg('Probando conexión con Odoo...');
    setConnDetail(null);
    try {
      let res: Response;
      try {
        res = await apiFetch(`${API}/api/admin/integrations/odoo/test`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
      } catch (netErr: any) {
        setConnStatus('failed');
        setConnMsg('Error de red: No se pudo alcanzar el servidor backend.');
        setConnDetail(`URL del backend: ${API}\nError: ${netErr.message}\n\nVerifica que el servidor esté activo y accesible.`);
        return;
      }

      let data: any = {};
      const rawText = await res.text();
      try {
        data = JSON.parse(rawText);
      } catch {
        setConnStatus('failed');
        setConnMsg(`El servidor respondió con HTTP ${res.status} pero con contenido inesperado.`);
        setConnDetail(`Respuesta del servidor:\n${rawText.slice(0, 500)}`);
        return;
      }

      if (!res.ok) {
        setConnStatus('failed');
        setConnMsg(data.error || `Error HTTP ${res.status}`);
        setConnDetail(`Código HTTP: ${res.status}\nURL probada: ${API}/api/admin/integrations/odoo/test\nRespuesta del servidor: ${JSON.stringify(data, null, 2)}`);
        return;
      }

      setConnStatus('connected');
      setConnMsg(`✓ Conectado correctamente. Odoo ${data.odoo_version || ''} | UID: ${data.uid}`);
      setConnDetail(null);
    } catch (error: any) {
      setConnStatus('failed');
      setConnMsg(error.message || 'No se pudo conectar. Revisa las credenciales.');
      setConnDetail(`Error inesperado: ${error.message}`);
    }
  };

  if (loading) return (
    <div className="p-8 text-center text-gray-500 flex items-center justify-center gap-2">
      <Loader className="animate-spin" size={18} /> Cargando configuración...
    </div>
  );

  const connStatusStyle = {
    unknown: 'bg-gray-100 text-gray-600',
    testing: 'bg-blue-50 text-blue-700',
    connected: 'bg-green-50 text-green-700',
    failed: 'bg-red-50 text-red-700'
  }[connStatus];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Integraciones</h1>
          <p className="text-sm text-gray-500 mt-1">
            Conecta OmniFlow con tu ERP para sincronizar clientes automáticamente.
          </p>
        </div>
        <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600">
          <LinkIcon size={24} />
        </div>
      </div>

      {/* Odoo Card */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Card header */}
        <div className="p-6 border-b border-gray-100 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Database className="text-corporate-blue" />
            <div>
              <h2 className="text-lg font-bold text-gray-900">Odoo ERP</h2>
              <p className="text-sm text-gray-500">Conexión XML-RPC para sincronización de empresas</p>
            </div>
          </div>
          {/* Connection badge */}
          <span className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full ${connStatusStyle}`}>
            {connStatus === 'connected' && <CheckCircle size={13} />}
            {connStatus === 'failed' && <XCircle size={13} />}
            {connStatus === 'testing' && <Loader size={13} className="animate-spin" />}
            {connStatus === 'unknown' && <AlertTriangle size={13} />}
            {connStatus === 'unknown' && 'Sin verificar'}
            {connStatus === 'testing' && 'Probando...'}
            {connStatus === 'connected' && 'Conectado'}
            {connStatus === 'failed' && 'Error de conexión'}
          </span>
        </div>

        {/* Connection test message */}
        {connMsg && (
          <div className={`mx-6 mt-4 p-3 rounded-xl text-sm ${connStatus === 'connected' ? 'bg-green-50 text-green-700' : connStatus === 'failed' ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'}`}>
            <p className="font-medium">{connMsg}</p>
            {connDetail && (
              <pre className="mt-2 text-xs whitespace-pre-wrap break-all font-mono opacity-80 bg-black/5 rounded p-2">{connDetail}</pre>
            )}
          </div>
        )}

        <form onSubmit={handleSave} className="p-6 space-y-5">
          {/* Save status banner */}
          {saveStatus === 'success' && (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-xl text-green-700 text-sm">
              <CheckCircle size={16} /> {saveMsg}
            </div>
          )}
          {saveStatus === 'error' && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
              <XCircle size={16} /> {saveMsg}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL de Odoo <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                required
                value={formData.erp_url}
                onChange={(e) => setFormData({...formData, erp_url: e.target.value})}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                placeholder="https://tuempresa.odoo.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base de Datos <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.erp_db}
                onChange={(e) => setFormData({...formData, erp_db: e.target.value})}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                placeholder="tuempresa"
              />
              <p className="text-xs text-gray-400 mt-1">Normalmente el subdominio de tu URL de Odoo</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Usuario (Email de Odoo) <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                required
                value={formData.erp_username}
                onChange={(e) => setFormData({...formData, erp_username: e.target.value})}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                placeholder="admin@tuempresa.com"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key {!hasExistingKey && <span className="text-red-500">*</span>}
                {hasExistingKey && <span className="ml-2 text-xs text-green-600 font-normal">✓ Ya hay una API Key guardada</span>}
              </label>
              <input
                type="password"
                required={!hasExistingKey}
                value={formData.erp_api_key}
                onChange={(e) => setFormData({...formData, erp_api_key: e.target.value})}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                placeholder={hasExistingKey ? 'Deja vacío para conservar la actual' : 'Pega aquí tu API Key de Odoo'}
              />
              <p className="text-xs text-gray-400 mt-1">
                En Odoo: ve a Ajustes → Usuarios → tu usuario → pestaña <strong>Seguridad de la Cuenta</strong> → Generar clave API.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-center pt-4 border-t border-gray-100 gap-3">
            <button
              type="button"
              disabled={connStatus === 'testing' || (!hasExistingKey && !formData.erp_api_key)}
              onClick={handleTestConnection}
              className="flex items-center gap-2 border border-gray-300 text-gray-700 px-4 py-2.5 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-40 text-sm font-medium"
            >
              <RefreshCw size={16} className={connStatus === 'testing' ? 'animate-spin' : ''} />
              Probar conexión
            </button>
            <button
              type="submit"
              disabled={saveStatus === 'saving'}
              className="flex items-center gap-2 bg-corporate-blue text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 font-medium"
            >
              {saveStatus === 'saving' ? <Loader size={18} className="animate-spin" /> : <Save size={18} />}
              <span>{saveStatus === 'saving' ? 'Guardando...' : 'Guardar Configuración'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Info box */}
      <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5 text-sm text-blue-800 space-y-1">
        <p className="font-semibold">¿Cómo generar una API Key en Odoo?</p>
        <ol className="list-decimal list-inside space-y-1 text-blue-700">
          <li>Inicia sesión en tu instancia de Odoo</li>
          <li>Ve a <strong>Ajustes → Usuarios y Compañías → Usuarios</strong></li>
          <li>Abre tu perfil de usuario</li>
          <li>Pestaña <strong>Seguridad de la Cuenta</strong></li>
          <li>Sección <strong>Claves de API</strong> → <strong>Nuevo</strong></li>
          <li>Copia la clave generada y pégala aquí</li>
        </ol>
      </div>
    </div>
  );
}
