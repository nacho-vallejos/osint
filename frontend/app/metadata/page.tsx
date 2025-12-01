'use client';

import { useState } from 'react';
import { Upload, FileText, Image as ImageIcon, MapPin, Calendar, User, Camera, X } from 'lucide-react';
import Link from 'next/link';

interface MetadataResult {
  success: boolean;
  filename: string;
  file_size_mb: number;
  file_extension: string;
  metadata?: any;
  triangulation?: {
    available: boolean;
    type: string;
    location: {
      latitude: number;
      longitude: number;
      google_maps_url: string;
      coordinates_string: string;
      altitude?: number;
    };
    suggestion: string;
  };
  error?: string;
  supported_types?: string[];
}

export default function MetadataExtractorPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MetadataResult | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setResult(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setResult(null);
    }
  };

  const handleExtract = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://localhost:8000/api/v1/metadata/extract', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error extracting metadata:', error);
      setResult({
        success: false,
        filename: selectedFile.name,
        file_size_mb: 0,
        file_extension: '',
        error: 'Error de conexión con el servidor'
      });
    } finally {
      setLoading(false);
    }
  };

  const renderImageMetadata = (metadata: any) => {
    if (!metadata) return null;

    return (
      <div className="space-y-6">
        {/* Image Info */}
        <div>
          <h4 className="text-lg font-semibold text-cyan-400 mb-3 flex items-center gap-2">
            <ImageIcon className="w-5 h-5" />
            Información de Imagen
          </h4>
          <div className="bg-slate-900 rounded-lg p-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">Formato:</span>
              <span className="text-white font-mono">{metadata.format}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Dimensiones:</span>
              <span className="text-white">{metadata.size?.width} × {metadata.size?.height} px</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Megapixeles:</span>
              <span className="text-white">{metadata.size?.megapixels} MP</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Modo de Color:</span>
              <span className="text-white">{metadata.mode}</span>
            </div>
          </div>
        </div>

        {/* Camera Info */}
        {metadata.camera && (metadata.camera.make || metadata.camera.model) && (
          <div>
            <h4 className="text-lg font-semibold text-purple-400 mb-3 flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Información de Cámara
            </h4>
            <div className="bg-slate-900 rounded-lg p-4 space-y-2">
              {metadata.camera.make && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Fabricante:</span>
                  <span className="text-white">{metadata.camera.make}</span>
                </div>
              )}
              {metadata.camera.model && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Modelo:</span>
                  <span className="text-white">{metadata.camera.model}</span>
                </div>
              )}
              {metadata.camera.software && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Software:</span>
                  <span className="text-white">{metadata.camera.software}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Capture Info */}
        {metadata.capture_info && metadata.capture_info.datetime && (
          <div>
            <h4 className="text-lg font-semibold text-green-400 mb-3 flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Información de Captura
            </h4>
            <div className="bg-slate-900 rounded-lg p-4 space-y-2">
              {metadata.capture_info.datetime_original && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Fecha Original:</span>
                  <span className="text-white font-mono">{metadata.capture_info.datetime_original}</span>
                </div>
              )}
              {metadata.capture_info.iso && (
                <div className="flex justify-between">
                  <span className="text-gray-400">ISO:</span>
                  <span className="text-white">{metadata.capture_info.iso}</span>
                </div>
              )}
              {metadata.capture_info.focal_length && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Distancia Focal:</span>
                  <span className="text-white">{metadata.capture_info.focal_length}</span>
                </div>
              )}
              {metadata.capture_info.exposure_time && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Tiempo de Exposición:</span>
                  <span className="text-white">{metadata.capture_info.exposure_time}</span>
                </div>
              )}
              {metadata.capture_info.f_number && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Apertura:</span>
                  <span className="text-white">f/{metadata.capture_info.f_number}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* GPS Location */}
        {result?.triangulation?.available && (
          <div className="bg-gradient-to-br from-green-500/20 to-cyan-500/20 border border-green-500/50 rounded-lg p-6">
            <h4 className="text-lg font-semibold text-green-300 mb-3 flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              📍 GPS Location Found!
            </h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-300">Latitud:</span>
                <span className="text-white font-mono">{result.triangulation.location.latitude.toFixed(6)}°</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Longitud:</span>
                <span className="text-white font-mono">{result.triangulation.location.longitude.toFixed(6)}°</span>
              </div>
              {result.triangulation.location.altitude && (
                <div className="flex justify-between">
                  <span className="text-gray-300">Altitud:</span>
                  <span className="text-white">{result.triangulation.location.altitude} m</span>
                </div>
              )}
              <div className="mt-4">
                <a
                  href={result.triangulation.location.google_maps_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors text-center"
                >
                  🗺️ Abrir en Google Maps
                </a>
              </div>
              <p className="text-sm text-gray-400 text-center mt-2">
                {result.triangulation.suggestion}
              </p>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderDocumentMetadata = (metadata: any) => {
    if (!metadata) return null;

    return (
      <div className="space-y-6">
        <div>
          <h4 className="text-lg font-semibold text-cyan-400 mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Información del Documento
          </h4>
          <div className="bg-slate-900 rounded-lg p-4 space-y-2">
            {metadata.num_pages && (
              <div className="flex justify-between">
                <span className="text-gray-400">Páginas:</span>
                <span className="text-white">{metadata.num_pages}</span>
              </div>
            )}
            {metadata.encrypted !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-400">Cifrado:</span>
                <span className={metadata.encrypted ? "text-yellow-400" : "text-green-400"}>
                  {metadata.encrypted ? "Sí" : "No"}
                </span>
              </div>
            )}
          </div>
        </div>

        {metadata.metadata && Object.keys(metadata.metadata).length > 0 && (
          <div>
            <h4 className="text-lg font-semibold text-purple-400 mb-3 flex items-center gap-2">
              <User className="w-5 h-5" />
              Metadatos del Autor
            </h4>
            <div className="bg-slate-900 rounded-lg p-4 space-y-2">
              {metadata.metadata.author && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Autor:</span>
                  <span className="text-white">{metadata.metadata.author}</span>
                </div>
              )}
              {metadata.metadata.creator && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Creador:</span>
                  <span className="text-white">{metadata.metadata.creator}</span>
                </div>
              )}
              {metadata.metadata.producer && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Productor:</span>
                  <span className="text-white">{metadata.metadata.producer}</span>
                </div>
              )}
              {metadata.metadata.last_modified_by && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Última modificación:</span>
                  <span className="text-white">{metadata.metadata.last_modified_by}</span>
                </div>
              )}
              {metadata.metadata.title && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Título:</span>
                  <span className="text-white">{metadata.metadata.title}</span>
                </div>
              )}
              {(metadata.metadata.creation_date || metadata.metadata.created) && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Fecha de creación:</span>
                  <span className="text-white font-mono">
                    {metadata.metadata.creation_date || metadata.metadata.created}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center text-cyan-400 hover:text-cyan-300 mb-4"
          >
            ← Volver al inicio
          </Link>
          <h1 className="text-4xl font-bold text-white mb-2">
            📄 Extractor de Metadatos
          </h1>
          <p className="text-gray-400">
            Sube imágenes o documentos para extraer metadatos forenses incluyendo GPS, autor, fechas y más
          </p>
        </div>

        {/* Upload Area */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-8 mb-8">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive
                ? 'border-cyan-500 bg-cyan-500/10'
                : 'border-slate-600 hover:border-slate-500'
            }`}
          >
            <Upload className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            
            {selectedFile ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center gap-3 text-white">
                  <FileText className="w-5 h-5 text-cyan-400" />
                  <span className="font-semibold">{selectedFile.name}</span>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="p-1 hover:bg-slate-700 rounded"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-gray-400 text-sm">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <button
                  onClick={handleExtract}
                  disabled={loading}
                  className="px-8 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 disabled:text-gray-500 text-white font-semibold rounded-lg transition-colors"
                >
                  {loading ? 'Extrayendo...' : '🔍 Extraer Metadatos'}
                </button>
              </div>
            ) : (
              <>
                <p className="text-gray-300 text-lg mb-2">
                  Arrastra un archivo aquí o haz clic para seleccionar
                </p>
                <p className="text-gray-500 text-sm mb-4">
                  Formatos soportados: JPG, PNG, TIFF, PDF, DOCX
                </p>
                <label className="inline-block px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg cursor-pointer transition-colors">
                  Seleccionar Archivo
                  <input
                    type="file"
                    onChange={handleFileChange}
                    accept=".jpg,.jpeg,.png,.tiff,.tif,.pdf,.docx,.doc"
                    className="hidden"
                  />
                </label>
              </>
            )}
          </div>
        </div>

        {/* Results */}
        {result && (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-8">
            {result.success ? (
              <div className="space-y-6">
                {/* File Info */}
                <div>
                  <h3 className="text-2xl font-bold text-white mb-4">
                    ✅ Metadatos Extraídos
                  </h3>
                  <div className="bg-slate-900 rounded-lg p-4 space-y-2 mb-6">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Archivo:</span>
                      <span className="text-white font-mono">{result.filename}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Tamaño:</span>
                      <span className="text-white">{result.file_size_mb} MB</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Tipo:</span>
                      <span className="text-white uppercase">{result.file_extension}</span>
                    </div>
                  </div>
                </div>

                {/* Type-specific metadata */}
                {result.metadata?.file_type === 'image' && renderImageMetadata(result.metadata)}
                {(result.metadata?.file_type === 'pdf' || result.metadata?.file_type === 'docx') && 
                  renderDocumentMetadata(result.metadata)}
              </div>
            ) : (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6">
                <h3 className="text-xl font-bold text-red-300 mb-2">❌ Error</h3>
                <p className="text-red-200">{result.error}</p>
                {result.supported_types && (
                  <p className="text-gray-400 text-sm mt-2">
                    Formatos soportados: {result.supported_types.join(', ')}
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
