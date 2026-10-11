import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { AdminDashboard } from './pages/AdminDashboard'
import { ContractorDashboard } from './pages/ContractorDashboard'
import { ContractorOrderConfirmationPage } from './pages/ContractorOrderConfirmationPage'
import { ContractorOrderDetailPage } from './pages/ContractorOrderDetailPage'
import { ContractorMarketplacePage } from './pages/ContractorMarketplacePage'
import { ContractorOrderPage } from './pages/ContractorOrderPage'
import { ContractorSiteDetailPage } from './pages/ContractorSiteDetailPage'
import { ContractorSiteFormPage } from './pages/ContractorSiteFormPage'
import { ContractorSitesPage } from './pages/ContractorSitesPage'
import { HomeRedirect } from './pages/HomeRedirect'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { SupplierDashboard } from './pages/SupplierDashboard'
import { SupplierPlantDetailPage } from './pages/SupplierPlantDetailPage'
import { SupplierPlantFormPage } from './pages/SupplierPlantFormPage'
import { SupplierPlantsPage } from './pages/SupplierPlantsPage'
import { SupplierOrderDetailPage } from './pages/SupplierOrderDetailPage'
import { SupplierOrdersPage } from './pages/SupplierOrdersPage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route element={<ProtectedRoute allowedRoles={['CONTRACTOR']} />}>
            <Route path="/contractor" element={<ContractorDashboard />} />
            <Route path="/contractor/sites" element={<ContractorSitesPage />} />
            <Route path="/contractor/sites/new" element={<ContractorSiteFormPage mode="create" />} />
            <Route path="/contractor/sites/:id" element={<ContractorSiteDetailPage />} />
            <Route path="/contractor/sites/:id/edit" element={<ContractorSiteFormPage mode="edit" />} />
            <Route path="/contractor/marketplace" element={<ContractorMarketplacePage />} />
            <Route path="/contractor/orders/new" element={<ContractorOrderPage />} />
            <Route path="/contractor/orders/:id/edit" element={<ContractorOrderPage mode="edit" />} />
            <Route path="/contractor/orders/:id/confirmation" element={<ContractorOrderConfirmationPage />} />
            <Route path="/contractor/orders/:id" element={<ContractorOrderDetailPage />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['SUPPLIER']} />}>
            <Route path="/supplier" element={<SupplierDashboard />} />
            <Route path="/supplier/orders" element={<SupplierOrdersPage />} />
            <Route path="/supplier/orders/:id" element={<SupplierOrderDetailPage />} />
            <Route path="/supplier/plants" element={<SupplierPlantsPage />} />
            <Route path="/supplier/plants/new" element={<SupplierPlantFormPage mode="create" />} />
            <Route path="/supplier/plants/:id/edit" element={<SupplierPlantFormPage mode="edit" />} />
            <Route path="/supplier/plants/:id" element={<SupplierPlantDetailPage />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
            <Route path="/admin" element={<AdminDashboard />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
