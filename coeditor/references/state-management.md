# State Management Patterns for CopilotKit + LangGraph Applications

Comprehensive guide to managing shared state between React editors, CopilotKit, and LangGraph agents.

## Overview

State management in CopilotKit + LangGraph applications requires coordinating between:
1. **Frontend State** (React): UI state, editor content, user interactions
2. **CopilotKit Context**: State exposed to AI for context
3. **Backend State** (LangGraph): Agent state, workflow state
4. **Shared State**: Synchronized between frontend and backend

## State Management Libraries

### Zustand (Recommended)

Lightweight, TypeScript-friendly state management.

**Installation:**
```bash
npm install zustand
```

**Basic Usage:**
```typescript
import { create } from 'zustand';

interface EditorStore {
  content: string;
  selection: { start: number; end: number; text: string };
  updateContent: (content: string) => void;
  updateSelection: (selection: EditorStore['selection']) => void;
}

export const useEditorStore = create<EditorStore>((set) => ({
  content: '',
  selection: { start: 0, end: 0, text: '' },

  updateContent: (content) => set({ content }),
  updateSelection: (selection) => set({ selection }),
}));
```

**Why Zustand:**
- Minimal boilerplate
- No providers needed
- TypeScript-first
- DevTools integration
- Small bundle size (~1KB)

### Jotai

Atomic state management, perfect for granular updates.

**Installation:**
```bash
npm install jotai
```

**Basic Usage:**
```typescript
import { atom, useAtom } from 'jotai';

// Define atoms
export const contentAtom = atom('');
export const selectionAtom = atom({ start: 0, end: 0, text: '' });

// Derived atoms
export const wordCountAtom = atom((get) => {
  const content = get(contentAtom);
  return content.split(/\s+/).length;
});

// Usage in component
function Editor() {
  const [content, setContent] = useAtom(contentAtom);
  const [wordCount] = useAtom(wordCountAtom);

  return <div>{wordCount} words</div>;
}
```

**Why Jotai:**
- Atomic updates (fine-grained)
- Automatic dependency tracking
- No extra re-renders
- Great for complex derived state

### TanStack Query (React Query)

For server state management and synchronization.

**Installation:**
```bash
npm install @tanstack/react-query
```

**Basic Usage:**
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

// Fetch state from backend
function useEditorState() {
  return useQuery({
    queryKey: ['editor', 'state'],
    queryFn: async () => {
      const response = await fetch('/api/editor/state');
      return response.json();
    },
  });
}

// Sync state to backend
function useUpdateEditorState() {
  return useMutation({
    mutationFn: async (state: EditorState) => {
      await fetch('/api/editor/state', {
        method: 'POST',
        body: JSON.stringify(state),
      });
    },
  });
}
```

**Why React Query:**
- Perfect for backend synchronization
- Automatic caching
- Optimistic updates
- Background refetching

## Frontend State Patterns

### Zustand Store Pattern

**Complete Editor Store:**
```typescript
// stores/editorStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface EditorState {
  // Content
  content: string;
  contentType: 'text' | 'markdown' | 'code' | 'json';

  // Selection
  selection: {
    start: number;
    end: number;
    text: string;
  };

  // History
  history: string[];
  historyIndex: number;

  // UI State
  isLoading: boolean;
  error: string | null;

  // Collaboration
  collaborators: User[];
  comments: Comment[];

  // Actions
  updateContent: (content: string) => void;
  updateSelection: (selection: EditorState['selection']) => void;
  undo: () => void;
  redo: () => void;
  reset: () => void;
}

export const useEditorStore = create<EditorState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        content: '',
        contentType: 'text',
        selection: { start: 0, end: 0, text: '' },
        history: [],
        historyIndex: -1,
        isLoading: false,
        error: null,
        collaborators: [],
        comments: [],

        // Actions
        updateContent: (content) =>
          set((state) => ({
            content,
            history: [...state.history.slice(0, state.historyIndex + 1), content],
            historyIndex: state.historyIndex + 1,
          })),

        updateSelection: (selection) =>
          set({ selection }),

        undo: () => {
          const { history, historyIndex } = get();
          if (historyIndex > 0) {
            set({
              content: history[historyIndex - 1],
              historyIndex: historyIndex - 1,
            });
          }
        },

        redo: () => {
          const { history, historyIndex } = get();
          if (historyIndex < history.length - 1) {
            set({
              content: history[historyIndex + 1],
              historyIndex: historyIndex + 1,
            });
          }
        },

        reset: () =>
          set({
            content: '',
            selection: { start: 0, end: 0, text: '' },
            history: [],
            historyIndex: -1,
          }),
      }),
      {
        name: 'editor-storage', // localStorage key
        partialize: (state) => ({
          content: state.content,
          contentType: state.contentType,
        }), // Only persist certain fields
      }
    )
  )
);
```

**Agent Store:**
```typescript
// stores/agentStore.ts
import { create } from 'zustand';

interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  progress?: number;
}

interface Task {
  id: string;
  type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

interface AgentState {
  agents: Agent[];
  activeAgent: string | null;
  tasks: Task[];

  // Actions
  setActiveAgent: (agentId: string) => void;
  updateAgentStatus: (agentId: string, status: Agent['status']) => void;
  addTask: (task: Omit<Task, 'id'>) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [
    {
      id: 'writing_assistant',
      name: 'Writing Assistant',
      description: 'Helps with writing and editing',
      status: 'idle',
    },
    {
      id: 'code_assistant',
      name: 'Code Assistant',
      description: 'Helps with coding',
      status: 'idle',
    },
  ],
  activeAgent: null,
  tasks: [],

  setActiveAgent: (agentId) =>
    set({ activeAgent: agentId }),

  updateAgentStatus: (agentId, status) =>
    set((state) => ({
      agents: state.agents.map((agent) =>
        agent.id === agentId ? { ...agent, status } : agent
      ),
    })),

  addTask: (task) =>
    set((state) => ({
      tasks: [
        ...state.tasks,
        { ...task, id: `task-${Date.now()}` },
      ],
    })),

  updateTask: (taskId, updates) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId ? { ...task, ...updates } : task
      ),
    })),
}));
```

### Store Selectors

Optimize re-renders with selectors:

```typescript
// Only re-render when content changes
const content = useEditorStore((state) => state.content);

// Only re-render when selection changes
const selection = useEditorStore((state) => state.selection);

// Multiple values with shallow equality
import { shallow } from 'zustand/shallow';

const { content, selection } = useEditorStore(
  (state) => ({ content: state.content, selection: state.selection }),
  shallow
);
```

## Backend State Management

### LangGraph State Schema

```python
# backend/state/schemas.py
from typing import TypedDict, Annotated, Sequence, Optional, Literal
from langchain_core.messages import BaseMessage
import operator

class EditorState(TypedDict):
    """Shared state schema matching frontend."""

    # Document
    content: str
    content_type: Literal["text", "markdown", "code", "json"]

    # Selection
    selection: dict  # {"start": int, "end": int, "text": str}

    # Messages
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Agent context
    current_agent: str
    task: str
    task_status: Literal["pending", "in_progress", "completed", "failed"]

    # Metadata
    version: int
    metadata: dict
```

### State Manager

```python
# backend/state/state_manager.py
from typing import Dict, Any
import asyncio
from datetime import datetime

class StateManager:
    """Manages state synchronization between frontend and backend."""

    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._subscribers = []
        self._lock = asyncio.Lock()

    async def get_state(self, key: str = None) -> Any:
        """Get current state or specific key."""
        async with self._lock:
            if key:
                return self._state.get(key)
            return self._state.copy()

    async def update_state(self, updates: Dict[str, Any]) -> None:
        """Update state and notify subscribers."""
        async with self._lock:
            self._state.update(updates)
            self._state["version"] = self._state.get("version", 0) + 1
            self._state["updated_at"] = datetime.now().isoformat()

        # Notify subscribers
        await self._notify_subscribers(self._state)

    async def subscribe(self, callback):
        """Subscribe to state changes."""
        self._subscribers.append(callback)

    async def _notify_subscribers(self, state: Dict[str, Any]):
        """Notify all subscribers of state change."""
        for callback in self._subscribers:
            try:
                await callback(state)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")

# Global state manager instance
state_manager = StateManager()
```

## State Synchronization

### Frontend to Backend Sync

```typescript
// hooks/useStateSync.ts
import { useEffect } from 'react';
import { useEditorStore } from '../stores/editorStore';
import { AgentAPIClient } from '../lib/api-client';

export function useStateSync() {
  const content = useEditorStore((state) => state.content);
  const selection = useEditorStore((state) => state.selection);
  const contentType = useEditorStore((state) => state.contentType);

  useEffect(() => {
    // Debounce state sync
    const timeout = setTimeout(async () => {
      await AgentAPIClient.syncState({
        content,
        selection,
        content_type: contentType,
      });
    }, 500);

    return () => clearTimeout(timeout);
  }, [content, selection, contentType]);
}
```

### Backend to Frontend Sync (WebSocket)

```typescript
// hooks/useWebSocketSync.ts
import { useEffect } from 'react';
import { useEditorStore } from '../stores/editorStore';
import { useAgentStore } from '../stores/agentStore';

export function useWebSocketSync() {
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      // Update editor state
      if (update.content !== undefined) {
        useEditorStore.setState({ content: update.content });
      }

      // Update agent state
      if (update.agent_status) {
        useAgentStore.getState().updateAgentStatus(
          update.agent_id,
          update.agent_status
        );
      }

      // Update tasks
      if (update.task) {
        useAgentStore.getState().updateTask(
          update.task.id,
          update.task
        );
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => ws.close();
  }, []);
}
```

### Backend WebSocket Handler

```python
# backend/api/websocket.py
from fastapi import WebSocket
from ..state.state_manager import state_manager
import json

async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for state sync."""
    await websocket.accept()

    # Subscribe to state changes
    async def send_update(state):
        """Send state update to client."""
        try:
            await websocket.send_json(state)
        except:
            pass  # Connection closed

    await state_manager.subscribe(send_update)

    try:
        while True:
            # Receive state updates from frontend
            data = await websocket.receive_text()
            updates = json.loads(data)

            # Update backend state
            await state_manager.update_state(updates)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

## Optimistic Updates

### Frontend Optimistic Update Pattern

```typescript
// hooks/useOptimisticUpdate.ts
import { useEditorStore } from '../stores/editorStore';
import { AgentAPIClient } from '../lib/api-client';

export function useOptimisticUpdate() {
  const updateContent = useEditorStore((state) => state.updateContent);

  const optimisticUpdate = async (newContent: string) => {
    // Save current content for rollback
    const previousContent = useEditorStore.getState().content;

    // Optimistically update UI
    updateContent(newContent);

    try {
      // Sync to backend
      await AgentAPIClient.updateContent(newContent);
    } catch (error) {
      // Rollback on error
      updateContent(previousContent);
      console.error('Failed to sync:', error);
    }
  };

  return { optimisticUpdate };
}
```

### With TanStack Query

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

function useUpdateContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (newContent: string) => {
      await AgentAPIClient.updateContent(newContent);
      return newContent;
    },

    // Optimistic update
    onMutate: async (newContent) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['content'] });

      // Snapshot previous value
      const previousContent = queryClient.getQueryData(['content']);

      // Optimistically update
      queryClient.setQueryData(['content'], newContent);

      // Return context with previous value
      return { previousContent };
    },

    // Rollback on error
    onError: (err, newContent, context) => {
      queryClient.setQueryData(['content'], context?.previousContent);
    },

    // Refetch on success or error
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
    },
  });
}
```

## State Persistence

### Local Storage (Zustand Persist)

```typescript
import { persist } from 'zustand/middleware';

const useEditorStore = create(
  persist(
    (set) => ({
      content: '',
      updateContent: (content) => set({ content }),
    }),
    {
      name: 'editor-storage',
      // Custom storage
      storage: {
        getItem: (name) => {
          const str = localStorage.getItem(name);
          return str ? JSON.parse(str) : null;
        },
        setItem: (name, value) => {
          localStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          localStorage.removeItem(name);
        },
      },
      // Partial persistence
      partialize: (state) => ({
        content: state.content,
        contentType: state.contentType,
      }),
    }
  )
);
```

### IndexedDB for Large Documents

```typescript
// utils/indexedDB.ts
import { openDB, DBSchema } from 'idb';

interface EditorDB extends DBSchema {
  documents: {
    key: string;
    value: {
      id: string;
      content: string;
      updatedAt: number;
    };
  };
}

const dbPromise = openDB<EditorDB>('editor-db', 1, {
  upgrade(db) {
    db.createObjectStore('documents', { keyPath: 'id' });
  },
});

export async function saveDocument(id: string, content: string) {
  const db = await dbPromise;
  await db.put('documents', {
    id,
    content,
    updatedAt: Date.now(),
  });
}

export async function loadDocument(id: string) {
  const db = await dbPromise;
  return await db.get('documents', id);
}
```

### Backend Persistence (PostgreSQL)

```python
# backend/persistence/database.py
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class EditorDocument(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    content = Column(Text)
    content_type = Column(String)
    version = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Setup
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)

async def save_document(doc_id: str, content: str, content_type: str):
    """Save document to database."""
    async with AsyncSessionLocal() as session:
        doc = await session.get(EditorDocument, doc_id)

        if doc:
            doc.content = content
            doc.content_type = content_type
            doc.version += 1
        else:
            doc = EditorDocument(
                id=doc_id,
                content=content,
                content_type=content_type,
            )
            session.add(doc)

        await session.commit()

async def load_document(doc_id: str):
    """Load document from database."""
    async with AsyncSessionLocal() as session:
        return await session.get(EditorDocument, doc_id)
```

## Conflict Resolution

### Last-Write-Wins

```typescript
interface StateUpdate {
  version: number;
  content: string;
  timestamp: number;
}

function mergeState(local: StateUpdate, remote: StateUpdate): StateUpdate {
  // Remote version is newer
  if (remote.version > local.version) {
    return remote;
  }

  // Local version is newer
  if (local.version > remote.version) {
    return local;
  }

  // Same version, use timestamp
  if (remote.timestamp > local.timestamp) {
    return remote;
  }

  return local;
}
```

### Operational Transformation (OT)

For real-time collaboration:

```typescript
// utils/ot.ts
export function transform(op1: Operation, op2: Operation): Operation {
  // Implement OT algorithm
  // This is simplified - use library like ShareDB in production

  if (op1.type === 'insert' && op2.type === 'insert') {
    if (op1.position < op2.position) {
      return op2;
    } else {
      return { ...op2, position: op2.position + op1.text.length };
    }
  }

  // Handle other operation types...
  return op2;
}
```

### CRDT (Conflict-free Replicated Data Type)

```typescript
// Use libraries like Yjs or Automerge
import * as Y from 'yjs';

const ydoc = new Y.Doc();
const ytext = ydoc.getText('content');

// Local update
ytext.insert(0, 'Hello');

// Sync with peers
ydoc.on('update', (update) => {
  // Send to other clients
  broadcastUpdate(update);
});

// Receive updates from peers
function handleUpdate(update: Uint8Array) {
  Y.applyUpdate(ydoc, update);
}
```

## Performance Optimization

### Debouncing

```typescript
import { useDebounce } from 'use-debounce';

function Editor() {
  const [content, setContent] = useState('');
  const [debouncedContent] = useDebounce(content, 500);

  useEffect(() => {
    // Sync to backend only after 500ms of no changes
    syncToBackend(debouncedContent);
  }, [debouncedContent]);

  return <textarea value={content} onChange={(e) => setContent(e.target.value)} />;
}
```

### Throttling

```typescript
import { useThrottle } from 'use-throttle';

function Editor() {
  const [content, setContent] = useState('');
  const throttledContent = useThrottle(content, 1000);

  // Sync at most once per second
  useEffect(() => {
    syncToBackend(throttledContent);
  }, [throttledContent]);
}
```

### Batching Updates

```typescript
class BatchedStateSync {
  private updates: any[] = [];
  private timeout: NodeJS.Timeout | null = null;

  queueUpdate(update: any) {
    this.updates.push(update);

    if (!this.timeout) {
      this.timeout = setTimeout(() => this.flush(), 100);
    }
  }

  private async flush() {
    const batch = [...this.updates];
    this.updates = [];
    this.timeout = null;

    // Send all updates in one request
    await AgentAPIClient.batchUpdate(batch);
  }
}
```

## Best Practices

1. **Single Source of Truth**: One store per domain (editor, agents, UI)
2. **Immutable Updates**: Always create new objects, never mutate
3. **Type Safety**: Use TypeScript for all state
4. **Selective Subscriptions**: Only subscribe to what you need
5. **Debounce Syncs**: Don't sync on every keystroke
6. **Optimistic Updates**: Update UI immediately, sync in background
7. **Error Recovery**: Always have rollback mechanism
8. **Persistence**: Auto-save to prevent data loss
9. **Versioning**: Track state versions for conflict resolution
10. **Testing**: Test state logic independently of UI

## Common Patterns

### Command Pattern for Undo/Redo

```typescript
interface Command {
  execute: () => void;
  undo: () => void;
}

class InsertTextCommand implements Command {
  constructor(
    private editor: Editor,
    private text: string,
    private position: number
  ) {}

  execute() {
    this.editor.insertText(this.text, this.position);
  }

  undo() {
    this.editor.deleteText(this.position, this.text.length);
  }
}

// Usage
const history: Command[] = [];
const command = new InsertTextCommand(editor, 'hello', 0);
command.execute();
history.push(command);

// Undo
history.pop()?.undo();
```

### Event Sourcing

```typescript
interface Event {
  type: string;
  payload: any;
  timestamp: number;
  version: number;
}

const events: Event[] = [];

function applyEvent(event: Event) {
  switch (event.type) {
    case 'CONTENT_UPDATED':
      useEditorStore.setState({ content: event.payload.content });
      break;
    case 'SELECTION_CHANGED':
      useEditorStore.setState({ selection: event.payload.selection });
      break;
  }

  events.push(event);
}

// Rebuild state from events
function replayEvents(events: Event[]) {
  events.forEach(applyEvent);
}
```

## Troubleshooting

**State not syncing:**
- Check WebSocket connection
- Verify state schema matches frontend/backend
- Check for serialization issues

**Performance issues:**
- Add debouncing/throttling
- Use selectors to prevent unnecessary re-renders
- Batch updates

**State conflicts:**
- Implement versioning
- Use conflict resolution strategy (last-write-wins, OT, CRDT)
- Show conflict resolution UI to user
