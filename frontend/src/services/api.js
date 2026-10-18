import axios from 'axios';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';


const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});


const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const auditService = {
    // Encola el escaneo (202) y hace polling del job hasta que termina.
    startScan: async (target, stealth, ports, { pollIntervalMs = 2000, timeoutMs = 600000 } = {}) => {
        try {
            const { data } = await api.post('/api/scan', {
                target,
                stealth: parseInt(stealth),
                ports: parseInt(ports)
            });
            const jobId = data.job_id;
            const deadline = Date.now() + timeoutMs;

            while (Date.now() < deadline) {
                await sleep(pollIntervalMs);
                const { data: job } = await api.get(`/api/scan/${jobId}`);
                if (job.status === 'done') return job;
                if (job.status === 'error') {
                    throw job.error || 'El motor de auditoría reportó un error';
                }
            }
            throw 'Tiempo de espera agotado esperando al motor de auditoría';
        } catch (error) {
            console.error("Falla en la comunicación con el motor NSGA-II:", error);
            throw error.response?.data?.detail || error || "Error en el motor de auditoría";
        }
    },

    
    getReports: async () => {
        const response = await api.get('/api/reports/');
        return response.data;
    }
};


export const reportService = {
    
    getReportContent: async (filename) => {
        const response = await api.get(`/api/reports/${filename}`);
        return response.data; 
    },

    
    downloadPDF: async (filename) => {
        try {
            const response = await api.get(`/api/reports/${filename}/pdf`, { 
                responseType: 'blob' 
            });
            
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            
            
            const pdfName = filename.replace('.md', '.pdf');
            link.setAttribute('download', pdfName);
            
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error("Error en la descarga del binario PDF:", error);
            alert("No se pudo generar el PDF. Verifica que las dependencias de renderizado estén activas.");
        }
    },

    
    getYaraRule: async (target) => {
        const response = await api.get(`/api/rules/${target}`);
        return response.data;
    },

    getStrategy: async (target) => {
        try {
            const response = await api.get(`/api/strategy/${target}`);
            return response.data;
        } catch (error) {
            console.warn(`No se encontró estrategia para ${target}`, error);
            throw error; 
        }
    }
};


export const TopologyService = {
    getTopology: async (target) => {
        try {
            const response = await api.get(`/api/topology/${target}`);
            return response.data;
        } catch (error) {
            console.error(`Error al obtener la topología para ${target}:`, error);
            throw error;
        }
    }
};


export const NmapTecniqueService = {
  runActiveScan: async (target, stealth, ports) => {
    try {
      const response = await api.post(`/api/nmap`, {
        target: target,
        stealth: parseInt(stealth),
        ports: parseInt(ports)
      });

      return response.data;
    }
    catch (error) {
      console.error(`Error al ejecutar el escaneo activo para ${target}:`, error);
      throw error;
    }
  }
};


export const CVEService = {
    getCVEs: async (serviceBanner) => {
        try {
            const response = await api.get(`/api/cve/${encodeURIComponent(serviceBanner)}`);
            return response.data;
        } catch (error) {
            console.error(`Error al obtener CVEs para ${serviceBanner}:`, error);
            throw error;
        }
    }
};

export const StrategyService = {
    getStrategy: async (target, stealth, findings) => {
        try {
            const response = await api.post(`/api/strategy/live`, { target, stealth, findings });
            return response.data;
        } catch (error) {
            console.error(`Error al obtener la estrategia para ${target}:`, error);
            throw error;
        }
    }
};


export const PersistenceService = {
    syncData: async (data) => {
        try {
            const response = await api.post('/api/persistence/sync', data);
            return response.data;
        } catch (error) {
            console.error("Error al sincronizar datos con la Bóveda:", error);
            throw error;
        }
    }
};


export const LatestAudit = {
    getLatestScans: async () => {
        try {
            const response = await api.get('/api/persistence/latest');
            return response.data;
        } catch (error) {
            console.error("Error al obtener los últimos escaneos:", error);
            throw error;
        }   
    }
};

export const DeltaService = {
    getDelta: async (target) => {
        try {
            const response = await api.get(`/api/delta/${target}`);
            return response.data;
        } catch (error) {
            console.error(`Error al obtener el delta para ${target}:`, error);
            throw error;
        }
    }
};