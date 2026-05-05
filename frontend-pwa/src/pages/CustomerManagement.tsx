import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { Building2, Plus, User, Search, RefreshCw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface Customer {
  id: number;
  nombre_empresa: string;
  contacto_principal: string | null;
  rfc: string | null;
  external_erp_id: string | null;
  erp_source: string | null;
  created_at: string;
}

export default function CustomerManagement() {
  const { user } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    nombre_empresa: '',
    contacto_principal: '',
    rfc: ''
  });

  const fetchCustomers = async () => {
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/customers`);
      const data = await res.json();
      setCustomers(data.customers || []);
    } catch (error) {
      console.error('Failed to fetch customers', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [user]);

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/customers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.error) {
          throw new Error(data.error);
      }
      setShowModal(false);
      setFormData({ nombre_empresa: '', contacto_principal: '', rfc: '' });
      fetchCustomers();
    } catch (error: any) {
      alert(error.message || 'Error al crear cliente');
    }
  };

  const handleOdooSync = async () => {
    if (!confirm('¿Estás seguro de sincronizar los clientes desde Odoo? Esto podría tardar unos segundos.')) return;
    try {
      setLoading(true);
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/integrations/odoo/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({}) // Backend picks up g.org_id
      });
      const data = await res.json();
      if (data.error) {
        throw new Error(data.error);
      }
      alert(data.message || 'Sincronización completada exitosamente.');
      fetchCustomers();
    } catch (error: any) {
      alert(error.message || 'Error al conectar con Odoo. Verifica la configuración de tu Organización.');
      setLoading(false);
    }
  };

  const filteredCustomers = customers.filter(c => 
    c.nombre_empresa.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.rfc && c.rfc.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Directorio de Clientes</h1>
          <p className="text-sm text-gray-500 mt-1">
            Empresas con las que trabajamos. Base para asignar usuarios de portal o conectar con ERPs.
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleOdooSync}
            className="flex items-center space-x-2 bg-purple-50 text-purple-700 hover:bg-purple-100 px-4 py-2 rounded-xl transition-colors font-medium border border-purple-100"
          >
            <RefreshCw size={18} />
            <span>Sincronizar Odoo</span>
          </button>
          <button 
            onClick={() => setShowModal(true)}
            className="flex items-center space-x-2 bg-corporate-blue text-white hover:bg-blue-700 px-4 py-2 rounded-xl transition-colors font-medium shadow-sm hover:shadow"
          >
            <Plus size={18} />
            <span>Nueva Empresa</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Buscar por nombre o RFC..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 focus:border-corporate-blue focus:ring-1 focus:ring-corporate-blue outline-none transition-all text-sm"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Cargando directorio...</div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Empresa</th>
                  <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Contacto</th>
                  <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">RFC</th>
                  <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Origen</th>
                  <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Alta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredCustomers.length > 0 ? (
                  filteredCustomers.map(customer => (
                    <tr key={customer.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="p-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 rounded-xl bg-corporate-blue/10 flex items-center justify-center text-corporate-blue font-bold">
                            <Building2 size={20} />
                          </div>
                          <span className="font-medium text-gray-900">{customer.nombre_empresa}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center text-gray-600 text-sm">
                          <User size={16} className="mr-2 text-gray-400" />
                          {customer.contacto_principal || <span className="text-gray-400 italic">No asignado</span>}
                        </div>
                      </td>
                      <td className="p-4 text-sm text-gray-600">
                        {customer.rfc || '-'}
                      </td>
                      <td className="p-4">
                        {customer.erp_source === 'odoo' ? (
                           <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                             Odoo Sync
                           </span>
                        ) : (
                           <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                             Manual
                           </span>
                        )}
                      </td>
                      <td className="p-4 text-sm text-gray-500">
                        {customer.created_at}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-gray-500">
                      No hay clientes registrados que coincidan con la búsqueda.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal Nuevo Cliente */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-xl font-bold text-gray-900">Registrar Nueva Empresa</h2>
              <p className="text-sm text-gray-500 mt-1">Crea un cliente manualmente para asociarlo a reportes.</p>
            </div>
            <form onSubmit={handleCreateCustomer} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de la Empresa</label>
                <input 
                  type="text" 
                  required
                  value={formData.nombre_empresa}
                  onChange={(e) => setFormData({...formData, nombre_empresa: e.target.value})}
                  className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue transition-shadow outline-none"
                  placeholder="Ej. Acme Corp S.A. de C.V."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contacto Principal (Nombre)</label>
                <input 
                  type="text" 
                  value={formData.contacto_principal}
                  onChange={(e) => setFormData({...formData, contacto_principal: e.target.value})}
                  className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue transition-shadow outline-none"
                  placeholder="Ej. Juan Pérez"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">RFC</label>
                <input 
                  type="text" 
                  value={formData.rfc}
                  onChange={(e) => setFormData({...formData, rfc: e.target.value})}
                  className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue transition-shadow outline-none uppercase"
                  placeholder="ACM9012301A1"
                />
              </div>

              <div className="mt-6 flex gap-3 pt-2">
                <button 
                  type="button" 
                  onClick={() => setShowModal(false)}
                  className="flex-1 py-2.5 px-4 rounded-xl text-gray-700 font-medium hover:bg-gray-100 transition-colors"
                >
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  className="flex-1 py-2.5 px-4 rounded-xl bg-corporate-blue text-white font-medium hover:bg-blue-700 shadow-sm transition-all"
                >
                  Guardar Empresa
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
