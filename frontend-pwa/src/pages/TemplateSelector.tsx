import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Search, PlusCircle } from 'lucide-react';

interface Template {
  id: number;
  nombre: string;
}

export default function TemplateSelector() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [startingId, setStartingId] = useState<number | null>(null);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/templates`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        setTemplates(data.templates || []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        if (!navigator.onLine) {
          alert('Estás en modo Offline. No puedes iniciar reportes nuevos, pero puedes continuar los existentes en el tablero.');
        }
      });
  }, []);

  const handleStartReport = async (templateId: number) => {
    setStartingId(templateId);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/start/${templateId}`, {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok && data.id) {
        navigate(`/capture/${data.id}`);
      } else {
        alert("Error al iniciar reporte. Revisa tu conexión a internet.");
      }
    } catch (e) {
      alert("Error de red");
    } finally {
      setStartingId(null);
    }
  };

  const filtered = templates.filter(t => t.nombre.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="p-8 text-center text-gray-500">Cargando biblioteca de plantillas...</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Nueva Operación</h2>
        <p className="text-gray-500 mt-1">Selecciona un formato base para iniciar el levantamiento</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6 flex items-center">
        <Search className="text-gray-400 mr-3" size={20} />
        <input 
          type="text"
          placeholder="Buscar por nombre de formato..."
          className="flex-1 outline-none text-gray-700 placeholder-gray-400"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map(t => (
          <div 
            key={t.id}
            onClick={() => { if (!startingId) handleStartReport(t.id); }}
            className={`bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-all cursor-pointer group ${startingId === t.id ? 'opacity-50 pointer-events-none' : ''}`}
          >
            <div className="w-12 h-12 bg-blue-50 text-corporate-blue rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              {startingId === t.id ? (
                <div className="w-6 h-6 border-2 border-corporate-blue border-t-transparent rounded-full animate-spin" />
              ) : (
                <FileText size={24} />
              )}
            </div>
            <h3 className="font-bold text-gray-900 mb-1 leading-tight group-hover:text-corporate-blue transition-colors">{t.nombre}</h3>
            <p className="text-sm text-gray-500 flex items-center mt-4">
              <PlusCircle size={16} className="mr-1" />
              Iniciar Captura
            </p>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="col-span-full py-12 text-center text-gray-500 border-2 border-dashed border-gray-200 rounded-xl">
            No se encontraron plantillas.
          </div>
        )}
      </div>
    </div>
  );
}
