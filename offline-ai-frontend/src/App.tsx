/**
 * Main Application Component
 * 
 * This component manages the overall state and coordination of the AI agents system.
 * It handles the communication flow between different agents (Coordinator, Coder, Tester, Runner)
 * and maintains the state of their interactions.
 * 
 * Key Features:
 * - Dark/light mode toggle
 * - Agent communication orchestration
 * - State management for agent interactions
 * - Real-time updates of agent messages
 */

import React, { useState } from 'react';
import CodeAndFilesPage from './pages/CodeAndFilesPage';
import AICommunicationPage from './pages/AICommunicationPage';
import ManualAgentsPage from './pages/ManualAgentsPage';
import { useTheme } from './hooks/useTheme';
import './styles/shared.css';

type PageType = 'code' | 'ai' | 'manual';

export default function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('code');
  const { isDark, toggleTheme } = useTheme();

  const renderPage = () => {
    switch (currentPage) {
      case 'code':
        return <CodeAndFilesPage />;
      case 'ai':
        return <AICommunicationPage />;
      case 'manual':
        return <ManualAgentsPage />;
      default:
        return <CodeAndFilesPage />;
    }
  };

  const handlePageChange = (page: PageType) => (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setCurrentPage(page);
  };

  const handleThemeToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleTheme();
  };

  return (
    <div className={`h-screen w-screen ${isDark ? 'bg-gray-900' : 'bg-gray-100'} text-${isDark ? 'white' : 'gray-900'} flex flex-col overflow-hidden transition-colors duration-200`}>
      {/* Top Bar */}
      <div className={`p-4 flex justify-between items-center border-b ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
        <h1 className="text-xl font-bold">Offline AI Coding Assistant</h1>
        <div className="flex space-x-4 items-center">
          <nav className="flex space-x-2">
            <button
              type="button"
              className={`px-4 py-2 rounded transition-colors duration-200 ${
                currentPage === 'code' 
                  ? (isDark ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white') 
                  : (isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300')
              }`}
              onClick={handlePageChange('code')}
            >
              Code & Files
            </button>
            <button
              type="button"
              className={`px-4 py-2 rounded transition-colors duration-200 ${
                currentPage === 'ai' 
                  ? (isDark ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white') 
                  : (isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300')
              }`}
              onClick={handlePageChange('ai')}
            >
              AI Communication
            </button>
            <button
              type="button"
              className={`px-4 py-2 rounded transition-colors duration-200 ${
                currentPage === 'manual' 
                  ? (isDark ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white') 
                  : (isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300')
              }`}
              onClick={handlePageChange('manual')}
            >
              Manual Agents
            </button>
          </nav>
          
          <button 
            type="button"
            className={`${isDark ? 'bg-gray-800 hover:bg-gray-700' : 'bg-gray-200 hover:bg-gray-300'} px-3 py-1 rounded transition-colors duration-200`}
            onClick={handleThemeToggle}
          >
            {isDark ? '☀️ Light' : '🌙 Dark'}
          </button>
        </div>
      </div>

      {/* Page Content */}
      <div className="flex-1 overflow-hidden">
        {renderPage()}
      </div>
    </div>
  );
}