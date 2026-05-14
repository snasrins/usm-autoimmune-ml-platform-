import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import DashboardPage from './pages/DashboardPage';
import DashboardPageV3 from './pages/DashboardPageV3';
import DataPipelinePage from './pages/DataPipelinePage';
import DataIngestionPage from './pages/DataIngestionPage';
import DataPreparationPage from './pages/DataPreparationPage';
import DataCleaningPage from './pages/DataCleaningPage';
import DataCatalogPage from './pages/DataCatalogPage';
import MLPreparationQueuePage from './pages/MLPreparationQueuePage';
import DatasetEDAPage from './pages/DatasetEDAPage';
import DataQualityDetailPage from './pages/DataQualityDetailPage';
import DataQualityDashboardPage from './pages/DataQualityDashboardPage';
import TrainingJobsPage from './pages/TrainingJobsPage';
import ModelRegistryPage from './pages/ModelRegistryPage';
import ModelComparisonPage from './pages/ModelComparisonPage';
import BatchPredictionPage from './pages/BatchPredictionPage';
import PredictionsHistoryPage from './pages/PredictionsHistoryPage';
import HyperparameterTuningPage from './pages/HyperparameterTuningPage';
import UserProfilePage from './pages/UserProfilePage';
import DataQualityWorkbenchPage from './pages/DataQualityWorkbenchPage';
import ClinicalScorecardPage from './pages/ClinicalScorecardPage';
import ModelExplainabilityPage from './pages/ModelExplainabilityPageConnected';
import PatientClassifierPage from './pages/PatientClassifierPage';
import FeatureImportancePage from './pages/FeatureImportancePage';
import ExperimentLogPage from './pages/ExperimentLogPage';
import ComputeMonitorPage from './pages/ComputeMonitorPage';
import DataRepositoryPage from './pages/DataRepositoryPage';
import MissionControlPage from './pages/MissionControlPage';
import ProtectedRoute from './components/ProtectedRoute';
import './index.css';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mission-control"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard-v3"
          element={
            <ProtectedRoute>
              <DashboardPageV3 />
            </ProtectedRoute>
          }
        />
        <Route
          path="/data-preparation"
          element={
            <ProtectedRoute>
              <DataPipelinePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ml-prep-workflow"
          element={
            <ProtectedRoute>
              <DataPreparationPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/data-cleaning"
          element={
            <ProtectedRoute>
              <DataCleaningPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/data-catalog"
          element={
            <ProtectedRoute>
              <DataCatalogPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ml-preparation"
          element={
            <ProtectedRoute>
              <MLPreparationQueuePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dataset-eda"
          element={
            <ProtectedRoute>
              <DatasetEDAPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/data-quality/:id"
          element={
            <ProtectedRoute>
              <DataQualityDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/training"
          element={
            <ProtectedRoute>
              <TrainingJobsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/models"
          element={
            <ProtectedRoute>
              <ModelRegistryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/model-comparison"
          element={
            <ProtectedRoute>
              <ModelComparisonPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/batch-prediction"
          element={
            <ProtectedRoute>
              <BatchPredictionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/predictions-history"
          element={
            <ProtectedRoute>
              <PredictionsHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tuning"
          element={
            <ProtectedRoute>
              <HyperparameterTuningPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <UserProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/data-quality"
          element={
            <ProtectedRoute>
              <DataQualityWorkbenchPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/scorecard"
          element={
            <ProtectedRoute>
              <ClinicalScorecardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/explainability"
          element={
            <ProtectedRoute>
              <ModelExplainabilityPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/classifier"
          element={
            <ProtectedRoute>
              <PatientClassifierPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/features"
          element={
            <ProtectedRoute>
              <FeatureImportancePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/experiments"
          element={
            <ProtectedRoute>
              <ExperimentLogPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/compute"
          element={
            <ProtectedRoute>
              <ComputeMonitorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/repository"
          element={
            <ProtectedRoute>
              <DataRepositoryPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
    </ThemeProvider>
  );
}

export default App;
