import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Camera, Mic, MicOff, Save, CheckCircle2, ChevronLeft } from 'lucide-react';

interface ReportDetails {
  id: number;
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
  
  // State para el micrófono (cuál variable está grabando)
  const [recordingVar, setRecordingVar] = useState<string | null>(null);
  
  const recognitionRef = useRef<any>(null);
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  useEffect(() => {
    if (!id) return;
    fetch(`http://localhost:8001/api/report/${id}`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        setReport(data);
        setFormData(data.saved_data || {});
        
        // Populate existing image previews
        const previews: Record<string, string> = {};
        data.image_vars.forEach((v: string) => {
          if (data.saved_data[v]) {
            previews[v] = `http://localhost:8001/report/media/${id}/${v}`;
          }
        });
        setImagePreviews(previews);
        setLoading(false);
      });

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

  const handleSave = async () => {
    if (!id) return;
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

    try {
      const res = await fetch(`http://localhost:8001/api/report/save/${id}`, {
        method: 'POST',
        body: formDataPayload,
        credentials: 'include'
      });
      
      if (res.ok) {
        alert("Guardado exitosamente");
        navigate('/');
      } else {
        alert("Error al guardar");
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
      </div>

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
