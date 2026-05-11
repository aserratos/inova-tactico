import { apiFetch } from '../lib/api';
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { db } from '../lib/db';
import { FileText, Search, PlusCircle, Building2, X, ChevronRight, CheckCircle2, RefreshCw } from 'lucide-react';

interface Template {
  id: number;
  nombre: string;
}

interface Customer {
  id: number;
  nombre_empresa: string;
  rfc: string | null;
  contacto_principal: string | null;
  erp_source: string | null;
}

const API = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function TemplateSelector() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState('');
  const [customerSearch, setCustomerSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  // Modal de selección de cliente
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Cargar plantillas
    apiFetch(`${API}/api/templates`, { credentials: 'include' })
      .then(res => res.json())
      .then(async data => {
        const t = data.templates || [];
        setTemplates(t);
        setLoading(false);
        if (t.length > 0) {
          await db.cachedTemplates.bulkPut(t);
        }
      })
      .catch(async () => {
        // Fallback offline
        const localTemplates = await db.cachedTemplates.toArray();
        setTemplates(localTemplates);
        setLoading(false);
      });

    // Cargar clientes para el selector
    apiFetch(`${API}/api/customers`, { credentials: 'include' })
      .then(res => res.json())
      .then(async data => {
        const c = data.customers || [];
        setCustomers(c);
        if (c.length > 0) {
          await db.cachedCustomers.bulkPut(c);
        }
      })
      .catch(async () => {
        const localCustomers = await db.cachedCustomers.toArray();
        setCustomers(localCustomers);
      });
  }, []);

  // Cuando se abre el modal, enfocar la búsqueda
  useEffect(() => {
    if (selectedTemplate) {
      setTimeout(() => searchRef.current?.focus(), 100);
    }
  }, [selectedTemplate]);

  const handlePickTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setSelectedCustomer(null);
    setCustomerSearch('');
  };

  const handleStartReport = async () => {
    if (!selectedTemplate) return;
    setStarting(true);
    
    if (!navigator.onLine) {
      // Flujo Offline
      const fakeId = -Date.now();
      const customerData = selectedCustomer ? {
        nombre_empresa: selectedCustomer.nombre_empresa,
        rfc: selectedCustomer.rfc || '',
        contacto_principal: selectedCustomer.contacto_principal || '',
        cliente: selectedCustomer.nombre_empresa,
        empresa: selectedCustomer.nombre_empresa,
      } : {};

      if (Object.keys(customerData).length > 0) {
        sessionStorage.setItem(`prefill_${fakeId}`, JSON.stringify(customerData));
      }

      // Crear reporte "fantasma" en IndexedDB para que ReportCapture pueda abrirlo
      const reportNombre = `Reporte de ${selectedTemplate.nombre}` + (selectedCustomer ? ` — ${selectedCustomer.nombre_empresa}` : '');
      
      await db.cachedReports.put({
        id: fakeId,
        template_id: selectedTemplate.id,
        customer_id: selectedCustomer?.id || null,
        nombre: reportNombre,
        status: 'por_hacer',
        porcentaje_avance: 0,
        comentarios: '',
        data_json: '{}',
        updated_at: new Date().toISOString(),
        template_name: selectedTemplate.nombre
      });

      setStarting(false);
      navigate(`/capture/${fakeId}`);
      return;
    }

    // Flujo Online
    try {
      const body: any = { customer_id: selectedCustomer?.id || null };
      const res = await apiFetch(`${API}/api/report/start/${selectedTemplate.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok && data.id) {
        // Guardar customer_data en sessionStorage para que ReportCapture lo use para prellenar
        if (data.customer_data && Object.keys(data.customer_data).length > 0) {
          sessionStorage.setItem(`prefill_${data.id}`, JSON.stringify(data.customer_data));
        }
        navigate(`/capture/${data.id}`);
      } else {
        alert(data.error || 'Error al iniciar reporte. Revisa tu conexión a internet.');
      }
    } catch (e) {
      alert('Error de red');
    } finally {
      setStarting(false);
    }
  };

  const filtered = templates.filter(t => t.nombre.toLowerCase().includes(search.toLowerCase()));
  const filteredCustomers = customers.filter(c =>
    c.nombre_empresa.toLowerCase().includes(customerSearch.toLowerCase()) ||
    (c.rfc && c.rfc.toLowerCase().includes(customerSearch.toLowerCase()))
  );

  if (loading) return <div className="p-8 text-center text-gray-500">Cargando biblioteca de plantillas...</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Nuevo Documento</h2>
        <p className="text-gray-500 mt-1">Selecciona un formato base para iniciar la captura de datos</p>
      </div>

      {/* Buscador de plantillas */}
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

      {/* Grid de plantillas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map(t => (
          <div
            key={t.id}
            onClick={() => handlePickTemplate(t)}
            className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md hover:border-corporate-blue transition-all cursor-pointer group"
          >
            <div className="w-12 h-12 bg-blue-50 text-corporate-blue rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <FileText size={24} />
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

      {/* ── Modal de selección de cliente ── */}
      {selectedTemplate && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm p-0 sm:p-4">
          <div className="bg-white w-full sm:max-w-lg rounded-t-3xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[92vh] animate-in slide-in-from-bottom-4 duration-300">

            {/* Header del modal */}
            <div className="p-5 border-b border-gray-100 flex items-start justify-between flex-shrink-0">
              <div>
                <p className="text-xs font-semibold text-corporate-blue uppercase tracking-wider mb-0.5">Nuevo reporte</p>
                <h3 className="text-lg font-bold text-gray-900 leading-tight">{selectedTemplate.nombre}</h3>
                <p className="text-sm text-gray-500 mt-1">¿Para qué empresa es este reporte?</p>
              </div>
              <button
                onClick={() => setSelectedTemplate(null)}
                className="p-2 rounded-full hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-700 ml-3 flex-shrink-0"
              >
                <X size={20} />
              </button>
            </div>

            {/* Buscador de clientes */}
            <div className="px-5 py-3 border-b border-gray-100 flex-shrink-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                <input
                  ref={searchRef}
                  type="text"
                  placeholder="Buscar por nombre o RFC..."
                  value={customerSearch}
                  onChange={e => setCustomerSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 focus:border-corporate-blue focus:ring-2 focus:ring-corporate-blue/20 outline-none text-sm transition-all"
                />
              </div>
            </div>

            {/* Lista de clientes */}
            <div className="overflow-y-auto flex-1 py-2">
              {/* Opción sin cliente */}
              <button
                onClick={() => setSelectedCustomer(null)}
                className={`w-full flex items-center gap-3 px-5 py-3 text-left transition-colors hover:bg-gray-50 ${!selectedCustomer ? 'bg-blue-50' : ''}`}
              >
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${!selectedCustomer ? 'bg-corporate-blue text-white' : 'bg-gray-100 text-gray-400'}`}>
                  <RefreshCw size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-700">Sin empresa asociada</p>
                  <p className="text-xs text-gray-400">Continuar sin vincular a un cliente</p>
                </div>
                {!selectedCustomer && <CheckCircle2 size={18} className="text-corporate-blue flex-shrink-0" />}
              </button>

              {filteredCustomers.length > 0 && (
                <div className="px-5 pt-2 pb-1">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Directorio ({filteredCustomers.length})</p>
                </div>
              )}

              {filteredCustomers.map(customer => (
                <button
                  key={customer.id}
                  onClick={() => setSelectedCustomer(customer)}
                  className={`w-full flex items-center gap-3 px-5 py-3 text-left transition-colors hover:bg-gray-50 ${selectedCustomer?.id === customer.id ? 'bg-blue-50' : ''}`}
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${selectedCustomer?.id === customer.id ? 'bg-corporate-blue text-white' : 'bg-purple-50 text-purple-600'}`}>
                    <Building2 size={16} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{customer.nombre_empresa}</p>
                    <p className="text-xs text-gray-400 truncate">
                      {customer.rfc || 'Sin RFC'}
                      {customer.erp_source === 'odoo' && (
                        <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-purple-100 text-purple-700">Odoo</span>
                      )}
                    </p>
                  </div>
                  {selectedCustomer?.id === customer.id && <CheckCircle2 size={18} className="text-corporate-blue flex-shrink-0" />}
                </button>
              ))}

              {filteredCustomers.length === 0 && customerSearch && (
                <div className="px-5 py-6 text-center text-gray-400 text-sm">
                  No se encontró ninguna empresa con ese nombre o RFC.
                </div>
              )}

              {customers.length === 0 && !customerSearch && (
                <div className="px-5 py-4 text-center text-gray-400 text-sm">
                  <p>No hay clientes en el directorio.</p>
                  <p className="text-xs mt-1">Ve a <strong>Directorio</strong> → <strong>Sincronizar Odoo</strong> para importarlos.</p>
                </div>
              )}
            </div>

            {/* Footer con confirmación */}
            <div className="p-5 border-t border-gray-100 flex-shrink-0">
              {selectedCustomer && (
                <div className="flex items-center gap-2 mb-3 px-3 py-2 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700">
                  <CheckCircle2 size={15} className="flex-shrink-0" />
                  <span className="font-medium truncate">
                    Se precargarán datos de <strong>{selectedCustomer.nombre_empresa}</strong>
                  </span>
                </div>
              )}
              <button
                onClick={handleStartReport}
                disabled={starting}
                className="w-full flex items-center justify-center gap-2 bg-corporate-blue text-white py-3 px-6 rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {starting ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <ChevronRight size={20} />
                )}
                {starting ? 'Iniciando...' : 'Iniciar Captura'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
