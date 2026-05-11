import { apiFetch } from '../lib/api';
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Camera, Mic, MicOff, Save, ChevronLeft, Sparkles, X } from 'lucide-react';
import { db } from '../lib/db';

interface ReportDetails {
  id: number;
  template_id?: number;
  customer_id?: number | null;
  nombre: string;
  status: string;
  template_name: string;
  text_vars: string[];
  image_vars: string[];
  saved_data: Record<string, string>;
}

export default function ReportCapture() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // States para los formularios
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [imageFiles, setImageFiles] = useState<Record<string, File>>({});
  const [imagePreviews, setImagePreviews] = useState<Record<string, string>>({});
  
  // Banner de datos prellenados desde cliente
  const [prefillBanner, setPrefillBanner] = useState<string | null>(null);
  
  // State para el micrófono (cuál variable está grabando)
  const [recordingVar, setRecordingVar] = useState<string | null>(null);
  
  // OCR / IA Vision
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<string | null>(null);
  const ocrInputRef = useRef<HTMLInputElement | null>(null);

  const recognitionRef = useRef<any>(null);
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  useEffect(() => {
    const loadReport = async () => {
      if (!id) return;
      
      try {
        if (!navigator.onLine) throw new Error('Offline');
        
        const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/${id}`, { credentials: 'include' });
        if (!res.ok) throw new Error('Fetch failed');
        const data = await res.json();
        
        setReport(data);
        const savedData = data.saved_data || {};

        // Prefill: combinar datos del cliente guardados en sessionStorage con los del reporte
        const prefillRaw = sessionStorage.getItem(`prefill_${id}`);
        if (prefillRaw) {
          sessionStorage.removeItem(`prefill_${id}`);
          try {
            const prefill: Record<string, string> = JSON.parse(prefillRaw);
            // Inyectar solo en campos que estén vacíos en saved_data y que existan como variable en la plantilla
            const allVars = [...(data.text_vars || []), ...(data.image_vars || [])];
            const injected: string[] = [];
            const merged = { ...savedData };
            for (const varName of allVars) {
              if (!merged[varName] && prefill[varName]) {
                merged[varName] = prefill[varName];
                injected.push(varName.replace(/_/g, ' '));
              }
            }
            if (injected.length > 0) {
              setPrefillBanner(`✓ Datos prellenados desde cliente: ${injected.join(', ')}`);
            }
            setFormData(merged);
          } catch {
            setFormData(savedData);
          }
        } else {
          setFormData(savedData);
        }
        
        // Populate existing image previews from saved R2 keys
        const previews: Record<string, string> = {};
        for (const v of (data.image_vars || [])) {
          if (data.saved_data?.[v]) {
            // Solicitar URL firmada al backend para la imagen guardada en R2
            previews[v] = `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/${id}/media/${v}`;
          }
        }
        setImagePreviews(previews);
        setLoading(false);
      } catch (err) {
        // Fallback a IndexedDB (Offline Mode)
        console.log('Cargando reporte desde IndexedDB (Offline)...');
        import('../lib/db').then(({ db }) => {
          db.cachedReports.get(Number(id)).then(cached => {
            if (cached) {
              const savedData = JSON.parse(cached.data_json || '{}');
              setReport({
                id: cached.id,
                template_id: cached.template_id,
                customer_id: cached.customer_id,
                nombre: cached.nombre,
                status: cached.status,
                template_name: cached.template_name || 'Plantilla Offline',
                text_vars: cached.text_vars || [],
                image_vars: cached.image_vars || [],
                saved_data: savedData
              });
              setFormData(savedData);
              setImagePreviews({}); // Imágenes no están cacheadas por ahora (requeriría blob url)
              setLoading(false);
            } else {
              console.error('Reporte no encontrado en caché local');
            }
          });
        });
      }
    };
    
    loadReport();

    // Configurar Speech Recognition
    if ('webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'es-MX';
    }
  }, [id]);

  const handleTextChange = (varName: string, value: string) => {
    setFormData(prev => ({ ...prev, [varName]: value }));
  };

  const toggleRecording = (varName: string) => {
    if (!recognitionRef.current) {
      alert("Tu navegador no soporta el dictado por voz.");
      return;
    }

    if (recordingVar === varName) {
      // Parar
      recognitionRef.current.stop();
      setRecordingVar(null);
    } else {
      // Si había otro grabando, lo paramos
      if (recordingVar) recognitionRef.current.stop();
      
      // Iniciar nuevo
      setRecordingVar(varName);
      
      let finalTranscript = formData[varName] ? formData[varName] + ' ' : '';
      
      recognitionRef.current.onresult = (event: any) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
            handleTextChange(varName, finalTranscript);
          } else {
            interimTranscript += event.results[i][0].transcript;
            handleTextChange(varName, finalTranscript + interimTranscript);
          }
        }
      };
      
      recognitionRef.current.onend = () => {
        setRecordingVar(null);
      };
      
      recognitionRef.current.start();
    }
  };

  const handleImageCapture = (varName: string, file: File) => {
    setImageFiles(prev => ({ ...prev, [varName]: file }));
    
    // Crear preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreviews(prev => ({ ...prev, [varName]: e.target?.result as string }));
    };
    reader.readAsDataURL(file);
  };

  const triggerCamera = (varName: string) => {
    if (fileInputRefs.current[varName]) {
      fileInputRefs.current[varName]?.click();
    }
  };

  // --- OCR: Autollenar con IA ---
  const handleOcrScan = async (file: File) => {
    if (!report) return;
    setOcrLoading(true);
    setOcrResult(null);

    const payload = new FormData();
    payload.append('image', file);
    // Enviar los nombres de los campos de texto para que la IA sepa qué buscar
    payload.append('campos', JSON.stringify(report.text_vars));

    try {
      const res = await apiFetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/ocr/extract`,
        { method: 'POST', body: payload }
      );
      const data = await res.json();

      if (data.status === 'success' && data.data) {
        const filled = Object.keys(data.data).length;
        setFormData(prev => ({ ...prev, ...data.data }));
        if (filled > 0) {
          setOcrResult(`✅ IA extrajo ${filled} campo(s) del documento exitosamente.`);
        } else {
          setOcrResult('⚠️ La IA procesó el documento pero no encontró campos coincidentes.');
        }
      } else {
        // Mostrar el error real del servidor para diagnostico
        const errorMsg = data.error || data.message || JSON.stringify(data).slice(0, 200);
        setOcrResult(`❌ ${errorMsg}`);
      }
    } catch (e: any) {
      setOcrResult(`❌ Error de red: ${e?.message || 'sin detalles'}`);

    } finally {
      setOcrLoading(false);
    }
  };

  const handleSave = async () => {
    if (!id || !report) return;
    setSaving(true);
    
    const formDataPayload = new FormData();
    // 1. Agregar campos de texto
    Object.keys(formData).forEach(key => {
      formDataPayload.append(key, formData[key]);
    });
    
    // 2. Agregar archivos de imagen nuevos
    Object.keys(imageFiles).forEach(key => {
      formDataPayload.append(key, imageFiles[key]);
    });

    const isOfflineCreated = Number(id) < 0;
    if (isOfflineCreated) {
      if (report.template_id) formDataPayload.append('_template_id', String(report.template_id));
      if (report.customer_id) formDataPayload.append('_customer_id', String(report.customer_id));
    }

    const targetUrl = isOfflineCreated 
      ? `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/sync_offline_create`
      : `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/report/save/${id}`;

    try {
      if (!navigator.onLine) {
        // Modo Offline: Guardar en Dexie y salir
        const payloadObject: Record<string, any> = {};
        formDataPayload.forEach((value, key) => {
          payloadObject[key] = value;
        });

        await db.syncQueue.add({
          url: targetUrl,
          method: 'POST',
          payload: payloadObject,
          isFormData: true,
          timestamp: new Date().toISOString(),
          status: 'pending',
          retryCount: 0
        });

        // Update the cached report visually
        const cached = await db.cachedReports.get(Number(id));
        if (cached) {
          await db.cachedReports.update(Number(id), { status: 'terminado', porcentaje_avance: 100 });
        }

        alert("Sin conexión: Guardado en tu dispositivo. Se enviará a la nube al recuperar señal.");
        navigate('/');
        return;
      }

      const res = await apiFetch(targetUrl, {
        method: 'POST',
        body: formDataPayload,
        credentials: 'include'
      });
      
      if (res.ok) {
        alert("Guardado exitosamente");
        navigate('/');
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(`Error al guardar: ${errData.error || res.status}`);
      }
    } catch (e) {
      alert("Error de red al guardar");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Cargando formulario...</div>;
  if (!report) return <div className="p-8 text-red-500">Reporte no encontrado</div>;

  return (
    <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden pb-20 md:pb-0">
      {/* Header */}
      <div className="bg-corporate-dark px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center space-x-3">
          <button onClick={() => navigate('/')} className="text-gray-300 hover:text-white transition-colors">
            <ChevronLeft size={24} />
          </button>
          <div>
            <h2 className="text-white font-bold text-lg leading-tight">{report.nombre}</h2>
            <p className="text-blue-200 text-sm">{report.template_name}</p>
          </div>
        </div>
        {/* Botón OCR IA */}
        <button
          onClick={() => ocrInputRef.current?.click()}
          disabled={ocrLoading}
          className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-lg disabled:opacity-50"
          title="Autollenar con foto de documento"
        >
          {ocrLoading ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Sparkles size={16} />
          )}
          <span className="hidden sm:inline">{ocrLoading ? 'Leyendo...' : 'Autollenar IA'}</span>
        </button>
        {/* Input oculto para la imagen OCR */}
        <input
          type="file"
          accept="image/*"
          ref={ocrInputRef}
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.[0]) handleOcrScan(e.target.files[0]);
          }}
        />
      </div>

      {/* Banner de resultado OCR */}
      {ocrResult && (
        <div className={`mx-6 mt-4 px-4 py-3 rounded-lg text-sm font-medium flex items-center justify-between ${
          ocrResult.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' :
          ocrResult.startsWith('⚠️') ? 'bg-yellow-50 text-yellow-800 border border-yellow-200' :
          'bg-red-50 text-red-800 border border-red-200'
        }`}>
          <span>{ocrResult}</span>
          <button onClick={() => setOcrResult(null)}><X size={16} /></button>
        </div>
      )}

      {/* Banner de prefill desde cliente */}
      {prefillBanner && (
        <div className="mx-6 mt-4 px-4 py-3 rounded-lg text-sm font-medium flex items-center justify-between bg-purple-50 text-purple-800 border border-purple-200">
          <span>{prefillBanner}</span>
          <button onClick={() => setPrefillBanner(null)}><X size={16} /></button>
        </div>
      )}

      <div className="p-6 space-y-8">
        
        {/* TEXT VARIABLES */}
        {report.text_vars.length > 0 && (
          <div className="space-y-6">
            <h3 className="text-lg font-bold text-gray-900 border-b border-gray-100 pb-2">Datos y Hallazgos</h3>
            {report.text_vars.map((varName) => (
              <div key={varName} className="space-y-2">
                <label className="block text-sm font-semibold text-gray-700 capitalize">
                  {varName.replace(/_/g, ' ')}
                </label>
                <div className="relative">
                  <textarea
                    rows={3}
                    className={`w-full px-4 py-3 bg-gray-50 border rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-transparent transition-all outline-none resize-none ${recordingVar === varName ? 'border-blue-400 ring-2 ring-blue-100' : 'border-gray-200'}`}
                    placeholder="Describe los detalles aquí..."
                    value={formData[varName] || ''}
                    onChange={(e) => handleTextChange(varName, e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => toggleRecording(varName)}
                    className={`absolute bottom-3 right-3 p-2 rounded-full transition-all shadow-sm ${
                      recordingVar === varName 
                        ? 'bg-red-500 text-white animate-pulse' 
                        : 'bg-corporate-blue text-white hover:bg-blue-700'
                    }`}
                    title="Dictado por voz"
                  >
                    {recordingVar === varName ? <MicOff size={18} /> : <Mic size={18} />}
                  </button>
                </div>
                {recordingVar === varName && (
                  <p className="text-xs text-red-500 animate-pulse font-medium">Escuchando... (Presiona de nuevo para detener)</p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* IMAGE VARIABLES */}
        {report.image_vars.length > 0 && (
          <div className="space-y-6 pt-6">
            <h3 className="text-lg font-bold text-gray-900 border-b border-gray-100 pb-2">Evidencia Fotográfica</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {report.image_vars.map((varName) => (
                <div key={varName} className="bg-gray-50 rounded-xl border border-gray-200 p-4 flex flex-col items-center justify-center text-center">
                  <span className="text-sm font-semibold text-gray-700 mb-3 block capitalize">{varName.replace(/_/g, ' ')}</span>
                  
                  {imagePreviews[varName] ? (
                    <div className="relative w-full aspect-video rounded-lg overflow-hidden group">
                      <img src={imagePreviews[varName]} alt={varName} className="w-full h-full object-cover" />
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <button 
                          onClick={() => triggerCamera(varName)}
                          className="bg-white text-gray-900 px-4 py-2 rounded-lg font-medium text-sm flex items-center space-x-2"
                        >
                          <Camera size={16} />
                          <span>Retomar Foto</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => triggerCamera(varName)}
                      className="w-full aspect-video flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:text-corporate-blue hover:border-corporate-blue hover:bg-blue-50 transition-all group"
                    >
                      <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                        <Camera size={24} className="text-corporate-blue" />
                      </div>
                      <span className="font-medium text-sm">Abrir Cámara</span>
                    </button>
                  )}
                  
                  {/* Input oculto para la cámara */}
                  <input 
                    type="file" 
                    accept="image/*" 
                    capture="environment" // Fuerza a abrir la cámara trasera en móviles
                    ref={el => { fileInputRefs.current[varName] = el }}
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleImageCapture(varName, e.target.files[0]);
                      }
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      <div className="bg-gray-50 px-6 py-4 border-t border-gray-100 flex justify-end space-x-3 sticky bottom-0 z-10 md:static">
        <button 
          onClick={() => navigate('/')}
          className="px-6 py-2.5 rounded-lg font-medium text-gray-600 bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
        >
          Cancelar
        </button>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2.5 rounded-lg font-medium text-white bg-corporate-blue hover:bg-blue-700 shadow-md hover:shadow-lg transition-all flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Save size={20} />
          )}
          <span>{saving ? 'Guardando...' : 'Guardar y Salir'}</span>
        </button>
      </div>
    </div>
  );
}
