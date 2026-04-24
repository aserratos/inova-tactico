import { apiFetch } from '../lib/api';
import { useState, useEffect, useRef } from 'react';
import { FileText, UploadCloud, Trash2, Globe, Lock } from 'lucide-react';

interface Template {
  id: number;
  nombre: string;
  is_public: boolean;
  uploader_id: number;
}

export default function AdminTemplates() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchTemplates = async () => {
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/templates`, { credentials: 'include' });
      const data = await res.json();
      if (res.ok) setTemplates(data.templates || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTemplates(); }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.docx')) {
      alert("Solo se admiten formatos Word (.docx)");
      return;
    }

    const formData = new FormData();
    formData.append('document', file);

    setUploading(true);
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/templates/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        alert("Plantilla procesada y subida exitosamente.");
        fetchTemplates();
      } else {
        alert(data.error || "Error al subir");
      }
    } catch (err) {
      alert("Error de red");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de eliminar esta plantilla base?')) return;
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/templates/delete/${id}`, {
        method: 'POST',
        credentials: 'include'
      });
      if (res.ok) fetchTemplates();
      else alert("Error al eliminar");
    } catch (e) {
      alert("Error de red");
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <FileText className="mr-3 text-corporate-blue" />
            Formatos y Plantillas
          </h2>
          <p className="text-gray-500 mt-1">Sube tus documentos .docx originales para que la IA los convierta en formularios de campo.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* UPLOAD ZONE */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center h-64 border-dashed border-2 border-corporate-blue hover:bg-blue-50 transition-colors cursor-pointer" onClick={() => fileInputRef.current?.click()}>
          <input type="file" accept=".docx" className="hidden" ref={fileInputRef} onChange={handleFileChange} />
          {uploading ? (
             <div className="flex flex-col items-center text-corporate-blue">
               <div className="w-10 h-10 border-4 border-blue-200 border-t-corporate-blue rounded-full animate-spin mb-4" />
               <p className="font-bold">Procesando y extrayendo variables...</p>
             </div>
          ) : (
             <>
               <UploadCloud size={48} className="text-corporate-blue mb-4" />
               <h3 className="font-bold text-gray-900">Subir nuevo formato</h3>
               <p className="text-xs text-gray-500 mt-2 max-w-xs">Haz clic aquí o arrastra tu archivo Word (.docx) con las variables entre dobles corchetes.</p>
             </>
          )}
        </div>

        {/* TEMPLATES LIST */}
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {loading && <div className="col-span-full p-8 text-center text-gray-500">Cargando plantillas...</div>}
          {!loading && templates.length === 0 && <div className="col-span-full p-8 text-center text-gray-500 bg-white rounded-xl border border-gray-100 shadow-sm">No hay formatos disponibles en la base de datos.</div>}
          
          {templates.map(t => (
            <div key={t.id} className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow relative group">
              <div className="w-10 h-10 bg-blue-50 text-corporate-blue rounded-lg flex items-center justify-center mb-3">
                <FileText size={20} />
              </div>
              <h4 className="font-bold text-gray-900 leading-tight mb-1 pr-8">{t.nombre}</h4>
              <div className="flex items-center text-xs text-gray-500">
                {t.is_public ? <Globe size={14} className="mr-1 text-green-500" /> : <Lock size={14} className="mr-1 text-gray-400" />}
                {t.is_public ? 'Público (Toda la empresa)' : 'Privado'}
              </div>
              
              <button 
                onClick={(e) => { e.stopPropagation(); handleDelete(t.id); }}
                className="absolute top-4 right-4 p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                title="Eliminar formato"
              >
                <Trash2 size={18} />
              </button>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
