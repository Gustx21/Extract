import React, { useRef, useState } from 'react';

const URI = 'http://localhost:5000/processar';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState('xlsx');
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    } else {
      setFile(null);
    }
    setErro('');
  };

  const handleFormatChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormat(e.target.value);
  };

  const resetForm = () => {
    setFile(null);
    setLoading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!file) {
      setErro("Por favor, selecione um arquivo.");
      return;
    }

    setLoading(true);
    setErro('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('formato', format);

    try {
      const response = await fetch(URI, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.erro || 'Erro ao processar o arquivo');
      }

      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `relatorio_processado.${format}`);
      document.body.appendChild(link);
      link.click();
      
      link.remove();
      window.URL.revokeObjectURL(url);
      resetForm();
      
    } catch (err) {
      if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Ocorreu um erro inesperado.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans text-gray-900">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="text-center text-5xl font-bold tracking-tight text-gray-900 mb-8">
          Path of the stones
        </h2>

        <div className="bg-white py-8 px-4 shadow-sm sm:rounded-2xl sm:px-10 border border-gray-100">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Input de Arquivo */}
            <div>
              <label htmlFor="selectFile" className="block text-sm font-medium text-gray-700 mb-2">
                Arquivo de Origem
              </label>
              <input 
                id="selectFile"
                type="file" 
                accept=".xlsx, .xls, .csv, .parquet"
                onChange={handleFileChange} 
                ref={fileInputRef} 
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2.5 file:px-4
                  file:rounded-lg file:border-0
                  file:text-sm file:font-medium
                  file:bg-indigo-50 file:text-indigo-700
                  hover:file:bg-indigo-100 file:cursor-pointer
                  border border-gray-200 rounded-lg p-1 bg-gray-50/50
                  focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {/* Select de Formato */}
            <div>
              <label htmlFor="selectFormat" className="block text-sm font-medium text-gray-700 mb-2">
                Formato de Saída
              </label>
              <select 
                id="selectFormat" 
                value={format} 
                onChange={handleFormatChange} 
                className="block w-full rounded-lg border-gray-200 bg-gray-50/50 px-4 py-3 text-sm text-gray-700 
                  focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 
                  transition-colors"
              >
                <option value="xlsx">Excel (.xlsx)</option>
                <option value="csv">CSV (.csv)</option>
                <option value="parquet">Parquet (.parquet)</option>
              </select>
            </div>

            {/* Botão de Submit */}
            <button 
              type="submit" 
              disabled={loading || !file}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processando...
                </>
              ) : (
                'Processar e Baixar'
              )}
            </button>
          </form>

          {/* Mensagem de Erro */}
          {erro && (
            <div className="mt-6 bg-red-50 border border-red-100 rounded-lg p-4 flex items-start">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Erro na operação</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{erro}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;