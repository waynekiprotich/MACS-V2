import React from 'react';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <div className="min-h-screen bg-githubDark text-gray-200">
      <header className="border-b border-githubBorder p-4 bg-githubDarker flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">MACS-V2 Dashboard</h1>
      </header>
      <main className="p-6">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
