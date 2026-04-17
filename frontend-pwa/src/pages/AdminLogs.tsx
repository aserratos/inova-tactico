import { useState, useEffect } from 'react';
import { Activity, ShieldAlert, MonitorSmartphone, ArrowRight } from 'lucide-react';

interface LogData {
  id: number;
  user_email: string;
  action: string;
  details: string;
  ip_address: string;
  timestamp: string;
}

export default function AdminLogs() {
  const [logs, setLogs] = useState<LogData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/auth/api/admin/logs', { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data.logs) setLogs(data.logs);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, []);

  const getActionIcon = (action: string) => {
    if (action.includes('LOGIN') || action.includes('LOGOUT')) return <ShieldAlert className="text-blue-500" size={16} />;
    if (action.includes('DELETE') || action.includes('ERROR')) return <ShieldAlert className="text-red-500" size={16} />;
    return <MonitorSmartphone className="text-gray-500" size={16} />;
  };

  const getActionColor = (action: string) => {
    if (action.includes('LOGIN')) return 'bg-blue-50 text-blue-700 border-blue-100';
    if (action.includes('DELETE')) return 'bg-red-50 text-red-700 border-red-100';
    if (action.includes('CREATE') || action.includes('API')) return 'bg-purple-50 text-purple-700 border-purple-100';
    return 'bg-gray-50 text-gray-700 border-gray-100';
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Recopilando auditoría forense...</div>;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <Activity className="mr-3 text-corporate-blue" />
          Bitácora de Auditoría
        </h2>
        <p className="text-gray-500 mt-1">Registro inmutable de actividades en el Centro de Comando Táctico.</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold">
                <th className="px-6 py-4 w-48">Fecha y Hora</th>
                <th className="px-6 py-4">Usuario</th>
                <th className="px-6 py-4">Acción / Tipo</th>
                <th className="px-6 py-4 w-1/3">Detalle Técnico</th>
                <th className="px-6 py-4 text-right">Origen (IP)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 text-sm text-gray-500 font-mono whitespace-nowrap">
                    {log.timestamp}
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-semibold text-gray-900 text-sm">{log.user_email}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      {getActionIcon(log.action)}
                      <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-sm text-gray-700 flex items-center">
                      <ArrowRight size={14} className="mr-2 text-gray-400 shrink-0" />
                      {log.details}
                    </p>
                  </td>
                  <td className="px-6 py-4 text-right text-xs text-gray-400 font-mono">
                    {log.ip_address}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {logs.length === 0 && <div className="p-8 text-center text-gray-500">No hay registros en la bitácora.</div>}
        </div>
      </div>
    </div>
  );
}
