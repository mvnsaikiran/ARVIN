import React, { useState, useEffect, useRef } from 'react';
// NO-LOGIN MODE: firebase auth stubbed
import { auth } from '../lib/firebase';
type User = { uid: string; email: string | null; displayName?: string | null; photoURL?: string | null };
const signOut = async (_auth: any) => { window.location.reload(); };
import { UserProfile } from '../lib/useUserProfile';
import type { ChatMessage } from '../services/geminiService';
import { 
  Send, 
  LogOut, 
  Plus, 
  MessageSquare, 
  Bot, 
  User as UserIcon, 
  ThumbsUp, 
  ThumbsDown,
  ChevronLeft,
  Menu,
  ShieldCheck,
  Zap,
  Shield,
  Info,
  Paperclip,
  Check,
  FileText,
  ExternalLink,
  X,
  Search,
  BookOpen,
  Camera,
  LayoutDashboard,
  Wallet,
  Clock,
  Briefcase,
  History as HistoryIcon,
  HelpCircle,
  FileBox,
  Mic,
  MicOff,
  Download,
  BarChart3,
  ChevronRight,
  Square,
  Volume2,
  VolumeX
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';

const HighlightedText = ({ text, highlights }: { text: string; highlights: string[] }) => {
  if (!highlights || highlights.length === 0) return <>{text}</>;
  
  // Filter out short terms and deduplicate
  const terms = highlights.filter(t => t.length > 2);
  if (terms.length === 0) return <>{text}</>;

  const regex = new RegExp(`(${terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
  const parts = text.split(regex);
  
  return (
    <>
      {parts.map((part, i) => 
        regex.test(part) ? (
          <mark key={i} className="bg-amber-200 text-slate-900 rounded-sm px-0.5 font-bold border-b border-amber-400">{part}</mark>
        ) : (
          part
        )
      )}
    </>
  );
};
import { motion, AnimatePresence } from 'motion/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { POLICY_META, ARVIND_POLICIES } from '../data/policies';
import { resolveAssistantQuery } from '../services/assistantRuntime';
import { buildAssistantMemoryContext, persistConversationMemory } from '../services/chatMemoryService';
import {
  AnalyticsSummary,
  ChannelExperience,
  EmployeeRecord,
  EmployeeProfile,
  HRTicket,
  SupportedLanguage,
  createHRTicket,
  getAnalyticsSummary,
  getChannelExperiences,
  getDemoProfiles,
  getEmployeeSelfServiceModules,
  getEmployeeNudges,
  getGuidedJourneys,
  getManagerInsights,
  getManagerTeam,
  getEmployeeRecord,
  getTalentWorkflows,
  listServiceCatalogItems,
  recordAnalyticsEvent,
  recordLearningCase,
  updateAnalyticsFeedback,
} from '../services/employeeExperienceService';
import { normalizeEmployeeChatText } from '../services/queryNormalization';

interface Message {
  id: string;
  role: 'user' | 'model';
  content: string;
  timestamp: any;
  imagePreview?: string | null;
  metadata?: any;
  data?: any;
  suggestedQuestions?: string[];
  type?: string;
}

interface Chat {
  id: string;
  title: string;
  updatedAt: any;
}

interface UploadedKnowledgeFile {
  id: string;
  policyId: string;
  name: string;
  sourceDocumentName: string;
  size: number;
  type: string;
  fileUrl?: string;
  content?: string;
}

const DEMO_PROFILES = getDemoProfiles();

function getSpeechLanguage(language: SupportedLanguage) {
  if (language === 'hindi') return 'hi-IN';
  if (language === 'gujarati') return 'gu-IN';
  return 'en-IN';
}

function getConfidenceBadge(score?: number) {
  if (score === undefined) return { label: 'Needs HR confirmation', tone: 'bg-slate-100 text-slate-600', dot: 'bg-slate-400' };
  if (score >= 0.9) return { label: 'High confidence', tone: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' };
  if (score >= 0.75) return { label: 'Use with quick review', tone: 'bg-amber-50 text-amber-700', dot: 'bg-amber-500' };
  return { label: 'Needs HR confirmation', tone: 'bg-rose-50 text-rose-700', dot: 'bg-rose-500' };
}

function shouldOfferEscalation(message: Message) {
  if (message.role !== 'model') return false;
  const confidence = message.metadata?.confidenceScore ?? 0;
  const policyId = message.metadata?.policyId;
  return (
    message.type === 'error' ||
    confidence < 0.78 ||
    ['posh-policy', 'grievance-mechanism', 'whistleblower', 'gender-policy'].includes(policyId)
  );
}

function buildPolicyDocumentUrl(baseFileUrl?: string, pageNum?: number, highlightTerms: string[] = []) {
  if (!baseFileUrl) return "";

  const isPdf = /\.pdf($|[?#])/i.test(baseFileUrl);
  if (!isPdf) return baseFileUrl;

  const fragments: string[] = [];
  if (pageNum) fragments.push(`page=${pageNum}`);
  if (highlightTerms.length > 0) {
    fragments.push(`search=${encodeURIComponent(highlightTerms[0])}`);
  }

  return fragments.length > 0 ? `${baseFileUrl}#${fragments.join("&")}` : baseFileUrl;
}

function canPreviewPolicyInFrame(fileUrl?: string) {
  return !!fileUrl && (/\.pdf($|[?#])/i.test(fileUrl) || /\.html($|[?#])/i.test(fileUrl));
}

function buildUploadedPolicyId(fileName: string) {
  return fileName
    .replace(/\.[^/.]+$/, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function getPolicySourceLabel(
  linkedPolicy?: { sourceDocumentName?: string; name?: string } | null,
  linkedUploadedFile?: { name: string; sourceDocumentName?: string } | null,
  metadataSource?: string
) {
  if (linkedUploadedFile?.sourceDocumentName) return linkedUploadedFile.sourceDocumentName;
  if (linkedUploadedFile?.name) return linkedUploadedFile.name;
  if (linkedPolicy?.sourceDocumentName) return linkedPolicy.sourceDocumentName;
  if (linkedPolicy?.name) return linkedPolicy.name;
  return metadataSource || 'Arvind Limited Official Policy Document';
}

function formatMetadataDate(value?: string | number) {
  if (!value) return null;
  const date = typeof value === 'number' ? new Date(value) : new Date(value);
  if (Number.isNaN(date.getTime())) return typeof value === 'string' ? value : null;
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

export default function ChatInterface({ 
  user, 
  profile, 
  onOpenAdmin,
  onSwitchPersona,
}: { 
  user: User, 
  profile: UserProfile,
  onOpenAdmin?: () => void,
  onSwitchPersona?: (uid: string) => void,
}) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showUploadSuccess, setShowUploadSuccess] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, number>>({});
  const [isPolicyViewerOpen, setIsPolicyViewerOpen] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<any>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedKnowledgeFile[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'dashboard' | 'manager'>('chat');
  const [language, setLanguage] = useState<SupportedLanguage>(profile.languagePreference || 'english');
  const [showTeamsPreview, setShowTeamsPreview] = useState(false);
  const [nudges, setNudges] = useState(getEmployeeNudges(profile));
  const [imageAttachment, setImageAttachment] = useState<{ mimeType: string, data: string, previewUrl: string } | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [precisionMode, setPrecisionMode] = useState(false);
  const [huggingFaceMode, setHuggingFaceMode] = useState(false);
  const [activeSpeakingId, setActiveSpeakingId] = useState<string | null>(null);

  useEffect(() => {
    window.speechSynthesis.cancel();
    setActiveSpeakingId(null);
    return () => {
      window.speechSynthesis.cancel();
    };
  }, [currentChatId, activeTab]);

  const speakMessage = (messageId: string, text: string) => {
    if (activeSpeakingId === messageId) {
      window.speechSynthesis.cancel();
      setActiveSpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();

    // Strip Markdown symbols for a cleaner voice read
    const cleanText = text
      .replace(/[*_`#~]/g, '') // remove markdown symbols
      .replace(/\[File:[^\]]+\]/g, '') // remove file attachment markers
      .replace(/\|/g, ' ') // remove table pipes
      .replace(/-{3,}/g, ' ') // remove dashes
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const targetLang = getSpeechLanguage(language);
    utterance.lang = targetLang;

    // Explicitly target and assign a premium Indian locale voice accent
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      const voices = window.speechSynthesis.getVoices();
      console.log("SpeechSynthesis available voices:", voices.map(v => `${v.name} (${v.lang})`));
      
      const targetLangLower = targetLang.toLowerCase();
      
      // 1. Filter voices that are exact matches for the target language (e.g., en-IN, hi-IN, gu-IN)
      const exactLangVoices = voices.filter(v => {
        const voiceLang = v.lang.toLowerCase().replace('_', '-');
        return voiceLang === targetLangLower || voiceLang.startsWith(targetLangLower + '-');
      });

      let selectedVoice = null;

      if (exactLangVoices.length > 0) {
        // Try to find a premium or natural Indian voice first in exact matches
        selectedVoice = exactLangVoices.find(v => {
          const name = v.name.toLowerCase();
          return name.includes('natural') || name.includes('google') || name.includes('rishi') || name.includes('heera') || name.includes('ravi') || name.includes('neerja') || name.includes('kalpana');
        }) || exactLangVoices[0];
      }

      // 2. Fallback: Search for any Indian voice (contains 'india', 'indian', '-IN', '_IN' in language or name)
      if (!selectedVoice) {
        selectedVoice = voices.find(v => {
          const name = v.name.toLowerCase();
          const lang = v.lang.toLowerCase().replace('_', '-');
          return lang.endsWith('-in') || name.includes('india') || name.includes('indian');
        });
      }

      // 3. Fallback: Search for specific Indian voice names
      if (!selectedVoice) {
        const indianNames = ['veena', 'rishi', 'priya', 'ravi', 'heera', 'neerja', 'kalpana', 'hemant', 'harsh', 'karan'];
        selectedVoice = voices.find(v => {
          const name = v.name.toLowerCase();
          return indianNames.some(indianName => name.includes(indianName));
        });
      }

      if (selectedVoice) {
        console.log(`Setting speech voice: ${selectedVoice.name} (${selectedVoice.lang})`);
        utterance.voice = selectedVoice;
      } else {
        console.warn(`No specific Indian voice found for ${targetLang}. Using browser default.`);
      }
      
      // Setting parameters for high quality speech experience
      utterance.rate = 0.95; // Slightly slower for better clarity and comprehension
      utterance.pitch = 1.0;
    }

    utterance.onend = () => {
      setActiveSpeakingId(null);
    };

    utterance.onerror = () => {
      setActiveSpeakingId(null);
    };

    setActiveSpeakingId(messageId);
    window.speechSynthesis.speak(utterance);
  };

  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const employeeRecord = getEmployeeRecord(profile.uid);
  const guidedJourneys = getGuidedJourneys(profile);
  const analyticsSummary = getAnalyticsSummary();
  const managerTeam = getManagerTeam(profile.uid);
  const hasOperationsHub = profile.role !== 'employee';
  const hubLabel = profile.role === 'manager'
    ? 'Manager Hub'
    : profile.role === 'hrbp'
      ? 'HRBP Hub'
      : profile.role === 'admin'
        ? 'Admin Hub'
        : 'People Ops';

  useEffect(() => {
    setLanguage(profile.languagePreference || 'english');
    setNudges(getEmployeeNudges(profile));
    if (profile.role === 'employee' && activeTab === 'manager') {
      setActiveTab('dashboard');
    }
  }, [profile]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);
    const totalFiles = files.length;

    const syncedFiles: UploadedKnowledgeFile[] = [];
    const failedFiles: string[] = [];

    try {
      for (let i = 0; i < totalFiles; i++) {
        const file = files[i];
        setUploadProgress(Math.round((i / totalFiles) * 100));

        try {
          const formData = new FormData();
          formData.append('file', file);

          const response = await fetch('/api/policies/upload', {
            method: 'POST',
            body: formData,
          });

          const payload = await response.json().catch(() => ({}));
          if (!response.ok || !payload.success) {
            throw new Error(payload.error || `Upload failed with status ${response.status}`);
          }

          const policyId = payload.policyId || buildUploadedPolicyId(file.name);
          syncedFiles.push({
            id: `${policyId}-${Date.now()}-${i}`,
            policyId,
            name: file.name,
            sourceDocumentName: payload.sourceDocumentName || file.name,
            size: file.size,
            type: file.type,
            fileUrl: payload.fileUrl,
          });
        } catch (error) {
          failedFiles.push(`${file.name}: ${error instanceof Error ? error.message : String(error)}`);
        }

        setUploadProgress(Math.round(((i + 1) / totalFiles) * 100));
      }
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 350);
    }

    if (syncedFiles.length > 0) {
      setUploadedFiles(prev => {
        const existing = prev.filter(file => !syncedFiles.some(synced => synced.policyId === file.policyId));
        return [...syncedFiles, ...existing];
      });
      setShowUploadSuccess(true);
      setTimeout(() => setShowUploadSuccess(false), 2000);
    }

    if (failedFiles.length > 0) {
      window.alert(`Some policy files could not be synchronized:\n\n${failedFiles.join('\n')}`);
    }

    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Local chat store - persisted to localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(`hr_chats_${user.uid}`);
      if (stored) setChats(JSON.parse(stored));
    } catch {}
  }, [user.uid]);

  const saveChats = (updated: Chat[]) => {
    setChats(updated);
    try { localStorage.setItem(`hr_chats_${user.uid}`, JSON.stringify(updated)); } catch {}
  };

  const saveMessages = (chatId: string, msgs: Message[]) => {
    setMessages(msgs);
    try { localStorage.setItem(`hr_msgs_${chatId}`, JSON.stringify(msgs)); } catch {}
  };

  useEffect(() => {
    if (!currentChatId) { setMessages([]); return; }
    try {
      const stored = localStorage.getItem(`hr_msgs_${currentChatId}`);
      if (stored) setMessages(JSON.parse(stored));
      else setMessages([]);
    } catch { setMessages([]); }
  }, [currentChatId]);

  const createNewChat = () => {
    const id = `chat_${Date.now()}`;
    const newChat: Chat = { id, title: 'New Conversation', updatedAt: Date.now() };
    saveChats([newChat, ...chats]);
    setCurrentChatId(id);
  };

  const handleImageCapture = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert("Please select an image file.");
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64 = event.target?.result as string;
      const data = base64.split(',')[1];
      setImageAttachment({
        mimeType: file.type,
        data: data,
        previewUrl: base64
      });
    };
    reader.readAsDataURL(file);
  };
  
  const toggleListening = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }

    // @ts-ignore
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = getSpeechLanguage(language);

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(prev => prev + (prev ? ' ' : '') + transcript);
    };

    recognition.start();
  };

  const exportChat = () => {
    const chatContent = messages.map(m => `[${m.role.toUpperCase()}] ${m.content}`).join('\n\n---\n\n');
    const blob = new Blob([`Arvind HR Pulse Chat Export\nGenerated: ${new Date().toLocaleString()}\n\n${chatContent}`], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `HR_Pulse_Chat_${currentChatId?.slice(0, 5) || 'Export'}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if ((!input.trim() && !imageAttachment) || isTyping) return;

    let chatId = currentChatId;
    const userMessage = input.trim();
    const normalizedUserMessage = normalizeEmployeeChatText(userMessage);
    const currentAttachment = imageAttachment;
    const startedAt = Date.now();
    
    setInput('');
    setImageAttachment(null);
    
    if (abortControllerRef.current) abortControllerRef.current.abort();
    abortControllerRef.current = new AbortController();

    // Ensure a chat session exists
    if (!chatId) {
      chatId = `chat_${Date.now()}`;
      const newChat: Chat = { id: chatId, title: userMessage.slice(0, 40) || 'New Scan', updatedAt: Date.now() };
      const updatedChats = [newChat, ...chats];
      saveChats(updatedChats);
      setCurrentChatId(chatId);
    } else {
      const updatedChats = chats.map(c =>
        c.id === chatId
          ? { ...c, title: c.title === 'New Conversation' ? (userMessage.slice(0, 40) || 'Image Scan') : c.title, updatedAt: Date.now() }
          : c
      );
      saveChats(updatedChats);
    }

    const userMsg: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: userMessage || 'Analyzing image...',
      timestamp: Date.now(),
      imagePreview: currentAttachment?.previewUrl || null,
    };

    const updatedMessages = [...messages, userMsg];
    saveMessages(chatId, updatedMessages);
    setIsTyping(true);

    try {
      const history: ChatMessage[] = updatedMessages
        .filter(m => m && m.role && m.content)
        .slice(-10)
        .map(m => ({ role: m.role, parts: [{ text: m.content }] }));
      const memoryContext = precisionMode
        ? undefined
        : buildAssistantMemoryContext({
            userUid: profile.uid,
            chatId,
            messages: updatedMessages.map((message) => ({
              role: message.role,
              content: message.content,
              metadata: message.metadata,
              timestamp: typeof message.timestamp === 'number' ? message.timestamp : undefined,
            })),
            query: userMessage,
          });

      const aiResponse = await resolveAssistantQuery({
        message: userMessage,
        history,
        profile,
        language,
        knowledgeAssets: uploadedFiles,
        imageAttachment: currentAttachment ? { mimeType: currentAttachment.mimeType, data: currentAttachment.data } : undefined,
        memoryContext,
        precisionMode,
        huggingFaceMode,
        signal: abortControllerRef.current?.signal,
      });

      const interactionId = `msg_${Date.now() + 1}`;
      const aiMsg: Message = {
        id: interactionId,
        role: 'model',
        content: aiResponse.text,
        timestamp: Date.now(),
        metadata: aiResponse.data || null,
        suggestedQuestions: aiResponse.suggestedQuestions || [],
        type: aiResponse.type,
      };
      const finalMessages = [...updatedMessages, aiMsg];
      saveMessages(chatId, finalMessages);
      if (!precisionMode) {
        persistConversationMemory({
          userUid: profile.uid,
          chatId,
          messages: finalMessages.map((message) => ({
            role: message.role,
            content: message.content,
            metadata: message.metadata,
            timestamp: typeof message.timestamp === 'number' ? message.timestamp : undefined,
          })),
          profile,
          language,
        });
      }
      const actionMetadata = aiResponse.data && 'action' in aiResponse.data ? (aiResponse.data as any).action : undefined;
      const analyticsMetadata = (aiResponse.data ?? {}) as any;

      recordAnalyticsEvent({
        id: interactionId,
        query: userMessage,
        normalizedQuery: normalizedUserMessage,
        userUid: profile.uid,
        userRole: profile.role,
        grade: profile.grade,
        location: profile.location,
        responseType: aiResponse.type,
        policyId: aiResponse.data?.policyId,
        confidenceScore: aiResponse.data?.confidenceScore,
        escalated: !!actionMetadata?.caseId,
        unresolved: aiResponse.type === 'error',
        highRisk: analyticsMetadata?.safetyMode === 'high_risk',
        clarificationRequested: !!analyticsMetadata?.clarificationNeeded,
        usedLearningCase: !!analyticsMetadata?.learnedFromCaseId,
        safetyMode: analyticsMetadata?.safetyMode,
        turnaroundMs: Date.now() - startedAt,
        timestamp: Date.now(),
      });
    } catch (error: any) {
      if (error.message === 'Aborted') return;
      console.error('Message error:', error);
      const errId = `msg_err_${Date.now()}`;
      const errMsg: Message = {
        id: errId,
        role: 'model',
        content: "I'm having trouble connecting. Please check your internet connection or try again.",
        type: 'error',
        timestamp: Date.now(),
      };
      saveMessages(chatId, [...updatedMessages, errMsg]);
      recordAnalyticsEvent({
        id: errId,
        query: userMessage,
        normalizedQuery: normalizedUserMessage,
        userUid: profile.uid,
        userRole: profile.role,
        grade: profile.grade,
        location: profile.location,
        responseType: 'error',
        unresolved: true,
        turnaroundMs: Date.now() - startedAt,
        timestamp: Date.now(),
      });
    } finally {
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  };

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsTyping(false);
  };

  const appendWorkflowMessage = (content: string, data?: any) => {
    if (!currentChatId) return;
    const workflowMessage: Message = {
      id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      role: 'model',
      content,
      timestamp: Date.now(),
      metadata: data || null,
      type: 'action_trigger',
    };
    saveMessages(currentChatId, [...messages, workflowMessage]);
  };

  const handleEscalationAction = (kind: HRTicket["kind"], message: Message) => {
    const route = kind === 'posh' ? 'AIC' : kind === 'whistleblower' ? 'Ethics Helpline' : 'BUHR';
    const confidentiality = kind === 'posh' || kind === 'whistleblower' ? 'strictly-confidential' : 'confidential';
    const caseRecord = createHRTicket({
      kind,
      title: `${kind.replace(/_/g, ' ')} follow-up from chatbot`,
      summary: message.content,
      confidentiality,
      route,
      priority: kind === 'posh' ? 'critical' : kind === 'whistleblower' ? 'high' : 'medium',
      employeeUid: profile.uid,
      employeeName: profile.displayName,
      employeeGrade: profile.grade,
      employeeLocation: profile.location,
      assignedTo: route,
      transcriptExcerpt: messages.slice(-6).map((item) => `${item.role}: ${item.content}`).join('\n\n'),
      sourcePolicyId: message.metadata?.policyId,
    });

    appendWorkflowMessage(
      `A ${confidentiality === 'strictly-confidential' ? 'strictly confidential ' : ''}${kind.replace(/_/g, ' ')} case has been created.\n\n- Case ID: **${caseRecord.id}**\n- Route: **${caseRecord.route}**\n- Status: **${caseRecord.status}**\n- Assigned Queue: **${caseRecord.assignedTo}**`,
      {
        confidenceScore: 1,
        source: 'HR Case Workflow',
        action: { type: 'case_created', caseId: caseRecord.id, route: caseRecord.route },
      }
    );
  };

  const emailTranscriptToHR = () => {
    const caseRecord = createHRTicket({
      kind: 'hr_ticket',
      title: 'Chat transcript shared with HR',
      summary: 'Employee requested HR follow-up on the current chat transcript.',
      confidentiality: 'confidential',
      route: 'BUHR',
      priority: 'medium',
      employeeUid: profile.uid,
      employeeName: profile.displayName,
      employeeGrade: profile.grade,
      employeeLocation: profile.location,
      assignedTo: profile.managerName,
      transcriptExcerpt: messages.map((item) => `${item.role}: ${item.content}`).join('\n\n'),
    });

    appendWorkflowMessage(
      `Your chat transcript is ready for HR follow-up.\n\n- Workflow ID: **${caseRecord.id}**\n- Route: **BUHR**\n- Next owner: **${profile.managerName} / ${employeeRecord.approverChain.buhr}**`,
      {
        confidenceScore: 1,
        source: 'Transcript Routing Workflow',
        action: { type: 'email_transcript', caseId: caseRecord.id, route: 'BUHR' },
      }
    );
  };

  const handleJourneyPrompt = (prompt: string) => {
    setInput(prompt);
    setTimeout(() => {
      const sendBtn = document.getElementById('chat-send-button');
      sendBtn?.click();
    }, 80);
  };

  const switchRole = (targetUid: string) => {
    onSwitchPersona?.(targetUid);
    setActiveTab('chat');
    setCurrentChatId(null);
    setMessages([]);
  };

  const downloadPolicy = (policy: any) => {
    if (policy.fileUrl) {
      const url = policy.fileUrl.split('#')[0];
      const extension = url.split('.').pop()?.toLowerCase() || 'pdf';
      const filename = policy.sourceDocumentName
        || decodeURIComponent(url.split('/').pop() || `${policy.id}.${extension}`);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      return;
    }

    const filename = `${policy.id || 'policy'}.txt`;
    const blob = new Blob([policy.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleFeedback = (messageId: string, rating: number) => {
    if (feedbackSent[messageId]) return;
    setFeedbackSent(prev => ({ ...prev, [messageId]: rating }));
    const feedbackReason = rating === 1
      ? window.prompt('What was not useful about this answer? You can leave this blank if you want.') || undefined
      : undefined;
    updateAnalyticsFeedback(messageId, rating as 1 | 5, feedbackReason);

    if (rating === 5) {
      const messageIndex = messages.findIndex((item) => item.id === messageId);
      const approvedMessage = messageIndex >= 0 ? messages[messageIndex] : null;
      const priorUserMessage = messageIndex > 0
        ? [...messages.slice(0, messageIndex)].reverse().find((item) => item.role === 'user')
        : null;

      if (approvedMessage && priorUserMessage) {
        recordLearningCase({
          query: priorUserMessage.content,
          approvedAnswer: approvedMessage.content,
          policyId: approvedMessage.metadata?.policyId,
          source: 'feedback',
          confidence: Math.max(0.85, approvedMessage.metadata?.confidenceScore ?? 0.85),
        });
      }
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <AnimatePresence initial={false}>
        {isSidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 320, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="flex-shrink-0 bg-white border-r border-slate-200 h-full flex flex-col z-20"
          >
            <div className="p-6 flex items-center justify-between border-b border-slate-50">
              <h2 className="text-xl font-semibold tracking-tight text-slate-800">My History</h2>
              <button 
                onClick={() => {
                  setCurrentChatId(null);
                  setMessages([]);
                }}
                className="p-2 bg-slate-50 border border-slate-200 rounded-xl hover:bg-indigo-50 hover:border-indigo-100 transition-all text-indigo-600"
                title="New Chat"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
              <div className="px-3 pt-4 pb-2">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Conversations</p>
              </div>
              {chats.map(chat => (
                <button
                  key={chat.id}
                  onClick={() => setCurrentChatId(chat.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all ${
                    currentChatId === chat.id 
                      ? 'bg-indigo-50 border border-indigo-100' 
                      : 'hover:bg-slate-50 border border-transparent'
                  }`}
                >
                  <MessageSquare className={`w-4 h-4 ${currentChatId === chat.id ? 'text-indigo-600' : 'text-slate-400'}`} />
                  <span className={`text-sm truncate flex-1 font-medium ${currentChatId === chat.id ? 'text-indigo-900' : 'text-slate-600'}`}>
                    {chat.title}
                  </span>
                </button>
              ))}

              <div className="px-3 pt-6 pb-2">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Official Policies</p>
              </div>
              <div className="space-y-1">
                {POLICY_META.map(policy => (
                  <a
                    key={policy.id}
                    href={policy.fileUrl}
                    target={policy.fileUrl.endsWith('.pdf') ? "_blank" : undefined}
                    download={policy.fileUrl.endsWith('.pdf') ? undefined : (policy.sourceDocumentName || true)}
                    rel="noopener noreferrer"
                    className="w-full flex items-center gap-3 px-4 py-2 rounded-xl text-left hover:bg-slate-50 border border-transparent transition-all group"
                  >
                    <FileText className="w-4 h-4 text-slate-400 group-hover:text-indigo-600" />
                    <span className="text-sm truncate text-slate-600 group-hover:text-slate-900">
                      {policy.name}
                    </span>
                    {policy.fileUrl.endsWith('.pdf') ? (
                      <ExternalLink className="w-3 h-3 text-slate-300 opacity-0 group-hover:opacity-100 transition-all ml-auto" />
                    ) : (
                      <Download className="w-3 h-3 text-slate-300 opacity-0 group-hover:opacity-100 transition-all ml-auto" />
                    )}
                  </a>
                ))}
              </div>

              {(uploadedFiles.length > 0 || isUploading) && (
                <>
                  <div className="px-3 pt-6 pb-2 flex items-center justify-between">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Knowledge Base</p>
                    <button 
                      onClick={() => fileInputRef.current?.click()}
                      className="p-1 hover:bg-slate-200 rounded-md transition-colors"
                      title="Sync new documents"
                    >
                      <Paperclip className="w-3 h-3 text-slate-400" />
                    </button>
                  </div>
                  
                  {isUploading && (
                    <div className="mx-3 mb-2 px-4 py-3 rounded-xl bg-indigo-50 border border-indigo-100/50 shadow-sm overflow-hidden relative">
                      <div className="flex items-center gap-3 relative z-10">
                        <div className="p-1.5 bg-indigo-600 rounded-lg shrink-0">
                          <Zap className="w-3.5 h-3.5 text-white animate-pulse" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-center mb-1">
                            <p className="text-[11px] font-black text-indigo-900 uppercase tracking-tight">Syncing...</p>
                            <span className="text-[10px] font-black text-indigo-600 tabular-nums">{uploadProgress}%</span>
                          </div>
                          <div className="w-full bg-indigo-200/50 h-1 rounded-full overflow-hidden">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${uploadProgress}%` }}
                              className="h-full bg-indigo-600"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {uploadedFiles.map(file => (
                    <button
                      key={file.id}
                      onClick={() => {
                        setSelectedPolicy({
                          name: file.name,
                          sourceDocumentName: file.sourceDocumentName,
                          content: file.content,
                          fileUrl: file.fileUrl,
                          id: file.policyId || file.id
                        });
                        setIsPolicyViewerOpen(true);
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-50 border border-slate-100 group transition-all text-left hover:bg-white hover:shadow-md active:scale-[0.98]"
                    >
                      <div className="p-1.5 bg-white rounded-lg border border-slate-100 group-hover:bg-indigo-50 group-hover:border-indigo-100 transition-colors">
                        <FileText className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] font-bold text-slate-700 truncate">{file.name}</p>
                        <p className="text-[9px] text-slate-400 font-bold uppercase">{(file.size / 1024).toFixed(1)} KB • Live Policy Sync</p>
                      </div>
                      <ExternalLink className="w-3 h-3 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </>
              )}
            </div>

            <div className="p-4 border-t border-slate-100 space-y-4">
              {/* Persona Switcher */}
              <div className="px-4 py-3 bg-indigo-50/50 rounded-2xl border border-indigo-100/50">
                <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2">Experience Mode</p>
                <div className="grid grid-cols-2 gap-2">
                  {DEMO_PROFILES.map((persona) => (
                    <button
                      key={persona.uid}
                      onClick={() => switchRole(persona.uid)}
                      className={`text-[10px] py-1.5 rounded-lg font-bold uppercase transition-all ${
                        profile?.uid === persona.uid ? 'bg-indigo-600 text-white shadow-sm' : 'bg-white text-slate-400 hover:text-indigo-600'
                      }`}
                    >
                      {persona.role === 'employee' ? 'Employee' : persona.role === 'manager' ? 'Manager' : persona.role === 'hrbp' ? 'HRBP' : 'Admin'}
                    </button>
                  ))}
                </div>
              </div>

              {onOpenAdmin && (
                <button 
                  onClick={onOpenAdmin}
                  className="w-full flex items-center gap-3 px-4 py-3 bg-slate-900 text-white rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-slate-800 transition-all shadow-lg shadow-slate-200"
                >
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Operations Center
                </button>
              )}

              <div className="flex items-center gap-3 px-4 py-3 bg-slate-50 rounded-2xl border border-slate-100">
                <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 text-xs font-bold">
                  {user.displayName?.[0] || user.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">{user.displayName || user.email}</p>
                  <p className="text-[10px] text-slate-400 font-bold uppercase">{profile?.role || 'User'} • {profile.grade} • {profile.location}</p>
                </div>
                <button onClick={() => signOut(auth)} className="text-slate-400 hover:text-red-500 transition-colors">
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <main className="flex-1 flex flex-col bg-slate-50/50 min-w-0 relative">
        <header className="h-20 bg-white border-b border-slate-100 px-6 flex items-center justify-between sticky top-0 z-10 backdrop-blur-md">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 text-slate-500 hover:bg-slate-50 rounded-xl transition-colors"
            >
              {isSidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-100">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold tracking-tight text-slate-900 leading-none mb-1">Arvind HR Pulse</h1>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                  Enterprise Mode Active
                </p>
              </div>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-4 px-4 py-2 bg-slate-100 rounded-xl border border-slate-200/50">
             <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
             <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">HRIS Sync Online</p>
          </div>
        </header>

        <div className="bg-white border-b border-slate-200 flex px-6 items-center justify-between">
          <div className="flex">
            <button 
              onClick={() => setActiveTab('chat')}
              className={`px-6 py-4 flex items-center gap-2 text-xs font-bold uppercase tracking-widest border-b-2 transition-all ${
                activeTab === 'chat' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              <MessageSquare className="w-4 h-4" /> Smart Chat
            </button>
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`px-6 py-4 flex items-center gap-2 text-xs font-bold uppercase tracking-widest border-b-2 transition-all ${
                activeTab === 'dashboard' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" /> My Dashboard
            </button>
            {hasOperationsHub && (
              <button 
                onClick={() => setActiveTab('manager')}
                className={`px-6 py-4 flex items-center gap-2 text-xs font-bold uppercase tracking-widest border-b-2 transition-all ${
                  activeTab === 'manager' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'
                }`}
              >
                <ShieldCheck className="w-4 h-4" /> {hubLabel}
              </button>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            {hasOperationsHub && (
              <button 
                onClick={() => setShowTeamsPreview(!showTeamsPreview)}
                className={`p-2 rounded-lg text-[10px] font-black uppercase tracking-tighter border transition-all ${
                  showTeamsPreview ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-slate-50 text-slate-400 border-slate-200'
                }`}
              >
                {showTeamsPreview ? 'Teams Mode ON' : 'Teams Preview'}
              </button>
            )}
            <button 
              onClick={() => setPrecisionMode(!precisionMode)}
              className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                precisionMode ? 'bg-amber-100 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-600'
              } border`}
            >
              {precisionMode ? 'Precision ON' : 'Standard'}
            </button>
            <button 
              onClick={() => {
                setHuggingFaceMode(!huggingFaceMode);
                if (!huggingFaceMode) setPrecisionMode(false);
              }}
              className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                huggingFaceMode ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-600'
              } border`}
            >
              {huggingFaceMode ? '🛡️ Llama-3 ON' : 'Hugging Face'}
            </button>
            <button 
              onClick={() => setLanguage(language === 'english' ? 'hindi' : language === 'hindi' ? 'gujarati' : 'english')}
              className="px-3 py-1 bg-slate-100 text-slate-600 rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-indigo-50 transition-colors"
            >
              {language === 'english' ? 'English' : language === 'hindi' ? 'Hindi' : 'Gujarati'}
            </button>
          </div>
        </div>

        <div ref={scrollRef} className={`flex-1 overflow-y-auto px-6 py-8 space-y-8 scroll-smooth ${showTeamsPreview ? 'max-w-3xl mx-auto border-x border-slate-200 bg-emerald-50/10' : ''}`}>
          
          {/* Proactive Nudges */}
          <AnimatePresence>
            {nudges.length > 0 && activeTab === 'chat' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-3 mb-6 max-w-6xl mx-auto w-full"
              >
                {nudges.map((nudge) => (
                  <div key={nudge.id} className="bg-indigo-600/5 border border-indigo-600/10 rounded-2xl p-4 flex items-center justify-between group">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${nudge.type === 'alert' ? 'bg-rose-500 animate-pulse' : 'bg-indigo-500'}`}></div>
                      <p className="text-xs font-bold text-slate-700">{nudge.text}</p>
                    </div>
                    <button 
                      onClick={() => setNudges(nudges.filter(n => n.id !== nudge.id))}
                      className="p-1 text-slate-300 hover:text-slate-600 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {activeTab === 'dashboard' ? (
            <DashboardView profile={profile} user={user} employeeRecord={employeeRecord} analyticsSummary={analyticsSummary} onJourneySelect={handleJourneyPrompt} />
          ) : activeTab === 'manager' ? (
            <ManagerDashboardView profile={profile} teamMembers={managerTeam} analyticsSummary={analyticsSummary} onJourneySelect={handleJourneyPrompt} />
          ) : messages.length === 0 ? (
            <div className="max-w-6xl mx-auto w-full space-y-8 pb-8">
              <section className="relative overflow-hidden rounded-[2rem] border border-indigo-100 bg-gradient-to-br from-white via-indigo-50/50 to-slate-100 px-6 py-8 md:px-10 md:py-10 shadow-xl shadow-slate-200/40">
                <div className="absolute -right-12 -top-12 h-36 w-36 rounded-full bg-indigo-200/30 blur-3xl" />
                <div className="absolute -left-10 bottom-0 h-28 w-28 rounded-full bg-cyan-200/20 blur-3xl" />
                <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-2xl">
                    <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-white/80 px-3 py-1 text-[10px] font-black uppercase tracking-[0.24em] text-indigo-500 shadow-sm">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Policy Grounded HR Assistant
                    </div>
                    <div className="mb-5 flex items-center gap-4">
                      <div className="flex h-16 w-16 items-center justify-center rounded-[1.75rem] bg-indigo-600 text-white shadow-xl shadow-indigo-200">
                        <Bot className="h-8 w-8" />
                      </div>
                      <div>
                        <h3 className="text-3xl font-black tracking-tight text-slate-950 md:text-4xl">
                          {user.displayName ? `Welcome, ${user.displayName.split(' ')[0]}` : 'Hello there!'}
                        </h3>
                        <p className="mt-1 text-sm font-semibold uppercase tracking-[0.22em] text-slate-400">
                          Enterprise Mode Active
                        </p>
                      </div>
                    </div>
                    <p className="max-w-xl text-sm leading-7 text-slate-600 md:text-base">
                      I can answer policy questions, guide employee-specific applicability when you ask for it, and help start HR workflows with clear citations and next steps.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:w-[24rem]">
                    <div className="rounded-2xl border border-white/80 bg-white/90 px-4 py-3 shadow-sm">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Profile</p>
                      <p className="mt-2 text-sm font-bold text-slate-800">{profile.grade}</p>
                      <p className="text-xs text-slate-500">{profile.location}</p>
                    </div>
                    <div className="rounded-2xl border border-white/80 bg-white/90 px-4 py-3 shadow-sm">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Language</p>
                      <p className="mt-2 text-sm font-bold text-slate-800 capitalize">{language}</p>
                      <p className="text-xs text-slate-500">Switch anytime</p>
                    </div>
                    <div className="rounded-2xl border border-white/80 bg-white/90 px-4 py-3 shadow-sm">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Mode</p>
                      <p className="mt-2 text-sm font-bold text-slate-800">{precisionMode ? 'Precision' : 'Standard'}</p>
                      <p className="text-xs text-slate-500">Ready for chat</p>
                    </div>
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.24em] text-indigo-400">Quick Starts</p>
                    <h4 className="mt-1 text-lg font-bold tracking-tight text-slate-900">Choose a guided HR path</h4>
                  </div>
                  <p className="hidden text-xs font-semibold text-slate-400 md:block">
                    Clean prompts for onboarding, travel, mobility, support, and more.
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {guidedJourneys.map((journey) => (
                    <button
                      key={journey.id}
                      onClick={() => handleJourneyPrompt(journey.prompt)}
                      className="rounded-[1.75rem] border border-slate-200 bg-white px-5 py-5 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-xl hover:shadow-indigo-100/50"
                    >
                      <span className="text-[10px] font-black uppercase tracking-[0.24em] text-indigo-400">
                        {journey.category}
                      </span>
                      <div className="mt-3 flex items-start justify-between gap-3">
                        <span className="pr-2 text-lg font-black leading-tight text-slate-900">
                          {journey.title}
                        </span>
                        <ChevronRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-300 transition-colors group-hover:text-indigo-500" />
                      </div>
                      <span className="mt-3 block text-sm leading-6 text-slate-500">
                        {journey.description}
                      </span>
                    </button>
                  ))}
                </div>
              </section>
            </div>
          ) : (
            messages.filter(m => m && m.role).map((message, i) => (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                key={message.id || i}
                className={`flex gap-5 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-11 h-11 flex-shrink-0 rounded-2xl flex items-center justify-center shadow-md ${
                  message.role === 'model' 
                    ? 'bg-indigo-600 text-white' 
                    : 'bg-white border border-slate-200 text-slate-400'
                }`}>
                  {message.role === 'model' ? <Bot className="w-6 h-6" /> : <UserIcon className="w-6 h-6" />}
                </div>
                <div className={`max-w-[80%] space-y-3 ${message.role === 'user' ? 'text-right' : ''}`}>
                  <div className={`px-6 py-4 rounded-[2rem] inline-block text-left shadow-sm border ${
                    message.role === 'model' 
                      ? 'bg-white border-slate-100 text-slate-700 font-medium' 
                      : 'bg-indigo-600 text-white border-indigo-500 rounded-tr-none shadow-indigo-100'
                  } ${message.role === 'model' ? 'rounded-tl-none' : ''}`}>
                    {message.role === 'user' && (message as any).imagePreview && (
                      <div className="mb-3 rounded-2xl overflow-hidden border border-white/20 shadow-lg">
                        <img src={(message as any).imagePreview} alt="Uploaded attachment" className="max-w-full h-auto max-h-48 object-contain" />
                      </div>
                    )}
                    <div className="text-[15px] leading-relaxed relative markdown-container">
                      {message.role === 'model' ? (
                        <div className="markdown-body">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <div className="whitespace-pre-wrap">
                          {message.content}
                        </div>
                      )}
                      
                      {message.role === 'model' && message.metadata?.confidenceScore !== undefined && (
                        <div className="mt-3 flex flex-wrap items-center gap-2">
                          {(() => {
                            const badge = getConfidenceBadge(message.metadata?.confidenceScore);
                            return (
                              <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${badge.tone}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`}></span>
                                {badge.label}
                                <span className="opacity-70">{Math.round((message.metadata?.confidenceScore ?? 0) * 100)}%</span>
                              </span>
                            );
                          })()}
                          {message.metadata?.source && (
                            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">
                              Source: {message.metadata.source}
                            </span>
                          )}
                          {message.metadata?.source && /Structured|Grounder|Clause/i.test(message.metadata.source) && (
                            <span className="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[9px] font-black uppercase tracking-widest">
                              Grounded Rule
                            </span>
                          )}
                          {message.metadata?.policyVersion && (
                            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">
                              Version: v{message.metadata.policyVersion}
                            </span>
                          )}
                          {message.metadata?.safetyMode && message.metadata.safetyMode !== 'standard' && (
                            <span className={`text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded-full ${
                              message.metadata.safetyMode === 'high_risk'
                                ? 'bg-rose-50 text-rose-700'
                                : 'bg-amber-50 text-amber-700'
                            }`}>
                              {message.metadata.safetyMode === 'high_risk' ? 'High Risk' : 'Sensitive'}
                            </span>
                          )}
                          {message.metadata?.action?.caseId && (
                            <span className="text-[9px] font-black uppercase tracking-widest text-indigo-600">
                              Workflow: {message.metadata.action.caseId}
                            </span>
                          )}
                        </div>
                      )}

                      {message.role === 'model' && message.metadata?.isHuggingFaceLocal && message.metadata?.huggingFaceMetrics && (
                        <div className="mt-4 p-4 rounded-2xl bg-emerald-50/50 border border-emerald-500/10 text-emerald-800 space-y-3">
                          <p className="text-[10px] font-black uppercase tracking-[0.15em] text-emerald-600 flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                            🛡️ Private Local Inference (Hugging Face VPC)
                          </p>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-xs">
                            <div className="flex justify-between py-1 border-b border-slate-100">
                              <span className="text-slate-400 font-medium">Model Weight:</span>
                              <span className="font-bold text-slate-700">Meta-Llama-3-8B-Instruct</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-100">
                              <span className="text-slate-400 font-medium">Server Host:</span>
                              <span className="font-bold text-slate-700">{message.metadata.huggingFaceMetrics.host}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-100">
                              <span className="text-slate-400 font-medium">Inference Speed:</span>
                              <span className="font-bold text-emerald-600 tabular-nums">{message.metadata.huggingFaceMetrics.tokensPerSecond} tokens/sec</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-100">
                              <span className="text-slate-400 font-medium">GPU Temperature:</span>
                              <span className="font-bold text-amber-600 tabular-nums">{message.metadata.huggingFaceMetrics.gpuTemperature}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-100">
                              <span className="text-slate-400 font-medium">VRAM Allocated:</span>
                              <span className="font-bold text-slate-700 tabular-nums">{message.metadata.huggingFaceMetrics.gpuVramUsed}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-100">
                              <span className="text-slate-400 font-medium">Privacy Status:</span>
                              <span className="font-extrabold text-emerald-600 uppercase tracking-tight text-[10px] bg-emerald-50 px-1.5 py-0.5 rounded">100% Stateless</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {message.role === 'model' && message.type === 'error' && (
                        <div className="mt-3">
                          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest bg-rose-50 text-rose-700">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                            Policy not found clearly
                          </span>
                        </div>
                      )}

                      {message.role === 'model' && message.type === 'action_trigger' && (
                        <div className="mt-4 p-4 bg-white/10 rounded-2xl border border-white/20 backdrop-blur-sm">
                          <p className="text-[10px] font-black uppercase tracking-widest mb-3 text-white/60 flex items-center gap-2">
                            <Bot className="w-3 h-3" /> System Action Triggered
                          </p>
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-sm">Target: {message.metadata?.action?.type?.replace(/_/g, ' ')}</span>
                            <button className="px-4 py-2 bg-white text-indigo-600 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-slate-900 hover:text-white transition-all shadow-lg active:scale-95">
                              Run Workflow
                            </button>
                          </div>
                        </div>
                      )}

                      {message.metadata?.policyUrl && (
                        <div className="mt-4 flex flex-wrap gap-2">
                           <button 
                            onClick={() => {
                              const linkedPolicy = ARVIND_POLICIES.find(p => p.id === message.metadata.policyId);
                              const linkedUploadedFile = uploadedFiles.find(file =>
                                (message.metadata.policyId && file.policyId === message.metadata.policyId) ||
                                (message.metadata.policyName && file.name.toLowerCase() === message.metadata.policyName.toLowerCase()) ||
                                (message.metadata.policyUrl && file.fileUrl === message.metadata.policyUrl)
                              );
                              const highlightTerms = message.metadata.highlightTerms || [];
                              const pageNum = message.metadata.pageNumber;
                              let baseFileUrl = message.metadata.policyUrl || linkedPolicy?.fileUrl || "";
                              let finalUrl = buildPolicyDocumentUrl(baseFileUrl, pageNum, highlightTerms);

                              if (linkedPolicy) {
                                setSelectedPolicy({
                                  ...linkedPolicy,
                                  fileUrl: finalUrl,
                                  highlightTerms: highlightTerms
                                });
                                setIsPolicyViewerOpen(true);
                              } else if (linkedUploadedFile) {
                                setSelectedPolicy({
                                  name: linkedUploadedFile.name,
                                  sourceDocumentName: linkedUploadedFile.sourceDocumentName,
                                  content: linkedUploadedFile.content,
                                  fileUrl: finalUrl || linkedUploadedFile.fileUrl,
                                  id: linkedUploadedFile.policyId || linkedUploadedFile.id,
                                  highlightTerms: highlightTerms,
                                });
                                setIsPolicyViewerOpen(true);
                              } else if (baseFileUrl) {
                                window.open(finalUrl, '_blank');
                              }
                            }}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-[12px] font-bold hover:bg-slate-900 transition-all shadow-lg shadow-indigo-100 group"
                          >
                            <BookOpen className="w-4 h-4" />
                            Open Original Policy Document
                            <div className="w-px h-3 bg-white/20 mx-1" />
                            <span className="opacity-70 group-hover:opacity-100">{message.metadata.policyName || 'View PDF'}</span>
                            <ExternalLink className="w-3 h-3 ml-0.5 opacity-50" />
                          </button>
                        </div>
                      )}
                    </div>
                    {message.metadata && (
                      <div className="mt-6 pt-5 border-t border-slate-100 space-y-4">
                        {message.metadata.localizedSummary && (
                          <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
                            <p className="text-[10px] font-black uppercase tracking-widest text-emerald-600 mb-2">
                              Localized Summary
                            </p>
                            <p className="text-[13px] text-emerald-900 leading-relaxed">{message.metadata.localizedSummary}</p>
                          </div>
                        )}

                        {(message.metadata.scenarioTitle || message.metadata.scenarioComparison?.length > 0) && (
                          <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 p-5">
                            <p className="text-[10px] font-black uppercase tracking-widest text-indigo-500 mb-3">
                              {message.metadata.scenarioTitle || 'Scenario Simulation'}
                            </p>
                            <div className="space-y-2">
                              {(message.metadata.scenarioComparison || []).map((row: any, idx: number) => (
                                <div key={idx} className="grid grid-cols-[120px,1fr,1fr] gap-3 text-[12px]">
                                  <span className="font-bold text-slate-700">{row.label}</span>
                                  <span className="text-slate-500">{row.current}</span>
                                  <span className="text-indigo-700 font-semibold">{row.hypothetical}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {message.metadata.actionChecklist?.length > 0 && (
                          <div className="rounded-2xl border border-slate-200/60 bg-slate-50 p-5">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-[0.1em] mb-3">
                              <Check className="w-3.5 h-3.5" /> Action Checklist
                            </div>
                            <ul className="space-y-2">
                              {message.metadata.actionChecklist.map((step: string, idx: number) => (
                                <li key={idx} className="flex gap-2.5 text-[13px] text-slate-700 leading-snug">
                                  <div className="w-5 h-5 rounded-full bg-white border border-slate-200 text-[10px] font-black text-slate-500 flex items-center justify-center shrink-0">
                                    {idx + 1}
                                  </div>
                                  {step}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div className="flex items-center gap-2 text-[10px] font-bold text-indigo-500 uppercase tracking-[0.1em] bg-indigo-50 px-3 py-1.5 rounded-full w-fit">
                          <FileText className="w-3.5 h-3.5" /> Policy Reference
                        </div>
                        
                        {(() => {
                          const citations = message.metadata.citations || [];
                          
                          if (citations && citations.length > 0) {
                            return (
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full">
                                {citations.map((cite: any, idx: number) => {
                                  const citePolicyId = cite.policyId || "";
                                  const citePolicyName = cite.policyName || cite.policy || "";
                                  const citePageNum = cite.pageNumber || cite.page || 1;
                                  
                                  const linkedPolicy = ARVIND_POLICIES.find(p => 
                                    (citePolicyId && p.id === citePolicyId) ||
                                    (citePolicyName && p.name.toLowerCase() === citePolicyName.toLowerCase())
                                  );
                                  
                                  const linkedUploadedFile = uploadedFiles.find(f => 
                                    (citePolicyId && f.policyId === citePolicyId) ||
                                    (citePolicyName && f.name.toLowerCase() === citePolicyName.toLowerCase()) ||
                                    (cite.policyUrl && f.fileUrl === cite.policyUrl)
                                  );
                                  
                                  const isArvindPolicy = !!linkedPolicy;
                                  const isUploadedFile = !!linkedUploadedFile;
                                  const fileUrl = cite.policyUrl || linkedPolicy?.fileUrl || linkedUploadedFile?.fileUrl || '#';
                                  const hasLink = fileUrl !== '#';
                                  
                                  const cardContent = (
                                    <div className="flex flex-col h-full justify-between">
                                      <div className="flex items-start justify-between mb-3 w-full">
                                        <div className="flex-1 min-w-0 pr-2">
                                          <h4 className={`text-[14px] font-bold text-slate-800 ${hasLink ? 'group-hover:text-indigo-600' : ''} transition-colors line-clamp-2`}>
                                            {citePolicyName || linkedPolicy?.name || linkedUploadedFile?.name || 'Standard Operating Procedure'}
                                          </h4>
                                          <p className="text-[11px] text-slate-400 mt-1">
                                            Source: {cite.source || getPolicySourceLabel(linkedPolicy, linkedUploadedFile, message.metadata.source)}
                                          </p>
                                        </div>
                                        {hasLink && (
                                          <div className="p-1.5 bg-slate-50 rounded-lg group-hover:bg-indigo-50 transition-colors shrink-0">
                                            <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-500" />
                                          </div>
                                        )}
                                      </div>
                                      
                                      <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] font-semibold text-slate-600">
                                        <span>Clause / Page</span>
                                        <span className="text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full font-bold">
                                          {cite.clauseReference || `Page ${citePageNum}`}
                                        </span>
                                      </div>
                                    </div>
                                  );

                                  if (isArvindPolicy) {
                                    const highlightTerms = message.metadata.highlightTerms || [];
                                    const finalUrl = buildPolicyDocumentUrl(fileUrl, citePageNum, highlightTerms);
                                    
                                    return (
                                      <button 
                                        key={idx}
                                        onClick={() => {
                                          setSelectedPolicy({
                                            ...linkedPolicy,
                                            fileUrl: finalUrl,
                                            highlightTerms: highlightTerms
                                          });
                                          setIsPolicyViewerOpen(true);
                                        }}
                                        className="block bg-white rounded-2xl p-4 border border-slate-200/60 shadow-sm hover:shadow-md transition-all cursor-pointer group text-left w-full hover:-translate-y-0.5"
                                      >
                                        {cardContent}
                                      </button>
                                    );
                                  } else if (isUploadedFile) {
                                    const highlightTerms = message.metadata.highlightTerms || [];
                                    const finalUrl = buildPolicyDocumentUrl(fileUrl, citePageNum, highlightTerms);

                                    return (
                                      <button 
                                        key={idx}
                                        onClick={() => {
                                          setSelectedPolicy({
                                            name: linkedUploadedFile.name,
                                            sourceDocumentName: linkedUploadedFile.sourceDocumentName,
                                            content: linkedUploadedFile.content,
                                            fileUrl: finalUrl || linkedUploadedFile.fileUrl,
                                            id: linkedUploadedFile.policyId || linkedUploadedFile.id,
                                            highlightTerms: highlightTerms
                                          });
                                          setIsPolicyViewerOpen(true);
                                        }}
                                        className="block bg-white rounded-2xl p-4 border border-slate-200/60 shadow-sm hover:shadow-md transition-all cursor-pointer group text-left w-full hover:-translate-y-0.5"
                                      >
                                        {cardContent}
                                      </button>
                                    );
                                  } else if (hasLink) {
                                    const highlightTerms = message.metadata.highlightTerms || [];
                                    const finalUrl = buildPolicyDocumentUrl(fileUrl, citePageNum, highlightTerms);

                                    return (
                                      <button
                                        key={idx}
                                        onClick={() => window.open(finalUrl, '_blank')}
                                        className="block bg-white rounded-2xl p-4 border border-slate-200/60 shadow-sm hover:shadow-md transition-all cursor-pointer group text-left w-full hover:-translate-y-0.5"
                                      >
                                        {cardContent}
                                      </button>
                                    );
                                  } else {
                                    return (
                                      <div key={idx} className="block bg-white rounded-2xl p-4 border border-slate-200/60 shadow-sm cursor-default w-full">
                                        {cardContent}
                                      </div>
                                    );
                                  }
                                })}
                              </div>
                            );
                          }

                          const linkedPolicy = ARVIND_POLICIES.find(p => 
                            (message.metadata.policyId && p.id === message.metadata.policyId) ||
                            (message.metadata.policyName && p.name.toLowerCase() === message.metadata.policyName.toLowerCase())
                          );
                          
                          const linkedUploadedFile = uploadedFiles.find(f => 
                            (message.metadata.policyId && f.policyId === message.metadata.policyId) ||
                            (message.metadata.policyName && f.name.toLowerCase() === message.metadata.policyName.toLowerCase()) ||
                            (message.metadata.policyUrl && f.fileUrl === message.metadata.policyUrl)
                          );

                          const isArvindPolicy = !!linkedPolicy;
                          const isUploadedFile = !!linkedUploadedFile;
                          const fileUrl = message.metadata.policyUrl || linkedPolicy?.fileUrl || linkedUploadedFile?.fileUrl || '#';
                          const hasLink = fileUrl !== '#';

                          const cardContent = (
                            <>
                              <div className="flex items-start justify-between mb-3">
                                <div>
                                   <h4 className={`text-[15px] font-bold text-slate-800 ${hasLink ? 'group-hover:text-indigo-600' : ''} transition-colors`}>
                                    {message.metadata.policyName || linkedPolicy?.name || linkedUploadedFile?.name || 'Standard Operating Procedure'}
                                  </h4>
                                  <p className="text-[11px] text-slate-400 mt-0.5">
                                    Source: {getPolicySourceLabel(linkedPolicy, linkedUploadedFile, message.metadata.source)}
                                  </p>
                                </div>
                                {hasLink && (
                                  <div className="p-2 bg-slate-50 rounded-xl group-hover:bg-indigo-50 transition-colors">
                                    <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-indigo-500" />
                                  </div>
                                )}
                              </div>
                              
                              {message.metadata.keyPoints && (
                                <ul className="space-y-2 mt-4">
                                  {message.metadata.keyPoints.map((point: string, i: number) => (
                                    <li key={i} className="flex gap-2.5 text-[13px] text-slate-600 leading-snug">
                                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-300 mt-1.5 shrink-0" />
                                      {point}
                                    </li>
                                  ))}
                                </ul>
                              )}

                              {(message.metadata.policyVersion || message.metadata.effectiveDate || message.metadata.lastUpdatedAt || message.metadata.clauseReference || message.metadata.matchedCriteria?.length > 0) && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 pt-4 border-t border-slate-100">
                                  {message.metadata.policyVersion && (
                                    <div>
                                      <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Version</p>
                                      <p className="text-[13px] font-semibold text-slate-700 mt-1">v{message.metadata.policyVersion}</p>
                                    </div>
                                  )}
                                  {message.metadata.effectiveDate && (
                                    <div>
                                      <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Effective Date</p>
                                      <p className="text-[13px] font-semibold text-slate-700 mt-1">{formatMetadataDate(message.metadata.effectiveDate)}</p>
                                    </div>
                                  )}
                                  {message.metadata.lastUpdatedAt && (
                                    <div>
                                      <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Last Updated</p>
                                      <p className="text-[13px] font-semibold text-slate-700 mt-1">{formatMetadataDate(message.metadata.lastUpdatedAt)}</p>
                                    </div>
                                  )}
                                  {message.metadata.clauseReference && (
                                    <div>
                                      <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Clause / Page</p>
                                      <p className="text-[13px] font-semibold text-slate-700 mt-1">{message.metadata.clauseReference}</p>
                                    </div>
                                  )}
                                </div>
                              )}

                              {message.metadata.matchedCriteria?.length > 0 && (
                                <div className="flex flex-wrap gap-2 mt-4">
                                  {message.metadata.matchedCriteria.map((criterion: string, idx: number) => (
                                    <span key={idx} className="px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-[10px] font-black uppercase tracking-widest">
                                      {criterion}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </>
                          );

                          if (isArvindPolicy) {
                            const highlightTerms = message.metadata.highlightTerms || [];
                            const pageNum = message.metadata.pageNumber;
                            const finalUrl = buildPolicyDocumentUrl(fileUrl, pageNum, highlightTerms);

                            return (
                              <button 
                                onClick={() => {
                                  setSelectedPolicy({
                                    ...linkedPolicy,
                                    fileUrl: finalUrl,
                                    highlightTerms: highlightTerms
                                  });
                                  setIsPolicyViewerOpen(true);
                                }}
                                className="w-full block bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm hover:shadow-md transition-shadow cursor-pointer group text-left"
                              >
                                {cardContent}
                              </button>
                            );
                          } else if (isUploadedFile) {
                            const highlightTerms = message.metadata.highlightTerms || [];
                            const pageNum = message.metadata.pageNumber;
                            const finalUrl = buildPolicyDocumentUrl(fileUrl, pageNum, highlightTerms);

                            return (
                              <button 
                                onClick={() => {
                                  setSelectedPolicy({
                                    name: linkedUploadedFile.name,
                                    sourceDocumentName: linkedUploadedFile.sourceDocumentName,
                                    content: linkedUploadedFile.content,
                                    fileUrl: finalUrl || linkedUploadedFile.fileUrl,
                                    id: linkedUploadedFile.policyId || linkedUploadedFile.id,
                                    highlightTerms: highlightTerms
                                  });
                                  setIsPolicyViewerOpen(true);
                                }}
                                className="w-full block bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm hover:shadow-md transition-shadow cursor-pointer group text-left"
                              >
                                {cardContent}
                              </button>
                            );
                          } else if (hasLink) {
                            const highlightTerms = message.metadata.highlightTerms || [];
                            const pageNum = message.metadata.pageNumber;
                            const finalUrl = buildPolicyDocumentUrl(fileUrl, pageNum, highlightTerms);

                            return (
                              <button
                                onClick={() => window.open(finalUrl, '_blank')}
                                className="w-full block bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm hover:shadow-md transition-shadow cursor-pointer group text-left"
                              >
                                {cardContent}
                              </button>
                            );
                          } else {
                            return (
                              <div className="block bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm transition-shadow cursor-default">
                                {cardContent}
                              </div>
                            );
                          }
                        })()}

                        {message.metadata.policyChanges?.length > 0 && (
                          <div className="rounded-2xl border border-sky-100 bg-sky-50/70 p-5">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-sky-700 uppercase tracking-[0.1em] mb-3">
                              <HistoryIcon className="w-3.5 h-3.5" /> Policy Change Summary
                            </div>
                            <ul className="space-y-2">
                              {message.metadata.policyChanges.map((change: string, idx: number) => (
                                <li key={idx} className="flex gap-2.5 text-[13px] text-slate-700 leading-snug">
                                  <div className="w-1.5 h-1.5 rounded-full bg-sky-400 mt-1.5 shrink-0" />
                                  {change}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                      </div>
                    )}
                  </div>
                  
                    <AnimatePresence>
                      {message.role === 'model' && message.metadata?.clarificationOptions && message.metadata.clarificationOptions.length > 0 && i === messages.length - 1 && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="flex flex-wrap gap-2 mt-2 mb-4"
                        >
                          {message.metadata.clarificationOptions.map((opt: string, idx: number) => (
                            <button
                              key={idx}
                              onClick={() => {
                                setInput(opt);
                                setTimeout(() => {
                                  const sendBtn = document.getElementById('chat-send-button');
                                  sendBtn?.click();
                                }, 100);
                              }}
                              className="text-[10px] font-black uppercase tracking-widest px-4 py-2 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-xl hover:bg-indigo-600 hover:text-white transition-all shadow-sm active:scale-95"
                            >
                              {opt}
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>

                    <AnimatePresence>
                      {message.role === 'model' && message.suggestedQuestions && message.suggestedQuestions.length > 0 && i === messages.length - 1 && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="flex flex-wrap gap-2 mt-4"
                        >
                          {message.suggestedQuestions.map((q, idx) => (
                            <button
                              key={idx}
                              onClick={() => {
                                setInput(q);
                                // Trigger send automatically with a small delay for focus
                                setTimeout(() => {
                                  const sendBtn = document.getElementById('chat-send-button');
                                  sendBtn?.click();
                                }, 100);
                              }}
                              className="text-[11px] font-bold px-4 py-2 bg-white border border-indigo-100 text-indigo-600 rounded-xl hover:bg-indigo-600 hover:text-white transition-all shadow-sm active:scale-95"
                            >
                              {q}
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                    
                    {message.role === 'model' && (
                      <div className="space-y-3 px-2 mt-2">
                        <div className="flex items-center gap-4">
                         <motion.button 
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          disabled={!!feedbackSent[message.id]}
                          onClick={() => handleFeedback(message.id, 5)}
                          className={`text-[10px] font-bold transition-all flex items-center gap-1.5 uppercase tracking-widest px-3 py-1.5 rounded-full border ${
                            feedbackSent[message.id] === 5 
                              ? "bg-indigo-600 text-white border-indigo-600 shadow-md" 
                              : "text-slate-400 border-slate-100 hover:border-indigo-200 hover:text-indigo-600 hover:bg-indigo-50"
                          }`}
                        >
                          <ThumbsUp className={`w-3.5 h-3.5 ${feedbackSent[message.id] === 5 ? "fill-white" : ""}`} /> 
                          {feedbackSent[message.id] === 5 ? "Helpful" : "Helpful"}
                        </motion.button>
                        <motion.button 
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          disabled={!!feedbackSent[message.id]}
                          onClick={() => handleFeedback(message.id, 1)}
                          className={`text-[10px] font-bold transition-all flex items-center gap-1.5 uppercase tracking-widest px-3 py-1.5 rounded-full border ${
                            feedbackSent[message.id] === 1 
                              ? "bg-red-500 text-white border-red-500 shadow-md" 
                              : "text-slate-400 border-slate-100 hover:border-red-200 hover:text-red-500 hover:bg-red-50"
                          }`}
                        >
                          <ThumbsDown className={`w-3.5 h-3.5 ${feedbackSent[message.id] === 1 ? "fill-white" : ""}`} /> 
                          {feedbackSent[message.id] === 1 ? "Not Useful" : "Not Useful"}
                        </motion.button>
                        <motion.button 
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => speakMessage(message.id, message.content)}
                          className={`text-[10px] font-bold transition-all flex items-center gap-1.5 uppercase tracking-widest px-3 py-1.5 rounded-full border ${
                            activeSpeakingId === message.id 
                              ? "bg-emerald-600 text-white border-emerald-600 shadow-md" 
                              : "text-slate-400 border-slate-100 hover:border-emerald-200 hover:text-emerald-600 hover:bg-emerald-50"
                          }`}
                          title={activeSpeakingId === message.id ? "Stop reading" : "Read answer aloud"}
                        >
                          {activeSpeakingId === message.id ? (
                            <>
                              <VolumeX className="w-3.5 h-3.5" />
                              Stop Voice
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-3.5 h-3.5" />
                              Listen
                            </>
                          )}
                        </motion.button>

                        <AnimatePresence>
                          {feedbackSent[message.id] && (
                            <motion.span
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              className="text-[10px] font-bold text-emerald-600 italic"
                            >
                              Thanks for your feedback!
                            </motion.span>
                          )}
                        </AnimatePresence>
                        </div>

                        {shouldOfferEscalation(message) && (
                          <div className="flex flex-wrap gap-2">
                            <button
                              onClick={() => handleEscalationAction(message.metadata?.policyId === 'posh-policy' ? 'posh' : message.metadata?.policyId === 'whistleblower' ? 'whistleblower' : 'grievance', message)}
                              className="px-3 py-2 bg-white border border-amber-200 text-amber-700 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-amber-50 transition-all"
                            >
                              {message.metadata?.policyId === 'posh-policy' ? 'Create POSH Case' : 'Escalate to BUHR'}
                            </button>
                            <button
                              onClick={emailTranscriptToHR}
                              className="px-3 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all"
                            >
                              Email Chat Transcript to HR
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                </div>
              </motion.div>
            ))
          )}
          {isTyping && (
            <div className="flex gap-5">
              <div className="w-11 h-11 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-100">
                <Bot className="w-6 h-6" />
              </div>
              <div className="bg-white border border-slate-100 px-6 py-5 rounded-[2rem] rounded-tl-none shadow-sm flex gap-2 items-center ring-4 ring-indigo-50/50">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          )}
        </div>

        <div className="p-8 bg-white border-t border-slate-100 sticky bottom-0 z-10">
          <AnimatePresence>
            {imageAttachment && (
              <motion.div 
                initial={{ opacity: 0, y: 10, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="max-w-4xl mx-auto mb-4 p-3 bg-white border-2 border-indigo-100 rounded-2xl shadow-xl flex items-center gap-4 group"
              >
                <div className="relative w-16 h-16 rounded-xl overflow-hidden bg-slate-100 border border-slate-200">
                  <img src={imageAttachment.previewUrl} alt="Preview" className="w-full h-full object-cover" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-bold text-slate-800">Ready to Analyze</p>
                  <p className="text-[10px] text-slate-400 font-bold uppercase">Multi-modal AI Input Detected</p>
                </div>
                <button 
                  onClick={() => setImageAttachment(null)}
                  className="p-2 bg-slate-50 text-slate-400 hover:text-red-500 rounded-xl transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {isUploading && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="max-w-4xl mx-auto mb-4 bg-indigo-50 border border-indigo-100 rounded-2xl p-4 flex flex-col gap-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white">
                      <Paperclip className="w-4 h-4 animate-pulse" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-indigo-900 uppercase tracking-widest">Processing Knowledge Assets</p>
                      <p className="text-[10px] text-indigo-400 font-bold uppercase tracking-tight">Integrating Secure Offline Documents</p>
                    </div>
                  </div>
                  <p className="text-sm font-black text-indigo-600 tabular-nums">{uploadProgress}%</p>
                </div>
                <div className="w-full bg-indigo-100/50 h-2 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${uploadProgress}%` }}
                    className="h-full bg-indigo-600"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative group">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              className="hidden"
              accept=".txt,.md,.pdf,.doc,.docx"
              multiple
            />
            <input
              type="file"
              ref={imageInputRef}
              onChange={handleImageCapture}
              className="hidden"
              accept="image/*"
            />
            <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-1.5 px-1 bg-slate-50/50 rounded-full">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading || isTyping}
                className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all relative"
                title="Attach Document"
              >
                <Paperclip className={`w-5 h-5 ${isUploading ? 'animate-spin' : ''}`} />
                {showUploadSuccess && (
                  <motion.div 
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute -top-1 -right-1 bg-emerald-500 text-white rounded-full p-0.5"
                  >
                    <Check className="w-2.5 h-2.5" />
                  </motion.div>
                )}
              </button>
              <button
                type="button"
                onClick={() => imageInputRef.current?.click()}
                disabled={isTyping}
                className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all"
                title="Capture / Attach Image"
              >
                <Camera className="w-5 h-5" />
              </button>
              <div className="w-px h-6 bg-slate-200 mx-0.5"></div>
              <button
                type="button"
                onClick={toggleListening}
                disabled={isTyping}
                className={`p-2 rounded-full transition-all ${
                  isListening ? 'bg-rose-100 text-rose-600 animate-pulse' : 'text-slate-400 hover:text-indigo-600 hover:bg-indigo-50'
                }`}
                title={isListening ? "Listening..." : "Voice Input"}
              >
                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>
            </div>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={imageAttachment ? "Add notes about this image..." : "Ask anything about Arvind policies or records..."}
              className="w-full pl-40 pr-32 py-5 bg-slate-50 border border-slate-200 rounded-[2.5rem] focus:ring-8 focus:ring-indigo-50 focus:border-indigo-300 transition-all text-slate-700 font-bold placeholder:text-slate-400 shadow-inner outline-none"
            />
            {isTyping ? (
              <button
                type="button"
                onClick={stopGeneration}
                className="absolute right-3 top-3 bottom-3 px-6 bg-slate-900 text-white rounded-[2rem] font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-red-600 transition-all shadow-xl active:scale-95"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                Stop
              </button>
            ) : (
              <button
                id="chat-send-button"
                type="submit"
                disabled={(!input.trim() && !imageAttachment) || isTyping}
                className="absolute right-3 top-3 bottom-3 px-6 bg-indigo-600 text-white rounded-[2rem] font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-slate-900 disabled:bg-slate-200 disabled:text-slate-400 transition-all shadow-xl shadow-indigo-100 active:scale-95"
              >
                <Send className="w-4 h-4 ml-1" />
                Secure Ask
              </button>
            )}
            <button
              type="button"
              onClick={exportChat}
              disabled={messages.length === 0}
              className="absolute -right-16 top-1/2 -translate-y-1/2 p-4 bg-white border border-slate-200 text-slate-400 hover:text-indigo-600 rounded-2xl shadow-sm transition-all hover:shadow-md hidden xl:block"
              title="Export Conversation"
            >
              <Download className="w-5 h-5" />
            </button>
          </form>
          <div className="max-w-4xl mx-auto mt-5 flex items-center justify-center gap-6">
             <div className="flex items-center gap-2 opacity-50">
               <ShieldCheck className="w-3 h-3" />
               <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">End-to-End Encrypted Access</p>
             </div>
          </div>
        </div>
      </main>
      {/* Policy Viewer Modal */}
      <AnimatePresence>
        {isPolicyViewerOpen && selectedPolicy && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 sm:p-6 lg:p-8">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsPolicyViewerOpen(false)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 rounded-xl">
                    <FileText className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-800">{selectedPolicy.name}</h3>
                    <p className="text-xs text-slate-400">Official Policy Document • Arvind Limited</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsPolicyViewerOpen(false)}
                  className="p-2 hover:bg-slate-200/50 rounded-full transition-colors text-slate-400 hover:text-slate-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Modal Content (Document View) */}
              <div className="flex-1 overflow-hidden p-4 sm:p-8 bg-slate-100/30 flex flex-col">
                {!selectedPolicy.fileUrl ? (
                  <div className="max-w-2xl mx-auto w-full bg-white shadow-sm border border-slate-200 p-8 sm:p-16 rounded-sm overflow-y-auto flex-1">
                    {/* Internal Doc Header */}
                    <div className="border-b-2 border-slate-800 pb-8 mb-12 flex justify-between items-end">
                      <div>
                        <h1 className="text-3xl font-serif font-black text-slate-900 uppercase tracking-tighter">ARVIND</h1>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.3em] mt-1">Limited • Policy Framework</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Document Ref</p>
                        <p className="text-xs font-mono text-slate-600 uppercase font-bold">{selectedPolicy.id || 'GEN-POL-001'}</p>
                      </div>
                    </div>

                    <div className="space-y-8">
                      <h2 className="text-2xl font-bold text-slate-800 border-b border-slate-100 pb-4">
                        {selectedPolicy.name}
                      </h2>
                    
                    <div className="prose prose-slate max-w-none">
                      <div className="whitespace-pre-wrap text-slate-700 leading-relaxed font-sans text-[15px]">
                        <HighlightedText 
                          text={selectedPolicy.content || ""} 
                          highlights={selectedPolicy.highlightTerms || []} 
                        />
                      </div>
                    </div>
                    </div>
                  </div>
                ) : canPreviewPolicyInFrame(selectedPolicy.fileUrl) ? (
                  <div className="w-full h-full flex flex-col bg-white rounded-sm shadow-lg overflow-hidden border border-slate-200">
                    <iframe 
                      src={selectedPolicy.fileUrl} 
                      className="w-full h-full border-0"
                      title={selectedPolicy.name}
                    />
                  </div>
                ) : (
                  <div className="max-w-2xl mx-auto w-full bg-white shadow-sm border border-slate-200 p-8 sm:p-12 rounded-3xl flex-1 flex flex-col justify-center text-center">
                    <div className="mx-auto mb-5 p-4 bg-indigo-50 rounded-2xl border border-indigo-100">
                      <FileBox className="w-8 h-8 text-indigo-600" />
                    </div>
                    <h4 className="text-xl font-bold text-slate-800 mb-3">Preview not available in-app</h4>
                    <p className="text-sm text-slate-500 leading-relaxed">
                      This source document is attached as the original policy file and can be opened or downloaded directly.
                    </p>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 border-t border-slate-100 bg-white flex flex-col sm:flex-row justify-between gap-4 items-center">
                <div className="flex gap-2">
                  {selectedPolicy.highlightTerms?.length > 0 && (
                    <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-100 rounded-full">
                      <Search className="w-3 h-3 text-amber-600" />
                      <span className="text-[10px] font-bold text-amber-700 uppercase">Highlights Active</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-100 rounded-full">
                    <Check className="w-3 h-3 text-emerald-600" />
                    <span className="text-[10px] font-bold text-emerald-700 uppercase">Verified Doc</span>
                  </div>
                </div>

                <div className="flex gap-3">
                  {selectedPolicy.fileUrl && (
                    <a
                      href={selectedPolicy.fileUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2.5 text-sm font-bold text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors flex items-center gap-2"
                    >
                      <ExternalLink className="w-4 h-4" /> Open Original
                    </a>
                  )}
                  <button
                    onClick={() => downloadPolicy(selectedPolicy)}
                    className="px-6 py-2.5 text-sm font-bold bg-slate-900 text-white rounded-xl shadow-lg shadow-slate-200 hover:bg-slate-800 transition-all flex items-center gap-2"
                  >
                    {selectedPolicy.fileUrl ? 'Download Original File' : 'Download Extract'}
                  </button>
                  <button
                    onClick={() => setIsPolicyViewerOpen(false)}
                    className="px-6 py-2.5 text-sm font-bold bg-indigo-600 text-white rounded-xl shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all flex items-center gap-2"
                  >
                    Done
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

function buildReimbursementChart(total: number) {
  const base = Math.max(32000, Math.round(total / 5));
  return [
    { name: 'Jan', value: Math.round(base * 0.82), color: '#6366f1' },
    { name: 'Feb', value: Math.round(base * 0.9), color: '#8b5cf6' },
    { name: 'Mar', value: Math.round(base * 1.06), color: '#ec4899' },
    { name: 'Apr', value: Math.round(base * 0.97), color: '#10b981' },
    { name: 'May', value: Math.round(base * 1.15), color: '#f59e0b' },
  ];
}

function ManagerDashboardView({
  profile,
  teamMembers,
  analyticsSummary,
  onJourneySelect,
}: {
  profile: UserProfile;
  teamMembers: EmployeeRecord[];
  analyticsSummary: AnalyticsSummary;
  onJourneySelect: (prompt: string) => void;
}) {
  const pendingApprovals = teamMembers.filter(
    (member) => member.attendanceStatus === 'On Leave' || member.activeCases > 0
  ).length;
  const avgAttendance = teamMembers.length > 0
    ? Math.round(teamMembers.reduce((sum, member) => sum + member.attendanceRate, 0) / teamMembers.length)
    : 0;
  const openCases = teamMembers.reduce((sum, member) => sum + member.activeCases, 0);
  const hubTitle = profile.role === 'hrbp' ? 'HRBP Command Center' : profile.role === 'admin' ? 'Operations Command Center' : 'Manager Command Center';
  const insights = getManagerInsights(profile, teamMembers, analyticsSummary);
  const managerServices = listServiceCatalogItems().filter((item) =>
    ['Leave', 'Payroll', 'Grievance', 'POSH', 'Recruiting'].includes(item.category)
  );
  const talentWorkflows = getTalentWorkflows().slice(0, 3);
  const quickActions = profile.role === 'manager'
    ? [
        'Show team leave insights and pending approvals.',
        'Show escalation hotspots and unresolved employee questions.',
        'What can managers approve under the travel and conveyance policies?',
      ]
    : [
        'Show escalation hotspots and unresolved employee questions.',
        'Show policy changes that need benchmark review.',
        'Show the most used policies by employees this week.',
      ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto w-full space-y-8"
    >
      <div className="bg-white rounded-[2.5rem] border border-slate-100 p-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-8">
          <div>
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-2 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-600" /> {hubTitle}
            </h3>
            <p className="text-sm text-slate-500 max-w-2xl">
              This role-aware view surfaces team approvals, employee risk signals, and the weekly issues that should be reviewed before they become escalations.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {quickActions.map((prompt) => (
              <button
                key={prompt}
                onClick={() => onJourneySelect(prompt)}
                className="px-4 py-2 rounded-xl bg-indigo-50 text-indigo-700 text-[11px] font-bold hover:bg-indigo-100 transition-colors"
              >
                {prompt.length > 42 ? `${prompt.slice(0, 42)}...` : prompt}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="p-6 bg-slate-50 rounded-3xl border border-slate-100">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Pending People Actions</p>
            <p className="text-3xl font-black text-indigo-600">{String(pendingApprovals).padStart(2, '0')}</p>
          </div>
          <div className="p-6 bg-slate-50 rounded-3xl border border-slate-100">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Average Attendance</p>
            <p className="text-3xl font-black text-emerald-600">{avgAttendance}%</p>
          </div>
          <div className="p-6 bg-slate-50 rounded-3xl border border-slate-100">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Escalation Watchlist</p>
            <p className="text-3xl font-black text-amber-600">{openCases + analyticsSummary.lowConfidenceCount}</p>
          </div>
        </div>

        {teamMembers.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-50">
                  <th className="pb-4 text-[10px] font-black text-slate-400 uppercase tracking-tighter">Team Member</th>
                  <th className="pb-4 text-[10px] font-black text-slate-400 uppercase tracking-tighter">Status</th>
                  <th className="pb-4 text-[10px] font-black text-slate-400 uppercase tracking-tighter">Leave Bal.</th>
                  <th className="pb-4 text-[10px] font-black text-slate-400 uppercase tracking-tighter">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {teamMembers.map((member) => {
                  const pendingCount = Number(member.attendanceStatus === 'On Leave') + member.activeCases;
                  return (
                    <tr key={member.profile.uid} className="group hover:bg-slate-50 transition-colors">
                      <td className="py-4">
                        <p className="text-sm font-bold text-slate-800">{member.profile.displayName}</p>
                        <p className="text-[10px] text-slate-400">{member.profile.grade} • {member.profile.location} • {member.profile.businessUnit}</p>
                      </td>
                      <td className="py-4">
                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${
                          member.attendanceStatus === 'Present' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
                        }`}>
                          {member.attendanceStatus}
                        </span>
                      </td>
                      <td className="py-4 text-xs font-bold text-slate-600">
                        {member.leaveBalances.casual} CL / {member.leaveBalances.earned} EL / {member.leaveBalances.sick} SL
                      </td>
                      <td className="py-4">
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => onJourneySelect(`Review leave and attendance status for ${member.profile.displayName}.`)}
                            className="px-3 py-1 bg-white border border-slate-200 rounded-lg text-[9px] font-black uppercase tracking-tighter text-slate-400 hover:text-indigo-600 hover:border-indigo-100 transition-all"
                          >
                            Review
                          </button>
                          {pendingCount > 0 && (
                            <button
                              onClick={() => onJourneySelect(`Show the pending approvals and support needs for ${member.profile.displayName}.`)}
                              className="px-3 py-1 bg-indigo-600 text-white rounded-lg text-[9px] font-black uppercase tracking-tighter"
                            >
                              Act on {pendingCount}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 rounded-3xl bg-slate-50 border border-slate-100 text-sm text-slate-500">
            No direct reports are mapped for this persona yet. Use the quick actions above to review escalations, governance, and policy quality.
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {insights.map((insight) => (
          <button
            key={insight.id}
            onClick={() => onJourneySelect(insight.prompt)}
            className="text-left bg-white rounded-[2rem] border border-slate-100 p-6 shadow-sm hover:shadow-md transition-all"
          >
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{insight.title}</p>
            <p className={`text-3xl font-black ${
              insight.tone === 'good'
                ? 'text-emerald-600'
                : insight.tone === 'watch'
                  ? 'text-amber-600'
                  : insight.tone === 'risk'
                    ? 'text-rose-600'
                    : 'text-indigo-600'
            }`}>
              {insight.value}
            </p>
            <p className="text-xs text-slate-500 mt-3 leading-relaxed">{insight.detail}</p>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {[
          {
            title: 'Team Leave Insights',
            description: 'Spot leave concentration, missing attendance, and who needs approval support.',
            prompt: 'Show team leave insights and pending approvals.',
          },
          {
            title: 'Low Confidence Answers',
            description: `${analyticsSummary.lowConfidenceCount} answers need closer review before they repeat in production.`,
            prompt: 'Show low-confidence chatbot answers that need HR review.',
          },
          {
            title: 'Escalation Watchlist',
            description: `${analyticsSummary.escalationCount} escalations have been triggered in the latest analytics window.`,
            prompt: 'Show escalation hotspots and unresolved employee questions.',
          },
        ].map((item) => (
          <button
            key={item.title}
            onClick={() => onJourneySelect(item.prompt)}
            className="text-left bg-white rounded-[2rem] border border-slate-100 p-6 shadow-sm hover:shadow-md transition-all"
          >
            <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest mb-2">{item.title}</p>
            <p className="text-sm font-semibold text-slate-800 leading-relaxed">{item.description}</p>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.1fr,0.9fr] gap-6">
        <div className="bg-white rounded-[2rem] border border-slate-100 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h4 className="text-lg font-bold text-slate-800">Service Delivery Layer</h4>
              <p className="text-xs text-slate-500 mt-1">Map manager and HRBP questions to formal HR services and SLA-backed routes.</p>
            </div>
            <span className="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-[10px] font-black uppercase tracking-widest">
              {managerServices.length} services
            </span>
          </div>
          <div className="space-y-3">
            {managerServices.map((item) => (
              <button
                key={item.id}
                onClick={() => onJourneySelect(item.prompts[0])}
                className="w-full text-left rounded-2xl border border-slate-100 bg-slate-50 p-4 hover:bg-indigo-50 hover:border-indigo-100 transition-all"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest">{item.category}</p>
                    <p className="text-sm font-semibold text-slate-800 mt-1">{item.title}</p>
                  </div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase">SLA {item.slaHours}h</span>
                </div>
                <p className="text-xs text-slate-500 mt-2">{item.summary}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-[2rem] border border-slate-100 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h4 className="text-lg font-bold text-slate-800">Talent and Mobility</h4>
              <p className="text-xs text-slate-500 mt-1">Recruiting and internal mobility workflows that make the project feel closer to a full HR suite.</p>
            </div>
          </div>
          <div className="space-y-3">
            {talentWorkflows.map((workflow) => (
              <button
                key={workflow.id}
                onClick={() => onJourneySelect(workflow.prompt)}
                className="w-full text-left rounded-2xl border border-slate-100 bg-slate-50 p-4 hover:bg-indigo-50 hover:border-indigo-100 transition-all"
              >
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{workflow.stage}</p>
                <p className="text-sm font-semibold text-slate-800 mt-1">{workflow.title}</p>
                <p className="text-xs text-slate-500 mt-2">{workflow.summary}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function DashboardView({
  profile,
  user,
  employeeRecord,
  analyticsSummary,
  onJourneySelect,
}: {
  profile: UserProfile;
  user: User;
  employeeRecord: EmployeeRecord;
  analyticsSummary: AnalyticsSummary;
  onJourneySelect: (prompt: string) => void;
}) {
  const chartData = buildReimbursementChart(employeeRecord.reimbursementYtd);
  const modules = getEmployeeSelfServiceModules(employeeRecord);
  const serviceCatalog = listServiceCatalogItems().slice(0, 6);
  const talentWorkflows = getTalentWorkflows().slice(0, 2);
  const channels: ChannelExperience[] = getChannelExperiences().filter((item) => item.state !== 'planned');
  const stats = [
    { label: 'Casual Leave', value: `${employeeRecord.leaveBalances.casual} Days`, icon: Clock, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Earned Leave', value: `${employeeRecord.leaveBalances.earned} Days`, icon: Briefcase, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Sick Leave', value: `${employeeRecord.leaveBalances.sick} Days`, icon: LifeBuoy, color: 'text-rose-600', bg: 'bg-rose-50' },
    { label: 'Comp Off', value: `${employeeRecord.leaveBalances.compOff} Day`, icon: HistoryIcon, color: 'text-amber-600', bg: 'bg-amber-50' },
  ];
  const journeys = getGuidedJourneys(profile).slice(0, 6);
  const recentUpdates = [
    { title: 'HR service delivery layer is live with catalog-backed request flows.', date: 'Now', type: 'Platform' },
    { title: `${analyticsSummary.lowConfidenceCount} low-confidence answers flagged for weekly HR review`, date: 'Today', type: 'Quality' },
    { title: employeeRecord.travelClaimStatus, date: 'Latest', type: 'Travel' },
    { title: `${analyticsSummary.followUpResolutionRate}% follow-up resolution success in the latest AI ops window.`, date: 'Weekly', type: 'AI Ops' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto w-full space-y-8"
    >
      <div className="relative overflow-hidden bg-slate-900 rounded-[2.5rem] p-8 sm:p-12 text-white shadow-2xl shadow-indigo-100">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/20 blur-[100px] rounded-full -mr-20 -mt-20"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-emerald-500/10 blur-[80px] rounded-full -ml-24 -mb-24"></div>
        
        <div className="relative flex flex-col md:flex-row items-center gap-10">
          <div className="relative">
            <div className="w-32 h-32 rounded-[2.5rem] bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-4xl font-black border-4 border-white/10 shadow-2xl rotate-3 scale-110">
              {user.displayName?.[0] || 'U'}
            </div>
            <div className="absolute -bottom-2 -right-2 bg-emerald-500 text-white p-2 rounded-xl shadow-lg border-2 border-slate-900">
              <Check className="w-4 h-4" />
            </div>
          </div>
          
          <div className="text-center md:text-left flex-1">
            <h2 className="text-3xl font-black tracking-tight mb-2">
              {user.displayName || user.email}
            </h2>
            <div className="flex flex-wrap justify-center md:justify-start gap-3 items-center opacity-80 mb-6">
              <span className="px-3 py-1 bg-white/10 rounded-full text-[10px] font-bold uppercase tracking-widest border border-white/5 whitespace-nowrap">{profile.role}</span>
              <div className="w-1 h-1 bg-white/20 rounded-full"></div>
              <span className="text-xs font-medium">Employee ID: {profile.employeeId}</span>
              <div className="w-1 h-1 bg-white/20 rounded-full"></div>
              <span className="text-xs font-medium italic">{profile.grade} • {profile.location} • {profile.businessUnit}</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { label: 'Payroll Status', value: employeeRecord.payStubs[0]?.status || 'Verified', icon: ShieldCheck, color: 'text-emerald-400' },
                { label: 'Next Pay Day', value: 'May 31', icon: Wallet, color: 'text-indigo-400' },
                { label: 'Work Mode', value: profile.workMode, icon: Bot, color: 'text-amber-400' },
                { label: 'Active Cases', value: `${employeeRecord.activeCases} Open`, icon: HelpCircle, color: 'text-slate-400' },
              ].map((item) => (
                <div key={item.label} className="flex flex-col">
                  <p className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-1">{item.label}</p>
                  <div className="flex items-center gap-2">
                    <item.icon className={`w-3.5 h-3.5 ${item.color}`} />
                    <span className="text-sm font-bold">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div className="space-y-4">
            <div className="flex items-center justify-between px-2">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-600" /> Leave Balances
              </h3>
              <button
                onClick={() => onJourneySelect('Show my leave balance and missing attendance items.')}
                className="text-[10px] font-bold text-indigo-600 hover:underline uppercase tracking-tight"
              >
                Open Workflow
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {stats.map((stat) => (
                <div key={stat.label} className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm hover:shadow-md transition-all group overflow-hidden relative">
                  <div className={`absolute top-0 right-0 w-24 h-24 ${stat.bg} opacity-20 blur-2xl rounded-full -mr-10 -mt-10 group-hover:scale-150 transition-transform`}></div>
                  <div className="flex justify-between items-start relative z-10">
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
                      <h4 className="text-2xl font-black text-slate-800 tracking-tight">{stat.value}</h4>
                    </div>
                    <div className={`p-3 ${stat.bg} ${stat.color} rounded-2xl`}>
                      <stat.icon className="w-5 h-5" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h4 className="text-lg font-bold text-slate-800 tracking-tight flex items-center gap-2">
                  <LayoutDashboard className="w-5 h-5 text-indigo-600" /> HRIS Self Service
                </h4>
                <p className="text-xs text-slate-400 font-medium">Structured cards for leave, payroll, benefits, attendance, and approver chain.</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {modules.map((module) => (
                <button
                  key={module.id}
                  onClick={() => onJourneySelect(module.prompt)}
                  className="text-left rounded-[1.75rem] border border-slate-100 bg-slate-50 p-5 hover:bg-indigo-50 hover:border-indigo-100 transition-all"
                >
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{module.category}</p>
                  <p className="text-sm font-semibold text-slate-800 mt-2">{module.title}</p>
                  <p className="text-2xl font-black text-indigo-600 mt-3">{module.value}</p>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed">{module.detail}</p>
                  <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest mt-4">{module.actionLabel}</p>
                </button>
              ))}
            </div>
          </div>

          {/* New Analytics Card */}
          <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h4 className="text-lg font-bold text-slate-800 tracking-tight flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-indigo-600" /> Reimbursement Trends
                </h4>
                <p className="text-xs text-slate-400 font-medium">Profile-aware reimbursement activity for current FY</p>
              </div>
              <div className="flex gap-2">
                <span className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-full text-[10px] font-bold uppercase tracking-tight">
                  Total: {formatCurrency(employeeRecord.reimbursementYtd)}
                </span>
              </div>
            </div>
            <div className="h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <XAxis 
                    dataKey="name" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }} 
                  />
                  <Tooltip 
                    cursor={{ fill: '#f8fafc' }}
                    contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Bar dataKey="value" radius={[10, 10, 10, 10]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-lg font-bold text-slate-800 tracking-tight flex items-center gap-2">
                <Zap className="w-5 h-5 text-indigo-600" /> Guided Journeys
              </h4>
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Golden Prompts</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {journeys.map((journey) => (
                <button
                  key={journey.id}
                  onClick={() => onJourneySelect(journey.prompt)}
                  className="text-left p-5 rounded-[1.75rem] border border-slate-100 bg-slate-50 hover:bg-indigo-50 hover:border-indigo-100 transition-all"
                >
                  <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest mb-2">{journey.category}</p>
                  <p className="text-sm font-semibold text-slate-800 mb-2">{journey.title}</p>
                  <p className="text-xs text-slate-500 leading-relaxed">{journey.description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-[1.15fr,0.85fr] gap-8">
            <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h4 className="text-lg font-bold text-slate-800 tracking-tight flex items-center gap-2">
                    <FileBox className="w-5 h-5 text-indigo-600" /> HR Service Catalog
                  </h4>
                  <p className="text-xs text-slate-400 font-medium">Questions now map to formal HR services, routes, and SLAs instead of only free-text answers.</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {serviceCatalog.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => onJourneySelect(item.prompts[0])}
                    className="text-left rounded-[1.75rem] border border-slate-100 bg-slate-50 p-5 hover:bg-indigo-50 hover:border-indigo-100 transition-all"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest">{item.category}</p>
                      <span className="text-[10px] font-bold text-slate-400 uppercase">SLA {item.slaHours}h</span>
                    </div>
                    <p className="text-sm font-semibold text-slate-800 mt-2">{item.title}</p>
                    <p className="text-xs text-slate-500 mt-2 leading-relaxed">{item.summary}</p>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-4">{item.route}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm">
                <h4 className="text-lg font-bold text-slate-800 tracking-tight">Talent and Lifecycle</h4>
                <p className="text-xs text-slate-500 mt-1 mb-4">Add recruiting, onboarding, mobility, and exit journeys to make the product feel like a real HR suite.</p>
                <div className="space-y-3">
                  {talentWorkflows.map((workflow) => (
                    <button
                      key={workflow.id}
                      onClick={() => onJourneySelect(workflow.prompt)}
                      className="w-full text-left rounded-2xl border border-slate-100 bg-slate-50 p-4 hover:bg-indigo-50 hover:border-indigo-100 transition-all"
                    >
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{workflow.stage}</p>
                      <p className="text-sm font-semibold text-slate-800 mt-1">{workflow.title}</p>
                      <p className="text-xs text-slate-500 mt-2">{workflow.summary}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm">
                <h4 className="text-lg font-bold text-slate-800 tracking-tight">Cross Channel and Voice</h4>
                <p className="text-xs text-slate-500 mt-1 mb-4">Web, portal, mobile, and multilingual voice support create stronger HR product relevance.</p>
                <div className="space-y-3">
                  {channels.map((channel) => (
                    <div key={channel.id} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-slate-800">{channel.name}</p>
                        <span className={`px-2 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${
                          channel.state === 'live'
                            ? 'bg-emerald-50 text-emerald-600'
                            : 'bg-amber-50 text-amber-700'
                        }`}>
                          {channel.state}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-2 leading-relaxed">{channel.summary}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* HR Feed */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest flex items-center gap-2 px-2">
            <Activity className="w-4 h-4 text-indigo-600" /> Pulse Feed
          </h3>
          <div className="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden p-6 space-y-6">
            {recentUpdates.map((update) => (
              <div key={update.title} className="flex gap-4 group">
                <div className="w-10 h-10 rounded-xl bg-slate-50 flex flex-col items-center justify-center shrink-0 border border-slate-100 group-hover:bg-indigo-50 group-hover:border-indigo-100 transition-colors">
                  <span className="text-[10px] font-black text-slate-400 group-hover:text-indigo-600">NEW</span>
                </div>
                <div className="flex flex-col">
                  <h5 className="text-sm font-bold text-slate-800 leading-tight group-hover:text-indigo-600 transition-colors cursor-pointer">{update.title}</h5>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-bold text-slate-400">{update.date}</span>
                    <span className="w-1 h-1 bg-slate-200 rounded-full"></span>
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-tight">{update.type}</span>
                  </div>
                </div>
              </div>
            ))}
            <div className="border-t border-slate-100 pt-5">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Conversation Quality</p>
              <p className="text-sm font-semibold text-slate-800">{analyticsSummary.helpfulCount} helpful / {analyticsSummary.notUsefulCount} not useful</p>
              <p className="text-xs text-slate-500 mt-1">Low-confidence answers are pushed into weekly HR review so policy gaps get fixed quickly.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Security Statement */}
      <div className="bg-emerald-50/30 border border-emerald-100 rounded-2xl p-6 flex items-start gap-4">
        <div className="p-2 bg-emerald-500 text-white rounded-lg">
          <Shield className="w-4 h-4" />
        </div>
        <div>
          <p className="text-xs font-bold text-emerald-900 mb-1">Your data is secure and private.</p>
          <p className="text-xs text-emerald-700/70 leading-relaxed font-medium">
            This enterprise-mode demo uses role-aware local records so the chatbot can personalize answers, workflows, and nudges without exposing other employees&apos; details.
          </p>
        </div>
      </div>
    </motion.div>
  );
}

const LifeBuoy = (props: any) => (
  <svg
    {...props}
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10" />
    <path d="m4.93 4.93 4.24 4.24" />
    <path d="m14.83 9.17 4.24-4.24" />
    <path d="m14.83 14.83 4.24 4.24" />
    <path d="m9.17 14.83-4.24 4.24" />
    <circle cx="12" cy="12" r="4" />
  </svg>
);

const Activity = (props: any) => (
  <svg
    {...props}
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);
