export interface AIBlock {
  type: 'coder' | 'tester' | 'coordinator' | 'runner';
  content: string;
  timestamp: string;
  id: string;
  name: string;
} 