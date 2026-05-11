import { apiFetch } from '../lib/api';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileDown, FileCog, Copy, Clock, AlertTriangle, CheckCircle, User as UserIcon } from 'lucide-react';
import { db } from '../lib/db';
import { useAuth } from '../contexts/AuthContext';

interface Report {
  id: number;
  nombre: string;
  status: string;
  porcentaje_avance: number;
  fecha_actualizacion: string;
  assigned_to_id: number;
  assigned_to_name: string;
  created_by_id: number;
  has_compiled_file?: boolean;
}

interface TeamMember {
  id: number;
  nombre_completo: string;
}

export default function KanbanBoard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const [resReports, resTeam] = await Promise.all([
          apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/reports`, { credentials: 'include' }),
          apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/team`, { credentials: 'include' }).catch(() => null)
        ]);

        if (!resReports.ok) throw new Error('Error de servidor o sesión expirada');
        
        const data = await resReports.json();
        setReports(data.reports);

        if (resTeam && resTeam.ok) {
           const teamData = await resTeam.json();
           setTeam(teamData.users || []);
        }
        
        // Save to offline cache
        const offlineReports = await db.cachedReports.filter(r => r.id < 0).toArray();
        await db.cachedReports.clear();
        await db.cachedReports.bulkAdd([...data.reports, ...offlineReports]);
        setLoading(false);
      } catch (err: any) {
        console.warn("No se pudo conectar al servidor. Cargando caché offline...");
        const cached = await db.cachedReports.toArray();
        if (cached && cached.length > 0) {
          setReports(cached as any as Report[]);
          setError("Modo Sin Conexión - Mostrando datos guardados localmente");
        } else {
          setError(err.message || "Error de conexión");
        }
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  const getStatusCount = (status: string) => reports.filter(r => r.status === status).length;
  const getReportsByStatus = (status: string) => reports.filter(r => r.status === status);

  const handleCompile = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation(); // Evitar que abra la captura
    if (!confirm('¿Deseas enviar a generar el reporte final en Word?')) return;
    
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/compile/${id}`, {
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

  const handleClone = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm('¿Deseas clonar este reporte para usar sus datos base?')) return;
    
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/clone/${id}`, {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok) {
        alert("¡Reporte clonado exitosamente! Lo encontrarás en la columna 'Por Hacer'.");
        window.location.reload();
      } else {
        alert(data.error || "Error al clonar el reporte.");
      }
    } catch (err) {
      alert("Error de red al intentar clonar.");
    }
  };

  const handleDownload = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/download/${id}`, {
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

  const handleAssign = async (e: React.ChangeEvent<HTMLSelectElement>, reportId: number) => {
    e.stopPropagation();
    const newUserId = parseInt(e.target.value);
    if (!newUserId) return;

    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/assign/${reportId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: newUserId })
      });
      if (res.ok) {
        setReports(reports.map(r => 
          r.id === reportId 
            ? { ...r, assigned_to_id: newUserId, assigned_to_name: team.find(t => t.id === newUserId)?.nombre_completo || r.assigned_to_name } 
            : r
        ));
      } else {
        const data = await res.json();
        alert(data.error || "No se pudo asignar");
      }
    } catch (err) {
      alert("Error de red al asignar");
    }
  };

  const getInitials = (name: string) => {
    if (!name) return 'SA';
    const parts = name.split(' ');
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return name.substring(0, 2).toUpperCase();
  };

  const ReportCard = ({ report, status }: { report: Report, status: string }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [tempName, setTempName] = useState(report.nombre);

    const handleNameChange = async (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.stopPropagation();
        try {
          if (report.id < 0) {
            await db.cachedReports.update(report.id, { _report_name: tempName });
          } else {
            const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/rename/${report.id}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ nombre: tempName })
            });
            if (!res.ok) throw new Error("No se pudo renombrar en servidor");
          }
          setReports(prev => prev.map(r => r.id === report.id ? { ...r, nombre: tempName } : r));
        } catch (err) {
          alert("Error al guardar el nombre. Si está offline, asegúrese de editar un documento offline.");
        }
        setIsEditing(false);
      } else if (e.key === 'Escape') {
        e.stopPropagation();
        setTempName(report.nombre);
        setIsEditing(false);
      }
    };

    return (
      <div 
        onClick={() => navigate(`/capture/${report.id}`)}
        className="bg-white rounded-lg p-4 shadow-sm border border-gray-100 cursor-pointer hover:shadow-md transition-shadow active:cursor-grabbing group"
      >
        <div className="flex justify-between items-start mb-2">
          <span className="text-xs font-semibold text-corporate-blue bg-blue-50 px-2 py-1 rounded">
            REQ-{report.id.toString().padStart(3, '0')}
          </span>
          <div className="flex items-center gap-2">
            <button 
              onClick={(e) => handleClone(e, report.id)} 
              className="text-gray-400 hover:text-corporate-blue transition-colors bg-white hover:bg-blue-50 p-1.5 rounded-md" 
              title="Clonar reporte"
            >
              <Copy size={14} />
            </button>
            <span className="text-xs text-gray-400">{report.fecha_actualizacion}</span>
          </div>
        </div>
        
        <div onClick={e => e.stopPropagation()}>
          {isEditing ? (
            <input 
              autoFocus
              className="font-medium text-gray-900 leading-snug w-full border-b border-corporate-blue outline-none"
              value={tempName}
              onChange={e => setTempName(e.target.value)}
              onKeyDown={handleNameChange}
              onBlur={() => setIsEditing(false)}
            />
          ) : (
            <h4 
              className="font-medium text-gray-900 leading-snug hover:text-corporate-blue transition-colors"
              onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
              title="Haz clic para renombrar"
            >
              {report.nombre}
            </h4>
          )}
        </div>

        <div className="mt-3 flex items-center justify-between gap-2">
          <div 
            className="w-6 h-6 shrink-0 rounded-full bg-blue-100 border-2 border-white shadow-sm flex items-center justify-center text-xs font-bold text-corporate-blue" 
            title={report.assigned_to_name}
          >
            {getInitials(report.assigned_to_name)}
          </div>
          
          <div className="flex-1" onClick={e => e.stopPropagation()}>
            <select 
              className="text-xs w-full bg-gray-50 border border-gray-200 rounded p-1 text-gray-600 outline-none hover:border-corporate-blue focus:border-corporate-blue transition-colors"
              value={report.assigned_to_id || ''}
              onChange={(e) => handleAssign(e, report.id)}
            >
              <option value="" disabled>Asignar a...</option>
              {team.map(t => (
                <option key={t.id} value={t.id}>{t.nombre_completo}</option>
              ))}
            </select>
          </div>

          <span className="text-xs font-medium text-gray-500 shrink-0">{report.porcentaje_avance}%</span>
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
    );
  };

  const Column = ({ title, status, countClass }: { title: string, status: string, countClass: string }) => (
    <div className="w-80 flex flex-col bg-gray-50/50 rounded-xl p-4 border border-gray-200 shadow-sm shrink-0">
      <h3 className="font-semibold text-gray-700 flex items-center justify-between mb-4">
        {title}
        <span className={`${countClass} text-xs py-1 px-2 rounded-full`}>{getStatusCount(status)}</span>
      </h3>
      <div className="space-y-3 flex-1 overflow-y-auto">
        {getReportsByStatus(status).map(report => (
          <ReportCard key={report.id} report={report} status={status} />
        ))}
      </div>
    </div>
  );

  if (loading) return <div className="p-8">Cargando tablero...</div>;
  if (error && reports.length === 0) return <div className="p-8 text-red-500">{error}</div>;

  const misReportes = reports.filter(r => r.assigned_to_id === user?.id).length;
  const terminados = getStatusCount('terminado');
  const enEspera = getStatusCount('por_hacer');
  // Asumiremos retrasados como 'pendiente' por simplicidad, o se puede calcular por fecha.
  const retrasados = getStatusCount('pendiente');

  return (
    <div className="h-full flex flex-col">
      {/* Dashboard de Métricas Rápidas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-blue-50 text-corporate-blue rounded-xl"><UserIcon size={20} /></div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Mis Asignados</p>
            <p className="text-2xl font-bold text-gray-900">{misReportes}</p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-gray-50 text-gray-600 rounded-xl"><Clock size={20} /></div>
          <div>
            <p className="text-sm text-gray-500 font-medium">En Espera</p>
            <p className="text-2xl font-bold text-gray-900">{enEspera}</p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-yellow-50 text-yellow-600 rounded-xl"><AlertTriangle size={20} /></div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Con Problemas</p>
            <p className="text-2xl font-bold text-gray-900">{retrasados}</p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-green-50 text-green-600 rounded-xl"><CheckCircle size={20} /></div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Terminados</p>
            <p className="text-2xl font-bold text-gray-900">{terminados}</p>
          </div>
        </div>
      </div>

      <div className="mb-6 flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            Tablero de Producción
            {error && <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full font-normal">Offline</span>}
          </h2>
          <p className="text-gray-500 mt-1">Arrastra o haz clic para gestionar el estado de los documentos.</p>
        </div>
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
