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
    <div 
      data-theme="mantis" 
      className="min-h-screen bg-[var(--mantis-bg)] text-slate-100 font-sans relative overflow-x-hidden transition-colors duration-500"
    >
      {/* Scanline Overlay */}
      <div className="scanline-overlay" />

      {/* Mantis Glow Orbs */}
      <div className="liquid-orb top-[-10%] left-[-5%] w-[500px] h-[500px] bg-emerald-500/20 blur-[120px]" />
      <div className="liquid-orb bottom-[-10%] right-[-5%] w-[400px] h-[400px] bg-green-600/10 blur-[100px]" />
      <div className="liquid-orb top-[20%] right-[10%] w-[300px] h-[300px] bg-emerald-400/5 blur-[80px]" />

      <Sidebar />
      <Header />
      
      <main className="pl-64 pt-16 min-h-screen relative z-10">
        <div className="p-8 max-w-7xl mx-auto">
          {showTutorial && <InteractiveTutorial />}
          {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
