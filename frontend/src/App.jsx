import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import AuditDashboard from './pages/AuditDashboard';
import ReportsDashboard from './pages/ReportsDashboard'; 

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/audit" replace />} />
          <Route path="audit" element={<AuditDashboard />} />
          <Route path="reports" element={<ReportsDashboard />} /> 
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;