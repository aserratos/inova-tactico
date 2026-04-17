import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileDown, FileCog } from 'lucide-react';

interface Report {
  id: number;
  nombre: string;
  status: string;
  porcentaje_avance: number;
  fecha_actualizacion: string;
  asignado: string;
  asignado_iniciales: string;
  has_compiled_file?: boolean;
}

export default function KanbanBoard() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetches the real data from Flask
    fetch('http://localhost:8001/api/reports', { credentials: 'include' })
      .then(res => {
        if (!res.ok) throw new Error('Error al cargar datos. ¿Sesión iniciada?');
        return res.json();
      })
      .then(data => {
        setReports(data.reports);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const getStatusCount = (status: string) => reports.filter(r => r.status === status).length;
  const getReportsByStatus = (status: string) => reports.filter(r => r.status === status);

  const handleCompile = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation(); // Evitar que abra la captura
    if (!confirm('¿Deseas enviar a generar el reporte final en Word?')) return;
    
    try {
      const res = await fetch(`http://localhost:8001/api/report/compile/${id}`, {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok) {
        alert("¡Orden enviada! Tu documento se está generando. Vuelve en un momento.");
      } else {
        alert(data.error || "Error al compilar.");
      }
    } catch (err) {
      alert("Error de red");
    }
  };

  const handleDownload = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      const res = await fetch(`http://localhost:8001/api/report/download/${id}`, {
        credentials: 'include'
      });
      
      const contentType = res.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await res.json();
        if (data.url) {
          window.location.href = data.url;
        } else {
          alert(data.error || "Error al descargar.");
        }
      } else {
        // Blob download (direct from Flask send_file)
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Reporte_${id}.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      alert("Error al descargar");
    }
  };

  const Column = ({ title, status, countClass }: { title: string, status: string, countClass: string }) => (
    <div className="w-80 flex flex-col bg-gray-50/50 rounded-xl p-4 border border-gray-200 shadow-sm shrink-0">
      <h3 className="font-semibold text-gray-700 flex items-center justify-between mb-4">
        {title}
        <span className={`${countClass} text-xs py-1 px-2 rounded-full`}>{getStatusCount(status)}</span>
      </h3>
      <div className="space-y-3 flex-1 overflow-y-auto">
        {getReportsByStatus(status).map(report => (
          <div key={report.id} onClick={() => navigate(`/capture/${report.id}`)} className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer">
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-semibold text-corporate-blue bg-blue-50 px-2 py-1 rounded">
                REQ-{report.id.toString().padStart(3, '0')}
              </span>
              <span className="text-xs text-gray-400">{report.fecha_actualizacion}</span>
            </div>
            <h4 className="font-medium text-gray-900 leading-snug">{report.nombre}</h4>
            <div className="mt-3 flex items-center justify-between">
              <div className="w-6 h-6 rounded-full bg-blue-100 border-2 border-white shadow-sm flex items-center justify-center text-xs font-bold text-corporate-blue" title={report.asignado}>
                {report.asignado_iniciales}
              </div>
              <span className="text-xs font-medium text-gray-500">{report.porcentaje_avance}%</span>
            </div>
            
            {status === 'terminado' && (
              <div className="mt-4 pt-3 border-t border-gray-100 flex justify-end">
                {report.has_compiled_file ? (
                  <button 
                    onClick={(e) => handleDownload(e, report.id)}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-green-50 text-green-700 hover:bg-green-100 rounded-md text-xs font-bold transition-colors"
                  >
                    <FileDown size={14} />
                    <span>Descargar Word</span>
                  </button>
                ) : (
                  <button 
                    onClick={(e) => handleCompile(e, report.id)}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-blue-50 text-corporate-blue hover:bg-blue-100 rounded-md text-xs font-bold transition-colors"
                  >
                    <FileCog size={14} />
                    <span>Generar Word</span>
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  if (loading) return <div className="p-8">Cargando tablero...</div>;
  if (error) return <div className="p-8 text-red-500">{error} (Asegúrate de haber iniciado sesión en localhost:8001)</div>;

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Operaciones en Curso</h2>
        <p className="text-gray-500 mt-1">Gestión centralizada de entregables (Datos Reales)</p>
      </div>
      
      <div className="flex-1 overflow-x-auto pb-8 md:pb-0">
        <div className="flex space-x-6 min-w-max h-full">
          <Column title="Por Hacer" status="por_hacer" countClass="bg-gray-200 text-gray-600" />
          <Column title="En Ejecución" status="en_ejecucion" countClass="bg-corporate-blue text-white" />
          <Column title="Pendiente" status="pendiente" countClass="bg-yellow-100 text-yellow-800" />
          <Column title="Terminado" status="terminado" countClass="bg-green-100 text-green-800" />
        </div>
      </div>
    </div>
  );
}
