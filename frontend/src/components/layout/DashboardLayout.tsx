import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import { InteractiveTutorial } from '../onboarding/InteractiveTutorial';
import { useTutorialStore } from '../../stores/tutorialStore';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const { isStarted, isCompleted, completionAcknowledged } = useTutorialStore();

  const showTutorial = isStarted && (!isCompleted || !completionAcknowledged);

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <Sidebar />
      <Header />
      <main className="pl-64 pt-16 min-h-screen">
        <div className="p-8">
          {showTutorial && <InteractiveTutorial />}
          {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
