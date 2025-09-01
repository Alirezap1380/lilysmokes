# Frontend Structure Documentation

## Overview
The frontend has been restructured into 4 main pages with a shared CSS file for consistent styling across all pages. The structure is now simplified with direct page components and a unified navigation system.

## Page Structure

### 1. Main App (`src/App.tsx`)
- **Purpose**: Main application container with navigation and theme management
- **Features**: 
  - Navigation between pages
  - Dark/light mode toggle
  - Unified layout and background
  - Responsive design

### 2. CodeAndFilesPage (`src/pages/CodeAndFilesPage.tsx`)
- **Purpose**: Code editor and file panel functionality
- **Components**: 
  - FileTree component
  - CodeViewer component
- **Features**: File browsing and code editing

### 3. AICommunicationPage (`src/pages/AICommunicationPage.tsx`)
- **Purpose**: AI agent communication and chat
- **Components**:
  - AgentVisualization component
  - ConversationHistory component (collapsible sidebar)
- **Features**: 
  - AI agent interactions
  - Conversation management
  - Backend connection handling
  - Collapsible conversation history

### 4. ManualAgentsPage (`src/pages/ManualAgentsPage.tsx`)
- **Purpose**: Manual agent canvas and configuration
- **Components**:
  - ManualAgentCanvas component
- **Features**: 
  - Manual agent setup
  - Agent configuration
  - Visual agent connections

## Shared Resources

### Shared CSS (`src/styles/shared.css`)
- **Purpose**: Common styles used across all pages
- **Includes**:
  - Animation keyframes
  - Common button styles
  - Status indicators
  - Layout utilities
  - Theme transitions

## Navigation
- Main navigation is handled in `src/App.tsx`
- Uses a simple state-based page switching system
- Each page is completely independent
- Unified header with navigation and theme toggle

## Key Improvements
1. **Simplified Structure**: Removed BaseLayout wrapper for cleaner architecture
2. **Collapsible Sidebar**: Conversation history can be collapsed/expanded
3. **Better Layout**: Fixed background and layout issues
4. **Consistent Theming**: Proper dark/light mode support across all pages
5. **Responsive Design**: Better mobile and desktop support

## Benefits of New Structure
1. **Cleaner Architecture**: Direct page components without unnecessary wrappers
2. **Better UX**: Collapsible conversation history saves space
3. **Consistent Styling**: Shared CSS ensures uniform appearance
4. **Maintainability**: Easier to modify individual pages
5. **Scalability**: Easy to add new pages

## File Organization
```
src/
├── App.tsx                     # Main app with navigation
├── pages/
│   ├── CodeAndFilesPage.tsx    # Code & files functionality
│   ├── AICommunicationPage.tsx # AI communication
│   └── ManualAgentsPage.tsx    # Manual agents
├── styles/
│   └── shared.css              # Shared styles for all pages
├── components/                 # Reusable components
├── services/                   # API services
├── hooks/                      # Custom hooks
├── contexts/                   # React contexts
└── types/                      # TypeScript types
```

## Features by Page

### Code & Files Page
- File tree navigation
- Code editor/viewer
- File management

### AI Communication Page
- AI agent visualization
- Collapsible conversation history
- Backend connection status
- Real-time agent interactions

### Manual Agents Page
- Manual agent canvas
- Agent configuration
- Visual connections between agents 