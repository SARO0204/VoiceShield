import React, { useState, useEffect } from "react";
import { Sidebar } from "./components/layout/Sidebar";
import { Header } from "./components/layout/Header";
import { DashboardPage } from "./pages/DashboardPage";
import { LiveProtectionPage } from "./pages/LiveProtectionPage";
import { AnalyzeAudioPage } from "./pages/AnalyzeAudioPage";
import { CallMonitorPage } from "./pages/CallMonitorPage";
import { VerificationPage } from "./pages/VerificationPage";
import { AlertsPage } from "./pages/AlertsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { ModelTrainingPage } from "./pages/ModelTrainingPage";
import { SystemHealthPage } from "./pages/SystemHealthPage";
import { SettingsPage } from "./pages/SettingsPage";
import { api } from "./services/api";
import type { DashboardSummary, SystemStatus, UserProfile } from "./types";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(
    null,
  );
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeProtection, setActiveProtection] = useState<boolean>(true);
  const [loadingDashboard, setLoadingDashboard] = useState<boolean>(true);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  const loadData = async () => {
    const [dashResult, sysResult, meResult] = await Promise.allSettled([
      api.getDashboard(),
      api.getSystemStatus(),
      api.getMe(),
    ]);

    if (dashResult.status === "fulfilled") {
      setDashboardData(dashResult.value);
      setDashboardError(null);
    } else {
      const message =
        dashResult.reason instanceof Error
          ? dashResult.reason.message
          : "Dashboard data is unavailable.";
      setDashboardError(message);
      console.error("Error fetching dashboard:", dashResult.reason);
    }
    if (sysResult.status === "fulfilled") setSystemStatus(sysResult.value);
    if (meResult.status === "fulfilled") setUser(meResult.value);
    setLoadingDashboard(false);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  const criticalAlertsCount = dashboardData?.critical_alerts || 0;

  return (
    <div className="flex min-h-screen bg-[#070b12] text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        criticalAlertCount={criticalAlertsCount}
      />

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <Header
          systemStatus={systemStatus}
          user={user}
          activeProtection={activeProtection}
          onToggleProtection={() => setActiveProtection(!activeProtection)}
          criticalAlertsCount={criticalAlertsCount}
          onOpenAlerts={() => setActiveTab("alerts")}
        />

        {/* Dynamic Page Views */}
        <main className="flex-1 p-6 overflow-y-auto">
          {activeTab === "dashboard" && (
            <DashboardPage
              data={dashboardData}
              isLoading={loadingDashboard}
              errorMessage={dashboardError}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === "live" && <LiveProtectionPage />}

          {activeTab === "analyze" && <AnalyzeAudioPage />}

          {activeTab === "calls" && <CallMonitorPage />}

          {activeTab === "verification" && <VerificationPage />}

          {activeTab === "alerts" && <AlertsPage />}

          {activeTab === "history" && <HistoryPage />}

          {activeTab === "analytics" && <AnalyticsPage />}

          {activeTab === "training" && <ModelTrainingPage />}

          {activeTab === "health" && <SystemHealthPage />}

          {activeTab === "settings" && <SettingsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;
