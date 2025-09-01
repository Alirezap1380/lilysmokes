import React from 'react';
import ManualAgentCanvas from '../components/ManualAgentCanvas';
import { useTheme } from '../hooks/useTheme';

export default function ManualAgentsPage() {
  const { isDark } = useTheme();
  
  return (
    <div className="h-full">
      <ManualAgentCanvas isDark={isDark} />
    </div>
  );
} 