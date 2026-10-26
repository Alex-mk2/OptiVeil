import { useState } from 'react';
import { auditService } from '../services/api';
import AuditForm from '../components/AuditForm';
import IntelligenceResults from '../components/IntelligenceResults';

function AuditDashboard() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [target, setTarget] = useState('');

  const handleScanSubmit = async (target, stealth, ports) => {
    setLoading(true);
    setError('');
    setResult(null);
    setTarget(target);

    try {
      const data = await auditService.startScan(target, stealth, ports);
      setResult(data);
    } catch (err) {
      console.error("Error en el escaneo:", err);
      setError('Error al conectar con el Core Engine. Verifica que FastAPI esté corriendo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <section className="lg:col-span-4 space-y-6">
        <AuditForm onScan={handleScanSubmit} loading={loading} />
      </section>
      <section className="lg:col-span-8">
        <IntelligenceResults result={result} loading={loading} error={error} target={target} />
      </section>
    </div>
  );
}

export default AuditDashboard;