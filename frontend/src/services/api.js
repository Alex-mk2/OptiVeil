import axios from 'axios';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';


const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});


export const auditService = {
    startScan: async (target, stealth, ports) => {
        try {
            const response = await api.post('/api/scan', { 
                target, 
                stealth: parseInt(stealth), 
                ports: parseInt(ports) 
            });
            return response.data;
        } catch (error) {
            console.error("Falla en la comunicación con el motor NSGA-II:", error);
            throw error.response?.data?.detail || "Error en el motor de auditoría";
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
    }
};