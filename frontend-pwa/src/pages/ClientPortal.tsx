import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { FileText, Download, Calendar, CheckCircle } from 'lucide-react';

interface Report {
  id: number;
  nombre: string;
  status: string;
  template_name: string;
  fecha_actualizacion: string;
  archivo_compilado_path: string | null;
}

export default function ClientPortal() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/reports`);
        const data = await res.json();
        setReports(data.reports || []);
      } catch (error) {
        console.error('Failed to fetch reports', error);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  const handleDownload = async (id: number) => {
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/download/${id}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Reporte_${id}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (error) {
      alert("Error al descargar el archivo. Puede que no se haya compilado todavía.");
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Cargando tus reportes...</div>;

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Portal de Clientes</h1>
        <p className="text-gray-500 mt-2 text-lg">Hola, {user?.nombre_completo || 'Cliente'}. Aquí puedes consultar y descargar el historial de tus servicios realizados.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map(report => (
          <div key={report.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-corporate-blue/10 rounded-xl">
                  <FileText className="text-corporate-blue" size={24} />
                </div>
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <CheckCircle size={12} className="mr-1" />
                  Completado
                </span>
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 mb-1 line-clamp-2" title={report.nombre}>
                {report.nombre}
              </h3>
              <p className="text-sm text-gray-500 mb-4">{report.template_name}</p>
              
              <div className="flex items-center text-xs text-gray-400 mb-6">
                <Calendar size={14} className="mr-1" />
                <span>Actualizado: {report.fecha_actualizacion || 'N/A'}</span>
              </div>
              
              <button
                onClick={() => handleDownload(report.id)}
                className="w-full flex items-center justify-center space-x-2 bg-gray-50 hover:bg-corporate-blue hover:text-white text-gray-700 font-medium py-2.5 px-4 rounded-xl transition-colors border border-gray-200 hover:border-corporate-blue"
              >
                <Download size={18} />
                <span>Descargar Reporte</span>
              </button>
            </div>
          </div>
        ))}
        
        {reports.length === 0 && (
          <div className="col-span-full bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
            <div className="mx-auto w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
              <FileText className="text-gray-300" size={32} />
            </div>
            <h3 className="text-lg font-medium text-gray-900">Aún no hay reportes finalizados</h3>
            <p className="text-gray-500 mt-1 max-w-sm mx-auto">Cuando nuestros técnicos terminen y aprueben un reporte para tu empresa, aparecerá aquí listo para su descarga.</p>
          </div>
        )}
      </div>
    </div>
  );
}
