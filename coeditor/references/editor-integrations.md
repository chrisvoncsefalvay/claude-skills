# Editor Integration Patterns

Comprehensive guide to integrating different editor types with CopilotKit and LangGraph for AI-powered collaborative editing.

## Editor Types Overview

### 1. Text/Code Editors
- **Monaco Editor** (VS Code editor)
- **CodeMirror** (Lightweight code editor)
- **Ace Editor** (Mature code editor)
- **TipTap** (Rich text editor)

### 2. Document Editors
- **Slate** (Framework for building editors)
- **Lexical** (Facebook's editor framework)
- **ProseMirror** (Structured editing)
- **Quill** (Rich text WYSIWYG)

### 3. Node-Based Editors
- **ReactFlow** (Graph/flow editor)
- **Rete.js** (Visual programming)
- **Cytoscape** (Graph theory)

## Monaco Editor Integration

### Installation

```bash
npm install @monaco-editor/react monaco-editor
```

### Basic Setup

```typescript
// components/MonacoEditor.tsx
import Editor, { OnMount } from '@monaco-editor/react';
import { useRef, useEffect } from 'react';
import { useEditorStore } from '../stores/editorStore';
import { useCopilotReadable, useCopilotAction } from '@copilotkit/react-core';
import type * as Monaco from 'monaco-editor';

export function MonacoEditor() {
  const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);
  const { content, updateContent, selection, updateSelection } = useEditorStore();

  // Make state readable by CopilotKit
  useCopilotReadable({
    description: "Current code in the editor",
    value: {
      content,
      language: 'typescript',
      selection: selection.text,
    },
  });

  // Define AI actions
  useCopilotAction({
    name: "insertCode",
    description: "Insert code at cursor position",
    parameters: [
      { name: "code", type: "string", description: "Code to insert", required: true },
    ],
    handler: async ({ code }) => {
      const editor = editorRef.current;
      if (!editor) return;

      const position = editor.getPosition();
      if (!position) return;

      editor.executeEdits('', [{
        range: {
          startLineNumber: position.lineNumber,
          startColumn: position.column,
          endLineNumber: position.lineNumber,
          endColumn: position.column,
        },
        text: code,
      }]);
    },
  });

  useCopilotAction({
    name: "replaceSelection",
    description: "Replace currently selected code",
    parameters: [
      { name: "newCode", type: "string", description: "New code", required: true },
    ],
    handler: async ({ newCode }) => {
      const editor = editorRef.current;
      if (!editor) return;

      const selection = editor.getSelection();
      if (!selection) return;

      editor.executeEdits('', [{
        range: selection,
        text: newCode,
      }]);
    },
  });

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Listen to content changes
    editor.onDidChangeModelContent(() => {
      const value = editor.getValue();
      updateContent(value);
    });

    // Listen to selection changes
    editor.onDidChangeCursorSelection((e) => {
      const model = editor.getModel();
      if (!model) return;

      const selectedText = model.getValueInRange(e.selection);
      updateSelection({
        start: model.getOffsetAt(e.selection.getStartPosition()),
        end: model.getOffsetAt(e.selection.getEndPosition()),
        text: selectedText,
      });
    });

    // Configure IntelliSense
    monaco.languages.registerCompletionItemProvider('typescript', {
      provideCompletionItems: async (model, position) => {
        // Integrate AI completions here
        return { suggestions: [] };
      },
    });
  };

  return (
    <Editor
      height="90vh"
      defaultLanguage="typescript"
      value={content}
      onMount={handleEditorDidMount}
      theme="vs-dark"
      options={{
        minimap: { enabled: true },
        fontSize: 14,
        wordWrap: 'on',
        automaticLayout: true,
        suggestOnTriggerCharacters: true,
        quickSuggestions: true,
      }}
    />
  );
}
```

### Advanced Monaco Features

**AI-Powered Code Actions:**
```typescript
import * as monaco from 'monaco-editor';

monaco.languages.registerCodeActionProvider('typescript', {
  provideCodeActions: async (model, range, context) => {
    const actions: monaco.languages.CodeAction[] = [];

    // Add AI-powered refactoring
    actions.push({
      title: 'Refactor with AI',
      kind: 'refactor',
      command: {
        id: 'ai.refactor',
        title: 'Refactor',
        arguments: [model.getValueInRange(range)],
      },
    });

    // Add AI explanations
    actions.push({
      title: 'Explain Code',
      kind: 'quickfix',
      command: {
        id: 'ai.explain',
        title: 'Explain',
        arguments: [model.getValueInRange(range)],
      },
    });

    return { actions, dispose: () => {} };
  },
});
```

**Inline AI Suggestions:**
```typescript
let currentSuggestion: monaco.editor.IContentWidget | null = null;

async function showAISuggestion(editor: monaco.editor.IStandaloneCodeEditor) {
  const position = editor.getPosition();
  if (!position) return;

  const model = editor.getModel();
  if (!model) return;

  // Get code before cursor
  const codeBefore = model.getValueInRange({
    startLineNumber: 1,
    startColumn: 1,
    endLineNumber: position.lineNumber,
    endColumn: position.column,
  });

  // Get AI suggestion
  const suggestion = await getAICompletion(codeBefore);

  // Show inline widget
  const widget: monaco.editor.IContentWidget = {
    getId: () => 'ai.suggestion',
    getDomNode: () => {
      const node = document.createElement('div');
      node.className = 'ai-suggestion';
      node.textContent = suggestion;
      return node;
    },
    getPosition: () => ({
      position,
      preference: [monaco.editor.ContentWidgetPositionPreference.BELOW],
    }),
  };

  editor.addContentWidget(widget);
  currentSuggestion = widget;
}
```

## Slate Editor Integration

### Installation

```bash
npm install slate slate-react slate-history
```

### Basic Setup

```typescript
// components/SlateEditor.tsx
import { createEditor, Descendant } from 'slate';
import { Slate, Editable, withReact } from 'slate-react';
import { withHistory } from 'slate-history';
import { useState, useMemo, useCallback } from 'react';
import { useCopilotReadable, useCopilotAction } from '@copilotkit/react-core';

const initialValue: Descendant[] = [
  {
    type: 'paragraph',
    children: [{ text: 'Start writing...' }],
  },
];

export function SlateEditor() {
  const editor = useMemo(() => withHistory(withReact(createEditor())), []);
  const [value, setValue] = useState<Descendant[]>(initialValue);

  // Serialize to plain text for AI
  const plainText = useMemo(() => {
    return value.map(n => Node.string(n)).join('\n');
  }, [value]);

  // Make content readable
  useCopilotReadable({
    description: "Document content",
    value: {
      content: plainText,
      structure: value,
    },
  });

  // AI actions
  useCopilotAction({
    name: "insertParagraph",
    description: "Insert a new paragraph",
    parameters: [
      { name: "text", type: "string", description: "Paragraph text", required: true },
    ],
    handler: async ({ text }) => {
      const { selection } = editor;
      if (!selection) return;

      Transforms.insertNodes(editor, {
        type: 'paragraph',
        children: [{ text }],
      });
    },
  });

  useCopilotAction({
    name: "formatText",
    description: "Apply formatting to selected text",
    parameters: [
      {
        name: "format",
        type: "string",
        description: "Format: bold, italic, underline",
        required: true,
      },
    ],
    handler: async ({ format }) => {
      Editor.addMark(editor, format, true);
    },
  });

  const renderElement = useCallback((props: any) => {
    switch (props.element.type) {
      case 'heading':
        return <h1 {...props.attributes}>{props.children}</h1>;
      case 'paragraph':
        return <p {...props.attributes}>{props.children}</p>;
      default:
        return <p {...props.attributes}>{props.children}</p>;
    }
  }, []);

  const renderLeaf = useCallback((props: any) => {
    let { children } = props;

    if (props.leaf.bold) {
      children = <strong>{children}</strong>;
    }

    if (props.leaf.italic) {
      children = <em>{children}</em>;
    }

    return <span {...props.attributes}>{children}</span>;
  }, []);

  return (
    <Slate editor={editor} value={value} onChange={setValue}>
      <Editable
        renderElement={renderElement}
        renderLeaf={renderLeaf}
        placeholder="Start writing..."
        spellCheck
        autoFocus
      />
    </Slate>
  );
}
```

### Advanced Slate Features

**AI-Powered Block Transformations:**
```typescript
import { Transforms, Editor, Node } from 'slate';

async function transformBlockWithAI(editor: Editor, transformation: string) {
  const { selection } = editor;
  if (!selection) return;

  // Get current block
  const [node] = Editor.node(editor, selection);
  const text = Node.string(node);

  // Transform with AI
  const transformed = await getAITransformation(text, transformation);

  // Replace block
  Transforms.insertText(editor, transformed, { at: selection });
}

// Usage
useCopilotAction({
  name: "improveWriting",
  description: "Improve the current paragraph",
  handler: async () => {
    await transformBlockWithAI(editor, 'improve');
  },
});
```

**Document Outline Generation:**
```typescript
function generateOutline(value: Descendant[]): Outline[] {
  const outline: Outline[] = [];

  for (const node of value) {
    if (node.type === 'heading') {
      outline.push({
        level: node.level,
        text: Node.string(node),
        id: node.id,
      });
    }
  }

  return outline;
}

// Make outline available to AI
useCopilotReadable({
  description: "Document outline",
  value: generateOutline(value),
});
```

## Lexical Editor Integration

### Installation

```bash
npm install lexical @lexical/react @lexical/rich-text
```

### Basic Setup

```typescript
// components/LexicalEditor.tsx
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import LexicalErrorBoundary from '@lexical/react/LexicalErrorBoundary';
import { useCopilotReadable, useCopilotAction } from '@copilotkit/react-core';
import { $getRoot, $getSelection, EditorState } from 'lexical';

const theme = {
  // Theme styling
};

function onError(error: Error) {
  console.error(error);
}

export function LexicalEditor() {
  const initialConfig = {
    namespace: 'MyEditor',
    theme,
    onError,
  };

  const handleChange = (editorState: EditorState) => {
    editorState.read(() => {
      const root = $getRoot();
      const text = root.getTextContent();

      // Update store
      useEditorStore.setState({ content: text });
    });
  };

  return (
    <LexicalComposer initialConfig={initialConfig}>
      <RichTextPlugin
        contentEditable={<ContentEditable className="editor-input" />}
        placeholder={<div className="editor-placeholder">Start typing...</div>}
        ErrorBoundary={LexicalErrorBoundary}
      />
      <HistoryPlugin />
      <OnChangePlugin onChange={handleChange} />
      <CopilotPlugin />
    </LexicalComposer>
  );
}

// Custom plugin for CopilotKit integration
function CopilotPlugin() {
  const [editor] = useLexicalComposerContext();

  useCopilotReadable({
    description: "Editor content",
    value: editor.getEditorState().read(() => {
      return $getRoot().getTextContent();
    }),
  });

  useCopilotAction({
    name: "insertText",
    description: "Insert text at cursor",
    parameters: [
      { name: "text", type: "string", required: true },
    ],
    handler: async ({ text }) => {
      editor.update(() => {
        const selection = $getSelection();
        if (selection) {
          selection.insertText(text);
        }
      });
    },
  });

  return null;
}
```

## ReactFlow Integration

### Installation

```bash
npm install reactflow
```

### Basic Setup

```typescript
// components/ReactFlowEditor.tsx
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useCallback } from 'react';
import { useCopilotReadable, useCopilotAction } from '@copilotkit/react-core';

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'input',
    data: { label: 'Start' },
    position: { x: 250, y: 0 },
  },
];

const initialEdges: Edge[] = [];

export function ReactFlowEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Make graph readable
  useCopilotReadable({
    description: "Workflow graph structure",
    value: {
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type,
        label: n.data.label,
        position: n.position,
      })),
      edges: edges.map(e => ({
        source: e.source,
        target: e.target,
      })),
    },
  });

  // AI actions for graph manipulation
  useCopilotAction({
    name: "addNode",
    description: "Add a new node to the workflow",
    parameters: [
      { name: "type", type: "string", description: "Node type", required: true },
      { name: "label", type: "string", description: "Node label", required: true },
      { name: "x", type: "number", description: "X position", required: false },
      { name: "y", type: "number", description: "Y position", required: false },
    ],
    handler: async ({ type, label, x = 250, y = 100 }) => {
      const newNode: Node = {
        id: `node-${Date.now()}`,
        type,
        data: { label },
        position: { x, y },
      };

      setNodes((nds) => [...nds, newNode]);
    },
  });

  useCopilotAction({
    name: "connectNodes",
    description: "Connect two nodes",
    parameters: [
      { name: "sourceId", type: "string", required: true },
      { name: "targetId", type: "string", required: true },
    ],
    handler: async ({ sourceId, targetId }) => {
      const newEdge: Edge = {
        id: `edge-${Date.now()}`,
        source: sourceId,
        target: targetId,
      };

      setEdges((eds) => [...eds, newEdge]);
    },
  });

  useCopilotAction({
    name: "optimizeLayout",
    description: "Automatically optimize node layout",
    handler: async () => {
      // Implement layout algorithm (e.g., force-directed, hierarchical)
      const optimizedNodes = optimizeGraphLayout(nodes, edges);
      setNodes(optimizedNodes);
    },
  });

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges]
  );

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
```

### Custom Nodes with AI

```typescript
// components/CustomNode.tsx
import { Handle, Position, NodeProps } from 'reactflow';
import { useCopilotAction } from '@copilotkit/react-core';

export function CustomNode({ data, id }: NodeProps) {
  useCopilotAction({
    name: `editNode-${id}`,
    description: `Edit node ${id}`,
    parameters: [
      { name: "newLabel", type: "string", required: true },
    ],
    handler: async ({ newLabel }) => {
      // Update node data
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? { ...node, data: { ...node.data, label: newLabel } }
            : node
        )
      );
    },
  });

  return (
    <div className="custom-node">
      <Handle type="target" position={Position.Top} />
      <div>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
```

## TipTap Editor Integration

### Installation

```bash
npm install @tiptap/react @tiptap/starter-kit
```

### Basic Setup

```typescript
// components/TipTapEditor.tsx
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { useCopilotReadable, useCopilotAction } from '@copilotkit/react-core';

export function TipTapEditor() {
  const editor = useEditor({
    extensions: [StarterKit],
    content: '<p>Start writing...</p>',
    onUpdate: ({ editor }) => {
      const text = editor.getText();
      const html = editor.getHTML();

      useEditorStore.setState({
        content: text,
        html,
      });
    },
  });

  if (!editor) return null;

  // Make content readable
  useCopilotReadable({
    description: "Document content",
    value: {
      text: editor.getText(),
      html: editor.getHTML(),
    },
  });

  // AI actions
  useCopilotAction({
    name: "insertText",
    description: "Insert text at cursor",
    parameters: [
      { name: "text", type: "string", required: true },
    ],
    handler: async ({ text }) => {
      editor.commands.insertContent(text);
    },
  });

  useCopilotAction({
    name: "formatSelection",
    description: "Apply formatting to selection",
    parameters: [
      {
        name: "format",
        type: "string",
        description: "bold, italic, heading",
        required: true,
      },
    ],
    handler: async ({ format }) => {
      switch (format) {
        case 'bold':
          editor.chain().focus().toggleBold().run();
          break;
        case 'italic':
          editor.chain().focus().toggleItalic().run();
          break;
        case 'heading':
          editor.chain().focus().toggleHeading({ level: 1 }).run();
          break;
      }
    },
  });

  return (
    <div>
      <MenuBar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  );
}
```

## Common Integration Patterns

### Selection Tracking

```typescript
export function useSelectionTracking(editor: any) {
  useEffect(() => {
    const handleSelectionChange = () => {
      const selection = editor.getSelection();
      const text = editor.getSelectedText();

      useEditorStore.setState({
        selection: {
          start: selection.start,
          end: selection.end,
          text,
        },
      });
    };

    editor.on('selectionChange', handleSelectionChange);

    return () => {
      editor.off('selectionChange', handleSelectionChange);
    };
  }, [editor]);
}
```

### Collaborative Editing

```typescript
// Using Yjs for CRDT-based collaboration
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';

const ydoc = new Y.Doc();
const provider = new WebsocketProvider('ws://localhost:1234', 'room-name', ydoc);

// For Monaco
import { MonacoBinding } from 'y-monaco';
const ytext = ydoc.getText('monaco');
new MonacoBinding(ytext, editor.getModel(), new Set([editor]), provider.awareness);

// For Slate
import { withYjs, YjsEditor } from '@slate-yjs/core';
const editor = withYjs(createEditor(), ydoc.get('content', Y.XmlText));

// For Lexical
import { createBinding } from '@lexical/yjs';
const binding = createBinding(editor, provider, ydoc.get('lexical', Y.XmlText));
```

### Auto-save

```typescript
export function useAutoSave(content: string, interval: number = 30000) {
  useEffect(() => {
    const timer = setInterval(async () => {
      await saveToBackend(content);
    }, interval);

    return () => clearInterval(timer);
  }, [content, interval]);

  // Also save before unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      saveToBackend(content);
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [content]);
}
```

## Best Practices

1. **Debounce Updates**: Don't sync on every keystroke
2. **Virtual Scrolling**: For large documents
3. **Lazy Loading**: Load content on demand
4. **Immutable Updates**: Always create new editor state
5. **Error Boundaries**: Catch editor crashes
6. **Accessibility**: Support keyboard navigation
7. **Mobile Support**: Touch-friendly controls
8. **Undo/Redo**: Implement properly
9. **Auto-save**: Prevent data loss
10. **Performance Monitoring**: Track render times

## Performance Optimization

### Virtualization for Large Documents

```typescript
import { FixedSizeList } from 'react-window';

function VirtualizedEditor({ lines }: { lines: string[] }) {
  const Row = ({ index, style }: any) => (
    <div style={style}>{lines[index]}</div>
  );

  return (
    <FixedSizeList
      height={600}
      itemCount={lines.length}
      itemSize={20}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

### Memoization

```typescript
const MemoizedEditor = memo(({ content }: { content: string }) => {
  return <Editor content={content} />;
}, (prev, next) => prev.content === next.content);
```

## Troubleshooting

**Editor not updating:**
- Check if state updates are immutable
- Verify event listeners are attached
- Check for memo/shouldComponentUpdate blocking

**Performance issues:**
- Add virtualization for large documents
- Debounce state updates
- Use memo for expensive renders

**CopilotKit not working:**
- Verify editor is within CopilotKit provider
- Check that state is being exposed via useCopilotReadable
- Ensure actions are registered properly
