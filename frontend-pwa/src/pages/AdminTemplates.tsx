import { apiFetch } from '../lib/api';
import { useState, useEffect, useRef } from 'react';
import { FileText, UploadCloud, Trash2, Globe, Lock, AlertCircle, CheckCircle2, Tag } from 'lucide-react';

interface Template {
  id: number;
  nombre: string;
  is_public: boolean;
  uploader_id: number;
}

const API = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function AdminTemplates() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchTemplates = async () => {
    try {
      const res = await apiFetch(`${API}/api/templates`, { credentials: 'include' });
      const data = await res.json();
      if (res.ok) {
        setTemplates(data.templates || []);
      } else {
        setUploadMsg({ type: 'error', text: `Error al cargar plantillas: ${data.error || res.status}` });
      }
    } catch (e: any) {
      setUploadMsg({ type: 'error', text: `Error de red al cargar plantillas: ${e.message}` });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTemplates(); }, []);

  const uploadFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.docx')) {
      setUploadMsg({ type: 'error', text: 'Solo se admiten archivos Word (.docx). Guarda el archivo como .docx desde Word.' });
      return;
    }

    const formData = new FormData();
    formData.append('document', file);

    setUploading(true);
    setUploadMsg(null);
    try {
      let res: Response;
      try {
        res = await apiFetch(`${API}/api/admin/templates/upload`, {
          method: 'POST',
          credentials: 'include',
          body: formData
        });
      } catch (netErr: any) {
        setUploadMsg({ type: 'error', text: `Error de red: No se pudo conectar al servidor (${netErr.message}). Verifica que el backend esté activo en: ${API}` });
        return;
      }

      let data: any = {};
      try {
        data = await res.json();
      } catch {
        setUploadMsg({ type: 'error', text: `El servidor respondió con HTTP ${res.status} pero no retornó JSON válido.` });
        return;
      }

      if (res.ok) {
        const varCount = data.variables?.length ?? '?';
        setUploadMsg({ type: 'success', text: `✓ "${data.nombre}" subida correctamente. Se detectaron ${varCount} variable(s) en la plantilla.` });
        fetchTemplates();
      } else {
        setUploadMsg({ type: 'error', text: `[HTTP ${res.status}] ${data.error || 'Error desconocido al subir la plantilla.'}` });
      }
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) await uploadFile(file);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) await uploadFile(file);
  };

  const handleDelete = async (id: number, nombre: string) => {
    if (!confirm(`¿Eliminar la plantilla "${nombre}"? Esta acción no se puede deshacer.`)) return;
    try {
      const res = await apiFetch(`${API}/api/admin/templates/delete/${id}`, {
        method: 'POST',
        credentials: 'include'
      });
      if (res.ok) {
        setUploadMsg({ type: 'success', text: `Plantilla "${nombre}" eliminada correctamente.` });
        fetchTemplates();
      } else {
        const data = await res.json().catch(() => ({}));
        setUploadMsg({ type: 'error', text: data.error || 'Error al eliminar la plantilla.' });
      }
    } catch (e: any) {
      setUploadMsg({ type: 'error', text: `Error de red: ${e.message}` });
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <FileText className="text-corporate-blue" />
            Formatos y Plantillas
          </h2>
          <p className="text-gray-500 mt-1">
            Sube tus documentos <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">.docx</code> con variables entre dobles corchetes <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">{'{{variable}}'}</code>
          </p>
        </div>
      </div>

      {/* Banner de estado */}
      {uploadMsg && (
        <div className={`flex items-start gap-3 p-4 rounded-xl border text-sm ${
          uploadMsg.type === 'success'
            ? 'bg-green-50 border-green-200 text-green-800'
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          {uploadMsg.type === 'success'
            ? <CheckCircle2 size={18} className="flex-shrink-0 mt-0.5" />
            : <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />}
          <span>{uploadMsg.text}</span>
          <button
            className="ml-auto flex-shrink-0 opacity-60 hover:opacity-100"
            onClick={() => setUploadMsg(null)}
          >✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* UPLOAD ZONE */}
        <div
          className={`bg-white p-6 rounded-xl shadow-sm border-2 border-dashed flex flex-col items-center justify-center text-center h-64 cursor-pointer transition-all ${
            dragOver
              ? 'border-corporate-blue bg-blue-50 scale-[1.01]'
              : 'border-gray-200 hover:border-corporate-blue hover:bg-blue-50/40'
          }`}
          onClick={() => !uploading && fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".docx"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileChange}
          />
          {uploading ? (
            <div className="flex flex-col items-center text-corporate-blue">
              <div className="w-10 h-10 border-4 border-blue-200 border-t-corporate-blue rounded-full animate-spin mb-4" />
              <p className="font-bold">Procesando plantilla...</p>
              <p className="text-xs text-gray-500 mt-1">Extrayendo variables del documento</p>
            </div>
          ) : (
            <>
              <UploadCloud size={44} className="text-corporate-blue mb-3" />
              <h3 className="font-bold text-gray-900">Subir nuevo formato</h3>
              <p className="text-xs text-gray-500 mt-2 max-w-xs leading-relaxed">
                Haz clic aquí o arrastra un archivo <strong>.docx</strong> con variables
                como <code className="bg-gray-100 px-1 rounded">{'{{nombre_cliente}}'}</code>
              </p>
            </>
          )}
        </div>

        {/* TEMPLATES LIST */}
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4 content-start">
          {loading && (
            <div className="col-span-full p-8 text-center text-gray-500">Cargando plantillas...</div>
          )}
          {!loading && templates.length === 0 && (
            <div className="col-span-full p-8 text-center text-gray-500 bg-white rounded-xl border border-gray-100 shadow-sm">
              <FileText className="mx-auto mb-3 text-gray-300" size={40} />
              <p className="font-medium">No hay formatos disponibles</p>
              <p className="text-sm mt-1">Sube tu primer archivo .docx para comenzar</p>
            </div>
          )}

          {templates.map(t => (
            <div
              key={t.id}
              className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow relative group"
            >
              <div className="w-10 h-10 bg-blue-50 text-corporate-blue rounded-lg flex items-center justify-center mb-3">
                <FileText size={20} />
              </div>
              <h4 className="font-bold text-gray-900 leading-tight mb-2 pr-8">{t.nombre}</h4>
              <div className="flex items-center text-xs text-gray-500">
                {t.is_public
                  ? <><Globe size={13} className="mr-1 text-green-500" />Público (Toda la empresa)</>
                  : <><Lock size={13} className="mr-1 text-gray-400" />Privado</>}
              </div>

              <button
                onClick={(e) => { e.stopPropagation(); handleDelete(t.id, t.nombre); }}
                className="absolute top-4 right-4 p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                title="Eliminar formato"
              >
                <Trash2 size={18} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Guía rápida */}
      <div className="bg-amber-50 border border-amber-100 rounded-xl p-5 text-sm text-amber-900 space-y-2">
        <p className="font-semibold flex items-center gap-2"><Tag size={16} />¿Cómo crear una plantilla compatible?</p>
        <ol className="list-decimal list-inside space-y-1 text-amber-800">
          <li>Abre tu documento Word (.docx)</li>
          <li>Coloca las variables de los datos como <code className="bg-amber-100 px-1.5 rounded">{'{{nombre_empresa}}'}</code>, <code className="bg-amber-100 px-1.5 rounded">{'{{rfc}}'}</code>, <code className="bg-amber-100 px-1.5 rounded">{'{{fecha}}'}</code></li>
          <li>Las variables de imagen se nombran con <code className="bg-amber-100 px-1.5 rounded">{'{{foto_fachada}}'}</code> seguido de <strong>una imagen de marcador de posición</strong> en el documento</li>
          <li>Guarda como <strong>.docx</strong> (no .doc ni .pdf)</li>
          <li>Súbelo aquí y el sistema detectará todas las variables automáticamente</li>
        </ol>
      </div>
    </div>
  );
}
