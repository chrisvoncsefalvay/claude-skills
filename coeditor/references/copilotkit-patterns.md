# CopilotKit Integration Patterns

Comprehensive guide to integrating CopilotKit into React applications for AI copilot experiences.

## Core Concepts

### CopilotKit Provider

The `CopilotKit` component wraps your application and provides AI capabilities to all child components.

```typescript
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

function App() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      <CopilotSidebar>
        <YourApp />
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

**Key Props:**
- `runtimeUrl`: Endpoint for AI backend (required)
- `agent`: Specify which agent to use
- `properties`: Additional configuration
- `transcribeAudioUrl`: For voice input (optional)

### Runtime Endpoint

The runtime endpoint connects to your backend. Options:

**1. Direct Backend Connection:**
```typescript
<CopilotKit runtimeUrl="http://localhost:8000/copilot">
```

**2. Next.js API Route:**
```typescript
<CopilotKit runtimeUrl="/api/copilotkit">
```

**3. Serverless Function:**
```typescript
<CopilotKit runtimeUrl="https://your-app.vercel.app/api/copilot">
```

## Context Management

### useCopilotReadable

Make application state readable by the AI:

```typescript
import { useCopilotReadable } from "@copilotkit/react-core";

function DocumentEditor() {
  const document = useDocumentState();

  // Make document readable
  useCopilotReadable({
    description: "The current document being edited",
    value: document,
  });

  // Make selection readable
  useCopilotReadable({
    description: "Currently selected text",
    value: {
      text: document.selection,
      start: document.selectionStart,
      end: document.selectionEnd,
    },
  });

  return <Editor />;
}
```

**Best Practices:**
- Provide clear, descriptive names
- Include relevant context only (don't expose sensitive data)
- Update when state changes (hook handles this automatically)
- Group related state together

### Advanced Context Patterns

**Conditional Context:**
```typescript
useCopilotReadable({
  description: "Selected code block",
  value: selection.type === 'code' ? selection.content : undefined,
  // Only include when relevant
});
```

**Structured Context:**
```typescript
useCopilotReadable({
  description: "Document structure with metadata",
  value: {
    content: document.content,
    metadata: {
      wordCount: countWords(document.content),
      language: document.language,
      lastModified: document.updatedAt,
    },
    outline: generateOutline(document.content),
  },
});
```

**Dynamic Context:**
```typescript
function useEditorContext() {
  const editor = useEditor();

  useCopilotReadable({
    description: "Editor state",
    value: useMemo(() => ({
      content: editor.getContent(),
      cursor: editor.getCursorPosition(),
      selection: editor.getSelection(),
      mode: editor.getMode(),
    }), [editor]),
  });
}
```

## Actions

### useCopilotAction

Define actions the AI can perform:

```typescript
import { useCopilotAction } from "@copilotkit/react-core";

function Editor() {
  const { insertText } = useEditor();

  useCopilotAction({
    name: "insertText",
    description: "Insert text at cursor position",
    parameters: [
      {
        name: "text",
        type: "string",
        description: "The text to insert",
        required: true,
      },
    ],
    handler: async ({ text }) => {
      insertText(text);
      return `Inserted: ${text}`;
    },
  });

  return <EditorComponent />;
}
```

**Parameter Types:**
- `string`: Text input
- `number`: Numeric values
- `boolean`: True/false
- `object`: Complex objects
- `array`: Lists of items

### Common Action Patterns

**1. Text Manipulation:**
```typescript
useCopilotAction({
  name: "replaceText",
  description: "Replace text in selection",
  parameters: [
    {
      name: "newText",
      type: "string",
      description: "Replacement text",
      required: true,
    },
  ],
  handler: async ({ newText }) => {
    const selection = editor.getSelection();
    editor.replaceRange(newText, selection.start, selection.end);
  },
});
```

**2. Content Generation:**
```typescript
useCopilotAction({
  name: "generateSection",
  description: "Generate a new document section",
  parameters: [
    {
      name: "topic",
      type: "string",
      description: "Section topic",
      required: true,
    },
    {
      name: "length",
      type: "number",
      description: "Approximate length in words",
      required: false,
    },
  ],
  handler: async ({ topic, length = 200 }) => {
    const content = await generateContent(topic, length);
    editor.insertSection(content);
    return `Generated section on ${topic}`;
  },
});
```

**3. Analysis Actions:**
```typescript
useCopilotAction({
  name: "analyzeCode",
  description: "Analyze code for issues",
  parameters: [],
  handler: async () => {
    const code = editor.getContent();
    const analysis = await analyzeCode(code);

    return {
      issues: analysis.issues,
      suggestions: analysis.suggestions,
      complexity: analysis.complexity,
    };
  },
});
```

**4. Multi-step Actions:**
```typescript
useCopilotAction({
  name: "refactorCode",
  description: "Refactor selected code",
  parameters: [
    {
      name: "strategy",
      type: "string",
      description: "Refactoring strategy (extract, inline, rename)",
      required: true,
    },
  ],
  handler: async ({ strategy }) => {
    // Step 1: Analyze
    const selection = editor.getSelection();
    const analysis = await analyzeSelection(selection);

    // Step 2: Generate refactoring
    const refactored = await refactor(selection, strategy, analysis);

    // Step 3: Apply changes
    editor.replaceSelection(refactored);

    // Step 4: Format
    await editor.format();

    return `Refactored using ${strategy} strategy`;
  },
});
```

## Chat Integration

### CopilotChat Component

Add a chat interface:

```typescript
import { CopilotChat } from "@copilotkit/react-ui";

function App() {
  return (
    <div className="app">
      <Editor />
      <CopilotChat
        instructions="You are a helpful writing assistant."
        labels={{
          title: "Writing Assistant",
          initial: "How can I help with your document?",
        }}
      />
    </div>
  );
}
```

**Customization:**
```typescript
<CopilotChat
  instructions="Custom system prompt"
  labels={{
    title: "Assistant",
    initial: "Welcome message",
    placeholder: "Type a message...",
  }}
  makeSystemMessage={(message) => ({
    role: "system",
    content: message,
  })}
  showResponseButton={true}
  className="custom-chat"
/>
```

### CopilotSidebar

Chat in a sidebar:

```typescript
import { CopilotSidebar } from "@copilotkit/react-ui";

function App() {
  return (
    <CopilotSidebar
      defaultOpen={false}
      clickOutsideToClose={true}
      labels={{
        title: "AI Assistant",
        initial: "Ask me anything!",
      }}
    >
      <YourApp />
    </CopilotSidebar>
  );
}
```

## Textarea Integration

### CopilotTextarea

AI-enhanced textarea with inline suggestions:

```typescript
import { CopilotTextarea } from "@copilotkit/react-textarea";

function NoteEditor() {
  const [text, setText] = useState("");

  return (
    <CopilotTextarea
      value={text}
      onChange={(e) => setText(e.target.value)}
      placeholder="Start writing..."
      autosuggestionsConfig={{
        textareaPurpose: "Note taking and writing",
        chatApiConfigs: {
          suggestionsApiConfig: {
            maxTokens: 50,
            stop: ["\n\n"],
          },
        },
      }}
      className="w-full h-96 p-4"
    />
  );
}
```

**Configuration:**
- `textareaPurpose`: Describe what the textarea is for
- `maxTokens`: Limit suggestion length
- `stop`: Stop sequences for suggestions
- `debounceTime`: Delay before showing suggestions

## Advanced Patterns

### Custom Agent Selection

```typescript
import { useCopilotContext } from "@copilotkit/react-core";

function AgentSelector() {
  const { setAgent } = useCopilotContext();

  return (
    <select onChange={(e) => setAgent(e.target.value)}>
      <option value="writing_assistant">Writing Assistant</option>
      <option value="code_assistant">Code Assistant</option>
      <option value="researcher">Researcher</option>
    </select>
  );
}
```

### Streaming Responses

Handle streaming for better UX:

```typescript
useCopilotAction({
  name: "generateLongContent",
  description: "Generate long-form content with streaming",
  parameters: [{ name: "topic", type: "string", required: true }],
  handler: async ({ topic }, { stream }) => {
    // Stream content as it's generated
    for await (const chunk of generateContentStream(topic)) {
      await stream(chunk);
    }

    return "Generation complete";
  },
});
```

### Error Handling

```typescript
useCopilotAction({
  name: "riskyAction",
  description: "Action that might fail",
  parameters: [{ name: "input", type: "string", required: true }],
  handler: async ({ input }) => {
    try {
      const result = await performRiskyOperation(input);
      return { success: true, result };
    } catch (error) {
      console.error("Action failed:", error);
      return {
        success: false,
        error: error.message,
      };
    }
  },
});
```

### Conditional Actions

Only enable actions when relevant:

```typescript
function ConditionalActions() {
  const { hasSelection, selectionType } = useEditor();

  // Only register when there's a selection
  useCopilotAction(
    hasSelection
      ? {
          name: "improveSelection",
          description: "Improve selected text",
          handler: async () => {
            const improved = await improveText(getSelection());
            replaceSelection(improved);
          },
        }
      : null
  );

  // Different action for code vs text
  useCopilotAction(
    selectionType === "code"
      ? {
          name: "explainCode",
          description: "Explain selected code",
          handler: async () => {
            return await explainCode(getSelection());
          },
        }
      : {
          name: "summarize",
          description: "Summarize selected text",
          handler: async () => {
            return await summarizeText(getSelection());
          },
        }
  );
}
```

### Context Hooks Pattern

Create reusable context hooks:

```typescript
// hooks/useCopilotEditor.ts
export function useCopilotEditor(editor: Editor) {
  // Make state readable
  useCopilotReadable({
    description: "Editor content",
    value: editor.getContent(),
  });

  useCopilotReadable({
    description: "Current selection",
    value: editor.getSelection(),
  });

  // Define actions
  useCopilotAction({
    name: "insertText",
    description: "Insert text at cursor",
    parameters: [{ name: "text", type: "string", required: true }],
    handler: async ({ text }) => {
      editor.insertText(text);
    },
  });

  useCopilotAction({
    name: "replaceSelection",
    description: "Replace current selection",
    parameters: [{ name: "text", type: "string", required: true }],
    handler: async ({ text }) => {
      editor.replaceSelection(text);
    },
  });
}

// Usage
function Editor() {
  const editor = useEditor();
  useCopilotEditor(editor);

  return <EditorComponent editor={editor} />;
}
```

## Performance Optimization

### Debouncing Context Updates

```typescript
import { useMemo, useDebounce } from "react";

function OptimizedContext() {
  const [content, setContent] = useState("");
  const debouncedContent = useDebounce(content, 500);

  useCopilotReadable({
    description: "Document content",
    value: debouncedContent, // Only update after 500ms of no changes
  });
}
```

### Memoized Values

```typescript
function MemoizedContext() {
  const editor = useEditor();

  const contextValue = useMemo(() => ({
    content: editor.getContent(),
    metadata: editor.getMetadata(),
    outline: generateOutline(editor.getContent()),
  }), [editor.version]); // Only recompute when version changes

  useCopilotReadable({
    description: "Editor state",
    value: contextValue,
  });
}
```

### Selective Context

Only include what's needed:

```typescript
function SelectiveContext() {
  const { content, selection, metadata } = useEditor();
  const { activeAgent } = useAgents();

  // Different context for different agents
  const contextForAgent = useMemo(() => {
    switch (activeAgent) {
      case "writing_assistant":
        return { content, selection };
      case "code_assistant":
        return { content, selection, language: metadata.language };
      case "researcher":
        return { content, metadata };
      default:
        return { content };
    }
  }, [activeAgent, content, selection, metadata]);

  useCopilotReadable({
    description: "Context for current agent",
    value: contextForAgent,
  });
}
```

## Testing

### Testing Actions

```typescript
import { renderHook } from "@testing-library/react-hooks";
import { CopilotKit } from "@copilotkit/react-core";

describe("Copilot Actions", () => {
  it("should register action", async () => {
    const wrapper = ({ children }) => (
      <CopilotKit runtimeUrl="/api/copilot">
        {children}
      </CopilotKit>
    );

    const { result } = renderHook(
      () => {
        useCopilotAction({
          name: "testAction",
          description: "Test action",
          handler: async () => "success",
        });
      },
      { wrapper }
    );

    // Test action registration
  });
});
```

### Mocking CopilotKit

```typescript
jest.mock("@copilotkit/react-core", () => ({
  CopilotKit: ({ children }) => children,
  useCopilotAction: jest.fn(),
  useCopilotReadable: jest.fn(),
}));
```

## Common Patterns

### Document Editor Pattern

```typescript
function DocumentEditor() {
  const { document, updateDocument } = useDocument();

  // Context
  useCopilotReadable({
    description: "Document",
    value: document,
  });

  // Actions
  useCopilotAction({
    name: "updateSection",
    description: "Update a document section",
    parameters: [
      { name: "sectionId", type: "string", required: true },
      { name: "content", type: "string", required: true },
    ],
    handler: async ({ sectionId, content }) => {
      updateDocument((doc) => {
        doc.sections[sectionId].content = content;
      });
    },
  });

  return <Editor document={document} />;
}
```

### Code Editor Pattern

```typescript
function CodeEditor() {
  const { code, language, updateCode } = useCodeEditor();

  useCopilotReadable({
    description: "Current code",
    value: { code, language },
  });

  useCopilotAction({
    name: "completeCode",
    description: "Complete code at cursor",
    handler: async () => {
      const completion = await getCompletion(code, getCursorPosition());
      insertAtCursor(completion);
    },
  });

  useCopilotAction({
    name: "fixBugs",
    description: "Find and fix bugs",
    handler: async () => {
      const fixes = await analyzeBugs(code);
      applyFixes(fixes);
      return `Fixed ${fixes.length} issues`;
    },
  });

  return <MonacoEditor code={code} onChange={updateCode} />;
}
```

### Workflow Editor Pattern

```typescript
function WorkflowEditor() {
  const { nodes, edges, addNode, addEdge } = useWorkflow();

  useCopilotReadable({
    description: "Workflow graph",
    value: { nodes, edges },
  });

  useCopilotAction({
    name: "addNode",
    description: "Add a node to the workflow",
    parameters: [
      { name: "type", type: "string", required: true },
      { name: "label", type: "string", required: true },
    ],
    handler: async ({ type, label }) => {
      const node = createNode(type, label);
      addNode(node);
    },
  });

  useCopilotAction({
    name: "optimizeWorkflow",
    description: "Optimize the workflow layout",
    handler: async () => {
      const optimized = await optimizeLayout(nodes, edges);
      updateWorkflow(optimized);
    },
  });

  return <ReactFlow nodes={nodes} edges={edges} />;
}
```

## Best Practices

1. **Clear Descriptions**: Write clear, actionable descriptions for context and actions
2. **Minimal Context**: Only expose what the AI needs
3. **Type Safety**: Use TypeScript for all parameters
4. **Error Handling**: Always handle errors gracefully
5. **Performance**: Debounce frequent updates
6. **Testing**: Test actions and context in isolation
7. **User Feedback**: Provide visual feedback for actions
8. **Documentation**: Document custom actions for team
9. **Validation**: Validate action parameters
10. **Accessibility**: Ensure keyboard navigation works

## Troubleshooting

**Actions not appearing:**
- Check action name is unique
- Verify handler is async
- Ensure component is within CopilotKit provider

**Context not updating:**
- Verify state changes trigger re-render
- Check useMemo dependencies
- Ensure value is serializable

**Performance issues:**
- Add debouncing to context updates
- Minimize context size
- Use selective context based on agent

**Type errors:**
- Ensure parameter types match
- Check TypeScript version
- Verify CopilotKit types are installed
