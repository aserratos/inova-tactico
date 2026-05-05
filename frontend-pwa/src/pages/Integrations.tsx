import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Save, Link as LinkIcon, Database } from 'lucide-react';

export default function Integrations() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    erp_url: '',
    erp_db: '',
    erp_username: '',
    erp_api_key: ''
  });

  const fetchConfig = async () => {
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/integrations/odoo`);
      const data = await res.json();
      if (data.config) {
        setFormData({
          erp_url: data.config.erp_url || '',
          erp_db: data.config.erp_db || '',
          erp_username: data.config.erp_username || '',
          erp_api_key: data.config.erp_api_key ? '********' : '' // Masked if it exists
        });
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
    setSaving(true);
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/integrations/odoo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      alert('Configuración guardada exitosamente.');
      fetchConfig();
    } catch (error: any) {
      alert(error.message || 'Error al guardar la configuración.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Cargando configuración...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Integraciones</h1>
          <p className="text-sm text-gray-500 mt-1">
            Conecta Inova Táctico con tus herramientas operativas (ERPs).
          </p>
        </div>
        <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600">
          <LinkIcon size={24} />
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex items-center gap-3">
          <Database className="text-corporate-blue" />
          <div>
            <h2 className="text-lg font-bold text-gray-900">Odoo ERP</h2>
            <p className="text-sm text-gray-500">Credenciales de API XML-RPC</p>
          </div>
        </div>
        
        <form onSubmit={handleSave} className="p-6 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">URL de Odoo</label>
              <input 
                type="url" 
                required
                value={formData.erp_url}
                onChange={(e) => setFormData({...formData, erp_url: e.target.value})}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                placeholder="Ej. https://mi-empresa.odoo.com"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de la Base de Datos</label>
              <input 
                type="text" 
                required
                value={formData.erp_db}
                onChange={(e) => setFormData({...formData, erp_db: e.target.value})}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                placeholder="Ej. mi-empresa-db"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Usuario (Email)</label>
              <input 
                type="email" 
                required
                value={formData.erp_username}
                onChange={(e) => setFormData({...formData, erp_username: e.target.value})}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                placeholder="admin@empresa.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña o API Key</label>
              <input 
                type="password" 
                required={!formData.erp_api_key || formData.erp_api_key !== '********'}
                value={formData.erp_api_key}
                onChange={(e) => setFormData({...formData, erp_api_key: e.target.value})}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                placeholder={formData.erp_api_key === '********' ? "******** (Ya configurada)" : "Escribe tu password / API Key"}
              />
              <p className="text-xs text-gray-500 mt-1">Por seguridad, usa una API Key generada en Odoo.</p>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-gray-100">
            <button 
              type="submit" 
              disabled={saving}
              className="flex items-center gap-2 bg-corporate-blue text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 font-medium"
            >
              <Save size={18} />
              <span>{saving ? 'Guardando...' : 'Guardar Configuración'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
