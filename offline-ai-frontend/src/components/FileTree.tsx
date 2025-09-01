import { useEffect, useState } from "react";
import { getGeneratedFiles, getFileContent } from "../services/api";

export default function FileTree() {
  const [files, setFiles] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load saved files when component mounts
    const loadFiles = async () => {
      try {
        const data = await getGeneratedFiles();
        setFiles(data.files || []);
        setError(null);
      } catch (error) {
        console.error('Failed to load files:', error);
        setError('Failed to load files');
      }
    };

    loadFiles();

    // Reload files when a new one is generated
    const refresh = async () => {
      try {
        const data = await getGeneratedFiles();
        setFiles(data.files || []);
        setError(null);
      } catch (error) {
        console.error('Failed to refresh files:', error);
        setError('Failed to refresh files');
      }
    };

    window.addEventListener("ai:file-generate", refresh);
    return () => window.removeEventListener("ai:file-generate", refresh);
  }, []);

  const handleFileClick = async (file: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const code = await getFileContent(file);
      window.dispatchEvent(new CustomEvent("ai:file-select", {
        detail: {
          file: file,
          code: code
        }
      }));
      setError(null);
    } catch (error) {
      console.error('Failed to load file content:', error);
      setError(`Failed to load ${file}`);
    }
  };

  return (
    <div className="w-64 p-4 bg-gray-900 text-white border-r border-gray-700 overflow-y-auto">
      <h2 className="text-lg font-bold mb-2">📁 Generated Files</h2>
      {error && (
        <div className="text-red-400 text-sm mb-2 p-2 bg-red-900/20 rounded">
          {error}
        </div>
      )}
      <ul className="space-y-1 text-sm">
        {files.map(file => (
          <li
            key={file}
            className="cursor-pointer hover:underline p-1 rounded hover:bg-gray-800"
            onClick={(e) => handleFileClick(file, e)}
          >
            {file}
          </li>
        ))}
      </ul>
    </div>
  );
}
