// Mock localStorage globally on both window and globalThis at the absolute top
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    clear: () => {
      store = {};
    },
    removeItem: (key: string) => {
      delete store[key];
    },
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock, writable: true });

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ChatInterface from './ChatInterface';
import * as assistantRuntime from '../services/assistantRuntime';

// Mock pure ESM / environment sensitive modules
vi.mock('react-markdown', () => ({
  default: ({ children }: any) => <div>{children}</div>,
}));

vi.mock('remark-gfm', () => ({
  default: () => {},
}));

vi.mock('pdfjs-dist', () => ({
  default: {},
  GlobalWorkerOptions: { workerSrc: '' },
  getDocument: vi.fn(),
}));

// Mock assistantRuntime
vi.mock('../services/assistantRuntime', () => ({
  resolveAssistantQuery: vi.fn(),
}));

// Mock chatMemoryService
vi.mock('../services/chatMemoryService', () => ({
  buildAssistantMemoryContext: vi.fn().mockReturnValue({
    session: {
      conversationSummary: '',
      activeTopic: 'General',
      recentFacts: [],
      openEntities: {}
    },
    longTerm: {
      durableFacts: [],
      relevantMemories: []
    }
  }),
  persistConversationMemory: vi.fn(),
}));

// Mock queryNormalization
vi.mock('../services/queryNormalization', () => ({
  normalizeEmployeeChatText: (text: string) => text,
  isEmployeeSpecificQuestion: () => false,
  isKnownUnsupportedQuestion: () => false,
}));

// Mock the firebase lib specifically used in the component
vi.mock('../lib/firebase', () => ({
  db: {},
  auth: { currentUser: { uid: 'user123' } },
}));

// Dynamic Proxy Mock for Framer Motion / Motion React (Self-contained to avoid hoisting errors)
vi.mock('motion/react', () => {
  const motionProxy = new Proxy({}, {
    get: (target, prop) => {
      return ({ children, ...props }: any) => {
        const Tag = prop as any;
        const { initial, animate, exit, transition, variants, ...cleanProps } = props;
        return <Tag {...cleanProps}>{children}</Tag>;
      };
    }
  });
  return {
    motion: motionProxy,
    AnimatePresence: ({ children }: any) => <>{children}</>,
  };
});

describe('ChatInterface Component Integration Lifecycle', () => {
  const mockUser = {
    uid: 'user123',
    email: 'test@example.com',
    displayName: 'Test User',
  } as any;

  const mockProfile = {
    uid: 'user123',
    role: 'employee' as const,
    grade: 'M2',
    location: 'Ahmedabad',
    displayName: 'Test User',
  } as any;

  it('handles rendering, message submission, AI response, sidebar updates, and switching chat history successfully', async () => {
    vi.mocked(assistantRuntime.resolveAssistantQuery).mockResolvedValue({
      text: 'AI Response Content',
      type: 'general',
      data: { confidenceScore: 0.95, source: 'Grounded Rule', policyId: 'domestic-travel' },
      suggestedQuestions: []
    });

    // 1. Initial Render and Greeting Check
    render(<ChatInterface user={mockUser} profile={mockProfile} />);
    expect(screen.getByText(/Policy Grounded HR Assistant/i)).toBeInTheDocument();
    
    const input = screen.getByPlaceholderText(/Ask anything about Arvind policies or records/i);
    expect(input).toBeInTheDocument();

    // 2. Submit Message and Verify Message + AI Response Rendering
    fireEvent.change(input, { target: { value: 'What is the travel policy?' } });

    const submitButton = screen.getByRole('button', { name: /Secure Ask/i });
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });

    const form = input.closest('form')!;
    fireEvent.submit(form);

    // Yield control to JS event loop to resolve promises and batch state updates
    await new Promise(r => setTimeout(r, 800));

    await waitFor(() => {
      expect(assistantRuntime.resolveAssistantQuery).toHaveBeenCalled();
    });

    // Verify user message bubble renders via direct DOM content check
    await waitFor(() => {
      expect(document.body.textContent).toContain('What is the travel policy?');
    });

    // Verify AI response renders via direct DOM content check
    await waitFor(() => {
      expect(document.body.textContent).toContain('AI Response Content');
    });

    // 3. Inject a historic conversation into localStorage and test switching chats
    const chat1Id = 'chat_999';
    const chats = [{ id: chat1Id, title: 'Previous Chat 999', updatedAt: Date.now() }];
    window.localStorage.setItem(`hr_chats_${mockUser.uid}`, JSON.stringify(chats));
    
    const messages = [
      { id: 'm1', role: 'user', content: 'History message 1', timestamp: Date.now() },
      { id: 'm2', role: 'model', content: 'History Response', timestamp: Date.now() }
    ];
    window.localStorage.setItem(`hr_msgs_${chat1Id}`, JSON.stringify(messages));

    // Clear the current render and re-mount to simulate a fresh load with populated history
    render(<ChatInterface user={mockUser} profile={mockProfile} />);

    const chatButton = await screen.findByText(/Previous Chat 999/i);
    fireEvent.click(chatButton);

    await waitFor(() => {
      expect(document.body.textContent).toContain('History message 1');
      expect(document.body.textContent).toContain('History Response');
    });
  });
});
