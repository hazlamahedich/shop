import React, { useEffect, useState } from 'react';

export function Interactive3DBackground() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth - 0.5) * 30,
        y: (e.clientY / window.innerHeight - 0.5) * 30,
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-hidden bg-[#0e0e13]">
      {/* Dynamic gradients reacting to mouse */}
      <div 
        className="absolute inset-0 opacity-40 transition-transform duration-75 ease-out"
        style={{
          transform: `translate(${mousePos.x}px, ${mousePos.y}px)`,
          background: 'radial-gradient(circle at 60% 40%, rgba(0, 245, 212, 0.4) 0%, transparent 50%), radial-gradient(circle at 40% 60%, rgba(14, 165, 233, 0.3) 0%, transparent 50%)',
          filter: 'blur(80px)'
        }}
      />

      {/* Grid overlay */}
      <div 
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M54.627 0l.83.83v58.34h-58.34l-.83-.83V0h58.34zM29.5 30.5v-29h-29v29h29zm30 0v-29h-29v29h29zm-30 30v-29h-29v29h29zm30 0v-29h-29v29h29z' fill='%23ffffff' fill-opacity='1' fill-rule='evenodd'/%3E%3C/svg%3E")`
        }}
      />

      {/* Scanline effect */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#00f5d4]/[0.03] to-transparent h-[15%] opacity-50 animate-[scan_6s_ease-in-out_infinite]" />

      <style>{`
        @keyframes scan {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(700%); }
        }
      `}</style>
    </div>
  );
}
