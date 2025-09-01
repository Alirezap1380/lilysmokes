import React from 'react';
import FileTree from '../components/FileTree';
import CodeViewer from '../components/CodeViewer';

export default function CodeAndFilesPage() {
  return (
    <div className="flex h-full">
      <FileTree />
      <CodeViewer />
    </div>
  );
} 