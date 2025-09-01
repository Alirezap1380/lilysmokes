import { useEffect, useState } from "react";

export default function CodeViewer() {
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [key, setKey] = useState<number>(0);

  useEffect(() => {
    const handler = (e: CustomEvent<{ file: string; code: string }>) => {
      try {
        setIsLoading(true);
        setError(null);
        const { file, code } = e.detail;
        setActiveFile(file);
        setFileContent(code || "");
        setKey(prev => prev + 1);
      } catch (err) {
        setError("Failed to load file content");
        console.error("File select error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    window.addEventListener("ai:file-select", handler as EventListener);
    return () => window.removeEventListener("ai:file-select", handler as EventListener);
  }, []);

  return (
    <div className="flex-1 flex flex-col bg-gray-950 border-l border-gray-700 overflow-hidden">
      <div className="p-2 text-sm text-gray-400 border-b border-gray-700">
        {activeFile ? `📄 ${activeFile}` : "Select a file to preview code"}
      </div>
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400">Loading...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full text-red-400">
            {error}
          </div>
        ) : fileContent ? (
          <pre className="p-4 text-sm text-gray-300 bg-gray-900 h-full overflow-auto">
            <code>{fileContent}</code>
          </pre>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            No code to display
          </div>
        )}
      </div>
    </div>
  );
}
