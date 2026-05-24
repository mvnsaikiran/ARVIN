import React, { useMemo, useState } from 'react';
import {
  Activity,
  AlertCircle,
  BarChart3,
  Briefcase,
  CheckCircle2,
  ChevronLeft,
  FileText,
  History,
  Play,
  RotateCcw,
  Save,
  Search,
  ShieldCheck,
  Upload,
  Users,
} from 'lucide-react';
import { motion } from 'motion/react';
import { UserProfile } from '../lib/useUserProfile';
import {
  AnalyticsEvent,
  HRTicket,
  PolicyGovernanceRecord,
  getAIOpsSnapshot,
  getAnalyticsEvents,
  getAnalyticsSummary,
  getChannelExperiences,
  getComplianceControls,
  getContentOpsTasks,
  getGuidedJourneys,
  getPolicyAcknowledgments,
  getTalentWorkflows,
  listHRTickets,
  listServiceCatalogItems,
  listPolicyGovernanceRecords,
  publishPolicyRecord,
  reopenHRTicket,
  rollbackPolicyRecord,
  updateHRTicketStatus,
  upsertPolicyGovernanceRecord,
} from '../services/employeeExperienceService';

type AdminTab = 'governance' | 'catalog' | 'cases' | 'analytics' | 'compliance' | 'aiops' | 'content';

function createEditableRecord(record?: PolicyGovernanceRecord): PolicyGovernanceRecord {
  if (record) {
    return {
      ...record,
      auditTrail: [...record.auditTrail],
      previousVersions: [...record.previousVersions],
    };
  }

  return {
    id: `custom_${Date.now()}`,
    title: 'New Policy Draft',
    category: 'Operations',
    content: '',
    owner: 'Corporate HR',
    approver: 'BUHR Governance Desk',
    environment: 'draft',
    lifecycleStatus: 'draft',
    effectiveDate: new Date().toISOString().slice(0, 10),
    expiryDate: '',
    version: 1,
    benchmarkRequired: true,
    benchmarkPassed: false,
    lastBenchmarkAccuracy: 0,
    sourceDocumentName: '',
    updatedAt: Date.now(),
    auditTrail: [],
    previousVersions: [],
  };
}

function formatDate(timestamp: number) {
  return new Date(timestamp).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function statsForCases(tickets: HRTicket[]) {
  return {
    open: tickets.filter((ticket) => ticket.status === 'open').length,
    inReview: tickets.filter((ticket) => ticket.status === 'in_review').length,
    resolved: tickets.filter((ticket) => ticket.status === 'resolved').length,
    sensitive: tickets.filter((ticket) => ticket.confidentiality !== 'standard').length,
  };
}

export default function AdminDashboard({
  profile,
  onBack,
  onOpenBenchmark,
}: {
  profile: UserProfile;
  onBack: () => void;
  onOpenBenchmark?: () => void;
}) {
  const [activeTab, setActiveTab] = useState<AdminTab>('governance');
  const [records, setRecords] = useState<PolicyGovernanceRecord[]>(() => listPolicyGovernanceRecords());
  const [tickets, setTickets] = useState<HRTicket[]>(() => listHRTickets());
  const [events, setEvents] = useState<AnalyticsEvent[]>(() => getAnalyticsEvents());
  const [search, setSearch] = useState('');
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>(() => listPolicyGovernanceRecords()[0]?.id ?? createEditableRecord().id);
  const [draftRecord, setDraftRecord] = useState<PolicyGovernanceRecord>(() => createEditableRecord(listPolicyGovernanceRecords()[0]));
  const [changeNote, setChangeNote] = useState('Updated through Operations Center.');
  const [ticketFilter, setTicketFilter] = useState<'all' | HRTicket['status']>('all');
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/admin/upload-policy', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.success) {
        alert(`Successfully uploaded ${data.fileName} and synchronized ${data.ingestedChunks} chunks across engines.`);
      } else {
        alert('Upload failed: ' + data.error);
      }
    } catch (err) {
      alert('Upload error: ' + String(err));
    } finally {
      setIsUploading(false);
      event.target.value = '';
    }
  };

  const refreshAll = () => {
    const nextRecords = listPolicyGovernanceRecords();
    const nextTickets = listHRTickets();
    const nextEvents = getAnalyticsEvents();
    setRecords(nextRecords);
    setTickets(nextTickets);
    setEvents(nextEvents);

    const latestSelected = nextRecords.find((record) => record.id === selectedPolicyId);
    if (latestSelected) {
      setDraftRecord(createEditableRecord(latestSelected));
    }
  };

  const analyticsSummary = useMemo(() => getAnalyticsSummary(), [events]);
  const caseStats = useMemo(() => statsForCases(tickets), [tickets]);
  const guidedJourneys = useMemo(() => getGuidedJourneys(profile), [profile]);
  const serviceCatalog = useMemo(() => listServiceCatalogItems(), []);
  const complianceControls = useMemo(() => getComplianceControls(), [tickets]);
  const acknowledgements = useMemo(() => getPolicyAcknowledgments(), [records]);
  const talentWorkflows = useMemo(() => getTalentWorkflows(), []);
  const channels = useMemo(() => getChannelExperiences(), []);
  const aiOps = useMemo(() => getAIOpsSnapshot(), [events]);
  const contentOps = useMemo(() => getContentOpsTasks(), [records]);

  const filteredRecords = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return records.filter((record) => {
      if (!normalizedSearch) return true;
      return [
        record.title,
        record.category,
        record.owner,
        record.approver,
        record.sourceDocumentName,
      ].some((value) => value.toLowerCase().includes(normalizedSearch));
    });
  }, [records, search]);

  const filteredTickets = useMemo(() => {
    return tickets.filter((ticket) => ticketFilter === 'all' || ticket.status === ticketFilter);
  }, [tickets, ticketFilter]);

  const selectedRecord = records.find((record) => record.id === selectedPolicyId);
  const publishBlocked = draftRecord.benchmarkRequired && (!draftRecord.benchmarkPassed || draftRecord.lastBenchmarkAccuracy < 95);

  const handleSelectRecord = (record: PolicyGovernanceRecord) => {
    setSelectedPolicyId(record.id);
    setDraftRecord(createEditableRecord(record));
  };

  const handleNewRecord = () => {
    const next = createEditableRecord();
    setSelectedPolicyId(next.id);
    setDraftRecord(next);
  };

  const handleSaveRecord = () => {
    const persisted = upsertPolicyGovernanceRecord(
      {
        ...draftRecord,
        updatedAt: Date.now(),
      },
      profile.displayName,
      changeNote || 'Updated through Operations Center.',
    );
    setSelectedPolicyId(persisted.id);
    setDraftRecord(createEditableRecord(persisted));
    refreshAll();
  };

  const handlePublishRecord = () => {
    publishPolicyRecord(draftRecord.id, profile.displayName);
    refreshAll();
  };

  const handleRollbackRecord = () => {
    rollbackPolicyRecord(draftRecord.id, profile.displayName);
    refreshAll();
  };

  const handleCaseStatus = (ticketId: string, status: HRTicket['status']) => {
    updateHRTicketStatus(ticketId, status, profile.displayName);
    refreshAll();
  };

  const handleCaseReopen = (ticketId: string) => {
    reopenHRTicket(ticketId, profile.displayName);
    refreshAll();
  };

  return (
    <div className="flex h-screen bg-slate-50">
      <aside className="w-28 bg-slate-900 flex flex-col items-center py-8 gap-8 border-r border-slate-800">
        <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div className="flex flex-col gap-6 items-center">
          {[
            { id: 'governance', label: 'Policy', icon: FileText },
            { id: 'catalog', label: 'Catalog', icon: Users },
            { id: 'cases', label: 'Cases', icon: Briefcase },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'compliance', label: 'Guard', icon: ShieldCheck },
            { id: 'aiops', label: 'AI Ops', icon: Activity },
            { id: 'content', label: 'Content', icon: Play },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as AdminTab)}
              className={`flex flex-col items-center gap-2 p-4 rounded-2xl transition-all group w-20 ${
                activeTab === item.id ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 scale-105' : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <item.icon className="w-6 h-6 mb-1" />
              <span className="text-[10px] font-bold uppercase tracking-tight text-center">{item.label}</span>
            </button>
          ))}
        </div>
        <button onClick={onBack} className="mt-auto flex flex-col items-center gap-1 p-3 text-slate-500 hover:text-white transition-all">
          <ChevronLeft className="w-6 h-6" />
          <span className="text-[8px] font-black uppercase tracking-tighter">Exit</span>
        </button>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-slate-200 px-8 py-6 flex items-start justify-between gap-6">
          <div>
            <p className="text-[10px] font-black text-indigo-500 uppercase tracking-[0.25em] mb-2">Arvind HR Pulse</p>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Operations Center</h1>
            <p className="text-sm text-slate-500 mt-2 max-w-3xl">
              Govern policies, monitor confidence, review escalations, and keep the employee experience above the production quality bar before you publish updates.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 min-w-[280px]">
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Benchmark Gate</p>
              <p className="text-2xl font-black text-emerald-600 mt-1">
                {Math.round(records.reduce((sum, record) => sum + record.lastBenchmarkAccuracy, 0) / Math.max(records.length, 1))}%
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Escalations</p>
              <p className="text-2xl font-black text-amber-600 mt-1">{analyticsSummary.escalationCount}</p>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8">
          {activeTab === 'governance' && (
            <div className="grid grid-cols-1 xl:grid-cols-[340px,1fr] gap-8">
              <section className="bg-white rounded-[2rem] border border-slate-100 shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest">Policy Governance</h2>
                  <div className="flex gap-2">
                    <label className="px-3 py-2 rounded-xl bg-slate-900 text-white text-[11px] font-bold hover:bg-slate-800 cursor-pointer flex items-center gap-1">
                      {isUploading ? 'Uploading...' : <><Upload className="w-3 h-3" /> Upload PDF</>}
                      <input type="file" className="hidden" accept=".pdf,.docx,.doc" onChange={handleFileUpload} disabled={isUploading} />
                    </label>
                    <button
                      onClick={handleNewRecord}
                      className="px-3 py-2 rounded-xl bg-indigo-50 text-indigo-700 text-[11px] font-bold hover:bg-indigo-100"
                    >
                      New Draft
                    </button>
                  </div>
                </div>
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search title, owner, source..."
                    className="w-full pl-10 pr-4 py-3 bg-slate-50 rounded-xl border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
                  {filteredRecords.map((record) => (
                    <button
                      key={record.id}
                      onClick={() => handleSelectRecord(record)}
                      className={`w-full text-left p-4 rounded-2xl border transition-all ${
                        selectedPolicyId === record.id ? 'bg-indigo-50 border-indigo-100 shadow-sm' : 'bg-white border-slate-100 hover:border-indigo-100'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <span className="text-[10px] font-black text-indigo-500 uppercase tracking-widest">{record.category}</span>
                        <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-full ${
                          record.lifecycleStatus === 'published' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {record.lifecycleStatus}
                        </span>
                      </div>
                      <p className="text-sm font-bold text-slate-800 leading-tight">{record.title}</p>
                      <p className="text-xs text-slate-500 mt-2">{record.owner} • v{record.version}</p>
                      <p className="text-xs text-slate-400 mt-1">{record.sourceDocumentName || 'Source document not mapped yet'}</p>
                    </button>
                  ))}
                </div>
              </section>

              <section className="bg-white rounded-[2rem] border border-slate-100 shadow-sm p-8">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-8">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">{draftRecord.title}</h2>
                    <p className="text-sm text-slate-500 mt-1">
                      Owner: {draftRecord.owner} • Approver: {draftRecord.approver} • Updated {formatDate(draftRecord.updatedAt)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <button
                      onClick={handleRollbackRecord}
                      disabled={draftRecord.previousVersions.length === 0}
                      className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 text-sm font-bold disabled:opacity-50"
                    >
                      <span className="inline-flex items-center gap-2"><RotateCcw className="w-4 h-4" />Rollback</span>
                    </button>
                    <button
                      onClick={handleSaveRecord}
                      className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-bold"
                    >
                      <span className="inline-flex items-center gap-2"><Save className="w-4 h-4" />Save</span>
                    </button>
                    <button
                      onClick={handlePublishRecord}
                      disabled={publishBlocked}
                      className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-bold disabled:bg-slate-300"
                    >
                      Publish
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Owner</span>
                    <input
                      value={draftRecord.owner}
                      onChange={(event) => setDraftRecord({ ...draftRecord, owner: event.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Approver</span>
                    <input
                      value={draftRecord.approver}
                      onChange={(event) => setDraftRecord({ ...draftRecord, approver: event.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Environment</span>
                    <select
                      value={draftRecord.environment}
                      onChange={(event) => setDraftRecord({ ...draftRecord, environment: event.target.value as PolicyGovernanceRecord['environment'] })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    >
                      <option value="draft">Draft</option>
                      <option value="staging">Staging</option>
                      <option value="published">Published</option>
                    </select>
                  </label>
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Lifecycle</span>
                    <select
                      value={draftRecord.lifecycleStatus}
                      onChange={(event) => setDraftRecord({ ...draftRecord, lifecycleStatus: event.target.value as PolicyGovernanceRecord['lifecycleStatus'] })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    >
                      <option value="draft">Draft</option>
                      <option value="in_review">In Review</option>
                      <option value="approved">Approved</option>
                      <option value="published">Published</option>
                      <option value="expired">Expired</option>
                    </select>
                  </label>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Policy Title</span>
                    <input
                      value={draftRecord.title}
                      onChange={(event) => setDraftRecord({ ...draftRecord, title: event.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Category</span>
                    <input
                      value={draftRecord.category}
                      onChange={(event) => setDraftRecord({ ...draftRecord, category: event.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Effective Date</span>
                    <input
                      type="date"
                      value={draftRecord.effectiveDate}
                      onChange={(event) => setDraftRecord({ ...draftRecord, effectiveDate: event.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Expiry Date</span>
                    <input
                      type="date"
                      value={draftRecord.expiryDate}
                      onChange={(event) => setDraftRecord({ ...draftRecord, expiryDate: event.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </label>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
                  <label className="space-y-2 lg:col-span-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Source Document</span>
                    <input
                      value={draftRecord.sourceDocumentName}
                      onChange={(event) => setDraftRecord({ ...draftRecord, sourceDocumentName: event.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Benchmark Accuracy</span>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={draftRecord.lastBenchmarkAccuracy}
                      onChange={(event) => setDraftRecord({ ...draftRecord, lastBenchmarkAccuracy: Number(event.target.value) })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </label>
                </div>

                <div className="flex flex-wrap gap-6 mb-8">
                  <label className="inline-flex items-center gap-3 text-sm text-slate-600">
                    <input
                      type="checkbox"
                      checked={draftRecord.benchmarkRequired}
                      onChange={(event) => setDraftRecord({ ...draftRecord, benchmarkRequired: event.target.checked })}
                    />
                    Mandatory re-benchmark before publish
                  </label>
                  <label className="inline-flex items-center gap-3 text-sm text-slate-600">
                    <input
                      type="checkbox"
                      checked={draftRecord.benchmarkPassed}
                      onChange={(event) => setDraftRecord({ ...draftRecord, benchmarkPassed: event.target.checked })}
                    />
                    Benchmark gate passed
                  </label>
                </div>

                {publishBlocked && (
                  <div className="mb-8 p-4 rounded-2xl border border-amber-200 bg-amber-50 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-amber-700 mt-0.5" />
                    <div>
                      <p className="text-sm font-bold text-amber-900">Publishing is blocked until benchmark accuracy is 95% or higher.</p>
                      <p className="text-xs text-amber-700 mt-1">
                        Either clear the benchmark gate for this policy record or rerun the balanced benchmark before publishing.
                      </p>
                    </div>
                  </div>
                )}

                <label className="block space-y-2 mb-8">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Governance Notes / Summary</span>
                  <textarea
                    value={draftRecord.content}
                    onChange={(event) => setDraftRecord({ ...draftRecord, content: event.target.value })}
                    rows={8}
                    className="w-full px-4 py-4 rounded-2xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </label>

                <label className="block space-y-2 mb-8">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Change Log Note</span>
                  <input
                    value={changeNote}
                    onChange={(event) => setChangeNote(event.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </label>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2 mb-4">
                      <History className="w-4 h-4 text-indigo-600" /> Audit Trail
                    </h3>
                    <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                      {draftRecord.auditTrail.length > 0 ? draftRecord.auditTrail.map((entry) => (
                        <div key={entry.id} className="rounded-xl bg-white border border-slate-100 p-4">
                          <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest">{entry.action}</p>
                          <p className="text-sm font-semibold text-slate-800 mt-1">{entry.note}</p>
                          <p className="text-xs text-slate-400 mt-2">{entry.actor} • {formatDate(entry.timestamp)}</p>
                        </div>
                      )) : (
                        <p className="text-sm text-slate-500">No audit entries yet for this record.</p>
                      )}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2 mb-4">
                      <RotateCcw className="w-4 h-4 text-indigo-600" /> Previous Versions
                    </h3>
                    <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                      {draftRecord.previousVersions.length > 0 ? draftRecord.previousVersions.map((version) => (
                        <div key={`${draftRecord.id}_${version.version}`} className="rounded-xl bg-white border border-slate-100 p-4">
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Version {version.version}</p>
                          <p className="text-sm font-semibold text-slate-800 mt-1">{version.title}</p>
                          <p className="text-xs text-slate-500 mt-2">{formatDate(version.updatedAt)}</p>
                        </div>
                      )) : (
                        <p className="text-sm text-slate-500">No previous versions stored yet.</p>
                      )}
                    </div>
                  </div>
                </div>
              </section>
            </div>
          )}

          {activeTab === 'catalog' && (
            <div className="space-y-8">
              <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                {[
                  { label: 'Catalog Items', value: serviceCatalog.length, tone: 'text-indigo-600' },
                  { label: 'Talent Flows', value: talentWorkflows.length, tone: 'text-emerald-600' },
                  { label: 'Channels', value: channels.length, tone: 'text-sky-600' },
                  { label: 'Ack Campaigns', value: acknowledgements.length, tone: 'text-amber-600' },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</p>
                    <p className={`text-3xl font-black mt-2 ${stat.tone}`}>{stat.value}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-[1.1fr,0.9fr] gap-6">
                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">HR Service Catalog</h2>
                  <div className="space-y-3">
                    {serviceCatalog.map((item) => (
                      <div key={item.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest">{item.category}</p>
                            <p className="text-sm font-semibold text-slate-800 mt-1">{item.title}</p>
                          </div>
                          <span className="text-[10px] font-bold text-slate-400 uppercase">SLA {item.slaHours}h</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-2">{item.summary}</p>
                        <p className="text-xs text-slate-400 mt-3">Route: {item.route} | Queue: {item.defaultAssignmentGroup}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                    <h2 className="text-lg font-bold text-slate-900 mb-4">Talent and Recruiting</h2>
                    <div className="space-y-3">
                      {talentWorkflows.map((workflow) => (
                        <div key={workflow.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{workflow.stage}</p>
                          <p className="text-sm font-semibold text-slate-800 mt-1">{workflow.title}</p>
                          <p className="text-xs text-slate-500 mt-2">{workflow.summary}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                    <h2 className="text-lg font-bold text-slate-900 mb-4">Cross-Channel Rollout</h2>
                    <div className="space-y-3">
                      {channels.map((channel) => (
                        <div key={channel.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4 flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-slate-800">{channel.name}</p>
                            <p className="text-xs text-slate-500 mt-1">{channel.summary}</p>
                          </div>
                          <span className={`px-2 py-1 rounded-full text-[10px] font-black uppercase ${
                            channel.state === 'live'
                              ? 'bg-emerald-50 text-emerald-600'
                              : channel.state === 'pilot'
                                ? 'bg-amber-50 text-amber-700'
                                : 'bg-slate-100 text-slate-500'
                          }`}>
                            {channel.state}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'cases' && (
            <div className="space-y-8">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Open', value: caseStats.open, tone: 'text-indigo-600' },
                  { label: 'In Review', value: caseStats.inReview, tone: 'text-amber-600' },
                  { label: 'Resolved', value: caseStats.resolved, tone: 'text-emerald-600' },
                  { label: 'Sensitive', value: caseStats.sensitive, tone: 'text-rose-600' },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</p>
                    <p className={`text-3xl font-black mt-2 ${stat.tone}`}>{stat.value}</p>
                  </div>
                ))}
              </div>

              <div className="bg-white rounded-[2rem] border border-slate-100 shadow-sm p-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">Employee Cases and Human Handoffs</h2>
                    <p className="text-sm text-slate-500">Track HR tickets, grievance routing, POSH confidentiality, and case progress.</p>
                  </div>
                  <select
                    value={ticketFilter}
                    onChange={(event) => setTicketFilter(event.target.value as typeof ticketFilter)}
                    className="px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-100"
                  >
                    <option value="all">All statuses</option>
                    <option value="open">Open</option>
                    <option value="assigned">Assigned</option>
                    <option value="in_review">In review</option>
                    <option value="resolved">Resolved</option>
                  </select>
                </div>

                <div className="space-y-4">
                  {filteredTickets.map((ticket) => (
                    <div key={ticket.id} className="rounded-[1.75rem] border border-slate-100 bg-slate-50 p-5">
                      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                        <div className="space-y-2">
                          <div className="flex items-center flex-wrap gap-2">
                            <span className="text-[10px] font-black uppercase tracking-widest text-indigo-500">{ticket.kind.replace('_', ' ')}</span>
                            <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-full ${
                              ticket.confidentiality === 'strictly-confidential'
                                ? 'bg-rose-50 text-rose-700'
                                : ticket.confidentiality === 'confidential'
                                  ? 'bg-amber-50 text-amber-700'
                                  : 'bg-emerald-50 text-emerald-700'
                            }`}>
                              {ticket.confidentiality}
                            </span>
                            <span className="text-[10px] font-black uppercase px-2 py-1 rounded-full bg-white border border-slate-200 text-slate-500">
                              {ticket.status}
                            </span>
                          </div>
                          <h3 className="text-lg font-bold text-slate-900">{ticket.title}</h3>
                          <p className="text-sm text-slate-600 leading-relaxed">{ticket.summary}</p>
                          <p className="text-xs text-slate-400">
                            {ticket.id} • {ticket.employeeName} • {ticket.employeeGrade} • {ticket.employeeLocation} • Route {ticket.route}
                          </p>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                            <div className="rounded-xl border border-slate-200 bg-white p-3">
                              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Assignment</p>
                              <p className="text-xs text-slate-700 mt-2">{ticket.assignmentGroup}</p>
                            </div>
                            <div className="rounded-xl border border-slate-200 bg-white p-3">
                              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">SLA / Due</p>
                              <p className="text-xs text-slate-700 mt-2">{ticket.slaHours}h</p>
                              <p className="text-[11px] text-slate-400 mt-1">{formatDate(ticket.dueAt)}</p>
                            </div>
                            <div className="rounded-xl border border-slate-200 bg-white p-3">
                              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Workflow</p>
                              <p className="text-xs text-slate-700 mt-2">{ticket.subtasks.length} subtasks</p>
                              <p className="text-[11px] text-slate-400 mt-1">{ticket.statusHistory[0]?.note || 'No history yet'}</p>
                            </div>
                          </div>
                          {ticket.transcriptExcerpt && (
                            <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-500 whitespace-pre-wrap">
                              {ticket.transcriptExcerpt}
                            </div>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => handleCaseStatus(ticket.id, 'assigned')}
                            className="px-3 py-2 rounded-xl bg-white border border-slate-200 text-[11px] font-bold text-slate-600"
                          >
                            Assign
                          </button>
                          <button
                            onClick={() => handleCaseStatus(ticket.id, 'in_review')}
                            className="px-3 py-2 rounded-xl bg-amber-50 border border-amber-200 text-[11px] font-bold text-amber-700"
                          >
                            Review
                          </button>
                          <button
                            onClick={() => handleCaseStatus(ticket.id, 'resolved')}
                            className="px-3 py-2 rounded-xl bg-emerald-50 border border-emerald-200 text-[11px] font-bold text-emerald-700"
                          >
                            Resolve
                          </button>
                          <button
                            onClick={() => handleCaseReopen(ticket.id)}
                            className="px-3 py-2 rounded-xl bg-slate-100 border border-slate-200 text-[11px] font-bold text-slate-700"
                          >
                            Reopen
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-8">
              <div className="grid grid-cols-2 xl:grid-cols-7 gap-4">
                {[
                  { label: 'Total Interactions', value: analyticsSummary.totalInteractions, tone: 'text-slate-900' },
                  { label: 'Low Confidence', value: analyticsSummary.lowConfidenceCount, tone: 'text-amber-600' },
                  { label: 'Escalations', value: analyticsSummary.escalationCount, tone: 'text-rose-600' },
                  { label: 'Helpful', value: analyticsSummary.helpfulCount, tone: 'text-emerald-600' },
                  { label: 'Not Useful', value: analyticsSummary.notUsefulCount, tone: 'text-slate-500' },
                  { label: 'Learning Cases', value: analyticsSummary.learningCaseCount, tone: 'text-indigo-600' },
                  { label: 'Loop Coverage', value: `${analyticsSummary.resolutionLoopCoverage}%`, tone: 'text-sky-600' },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</p>
                    <p className={`text-3xl font-black mt-2 ${stat.tone}`}>{stat.value}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">Top Unanswered Questions</h2>
                  <div className="space-y-3">
                    {analyticsSummary.unansweredQueries.length > 0 ? analyticsSummary.unansweredQueries.map((query) => (
                      <div key={query} className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-700">
                        {query}
                      </div>
                    )) : (
                      <p className="text-sm text-slate-500">No unresolved questions in the current analytics window.</p>
                    )}
                  </div>
                </div>

                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">Policy Usage</h2>
                  <div className="space-y-3">
                    {analyticsSummary.policyUsage.map((item) => (
                      <div key={item.policyId} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div>
                          <p className="text-sm font-semibold text-slate-800">{item.policyName}</p>
                          <p className="text-xs text-slate-400">{item.policyId}</p>
                        </div>
                        <p className="text-lg font-black text-indigo-600">{item.count}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">Grade / Location Hotspots</h2>
                  <div className="space-y-4">
                    <div>
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Grade</p>
                      <div className="space-y-2">
                        {analyticsSummary.gradeHotspots.slice(0, 5).map((item) => (
                          <div key={item.grade} className="flex items-center justify-between text-sm">
                            <span className="text-slate-700">{item.grade}</span>
                            <span className="font-bold text-indigo-600">{item.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Location</p>
                      <div className="space-y-2">
                        {analyticsSummary.locationHotspots.slice(0, 5).map((item) => (
                          <div key={item.location} className="flex items-center justify-between text-sm">
                            <span className="text-slate-700">{item.location}</span>
                            <span className="font-bold text-indigo-600">{item.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">Confusion Hotspots</h2>
                  <div className="space-y-3">
                    {analyticsSummary.confusionHotspots.length > 0 ? analyticsSummary.confusionHotspots.map((item) => (
                      <div key={item.topic} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div>
                          <p className="text-sm font-semibold text-slate-800">{item.topic}</p>
                          <p className="text-xs text-slate-400 mt-1">Repeated low-confidence or unresolved traffic</p>
                        </div>
                        <p className="text-lg font-black text-amber-600">{item.count}</p>
                      </div>
                    )) : (
                      <p className="text-sm text-slate-500">No confusion hotspots detected in the current analytics window.</p>
                    )}
                  </div>
                </div>

                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">Risk Signals</h2>
                  <div className="space-y-3">
                    {analyticsSummary.riskSignals.length > 0 ? analyticsSummary.riskSignals.map((item) => (
                      <div key={item.signal} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div>
                          <p className="text-sm font-semibold text-slate-800">{item.signal}</p>
                          <p className="text-xs text-slate-400 mt-1">Operational watch signal from live conversations</p>
                        </div>
                        <p className="text-lg font-black text-rose-600">{item.count}</p>
                      </div>
                    )) : (
                      <p className="text-sm text-slate-500">No active risk clusters in the current analytics window.</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-bold text-slate-900 mb-4">Recent Conversation Events</h2>
                <div className="space-y-3">
                  {events.slice(0, 10).map((event) => (
                    <div key={event.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-800">{event.query}</p>
                        <p className="text-xs text-slate-400 mt-1">
                          {event.policyId || 'Conversation Support'} • {event.grade} • {event.location} • {formatDate(event.timestamp)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="px-2 py-1 rounded-full bg-white border border-slate-200 text-slate-500">{event.responseType}</span>
                        <span className={`font-bold ${(event.confidenceScore ?? 0) >= 0.9 ? 'text-emerald-600' : (event.confidenceScore ?? 0) >= 0.75 ? 'text-amber-600' : 'text-rose-600'}`}>
                          {Math.round((event.confidenceScore ?? 0) * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'compliance' && (
            <div className="space-y-8">
              <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                {complianceControls.map((control) => (
                  <div key={control.id} className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{control.title}</p>
                    <p className={`text-xl font-black mt-3 ${
                      control.status === 'active'
                        ? 'text-emerald-600'
                        : control.status === 'watch'
                          ? 'text-amber-600'
                          : 'text-rose-600'
                    }`}>
                      {control.status}
                    </p>
                    <p className="text-xs text-slate-500 mt-3">{control.owner}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-[1fr,0.95fr] gap-6">
                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">Enterprise Compliance Controls</h2>
                  <div className="space-y-3">
                    {complianceControls.map((control) => (
                      <div key={control.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-semibold text-slate-800">{control.title}</p>
                          <span className={`px-2 py-1 rounded-full text-[10px] font-black uppercase ${
                            control.status === 'active'
                              ? 'bg-emerald-50 text-emerald-600'
                              : control.status === 'watch'
                                ? 'bg-amber-50 text-amber-700'
                                : 'bg-rose-50 text-rose-700'
                          }`}>
                            {control.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-2">{control.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">Policy Acknowledgments</h2>
                  <div className="space-y-3">
                    {acknowledgements.map((item) => (
                      <div key={item.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-slate-800">{item.policyName}</p>
                            <p className="text-xs text-slate-400 mt-1">{item.audience}</p>
                          </div>
                          <p className="text-xl font-black text-indigo-600">{item.completionRate}%</p>
                        </div>
                        <p className="text-xs text-slate-500 mt-2">Due {item.dueDate}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'aiops' && (
            <div className="space-y-8">
              <div className="grid grid-cols-2 xl:grid-cols-5 gap-4">
                {[
                  { label: 'Benchmark', value: `${aiOps.benchmarkAccuracy}%`, tone: 'text-emerald-600' },
                  { label: 'False Escalation', value: `${aiOps.falseEscalationRate}%`, tone: 'text-amber-600' },
                  { label: 'Follow-up Success', value: `${aiOps.followUpResolutionRate}%`, tone: 'text-indigo-600' },
                  { label: 'Unresolved Topics', value: aiOps.unresolvedTopicCount, tone: 'text-rose-600' },
                  { label: 'Learning Loop', value: `${aiOps.learningLoopCoverage}%`, tone: 'text-sky-600' },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</p>
                    <p className={`text-3xl font-black mt-2 ${stat.tone}`}>{stat.value}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-[1fr,1fr] gap-6">
                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">Policy Accuracy by Topic</h2>
                  <div className="space-y-3">
                    {aiOps.policyAccuracy.map((item) => (
                      <div key={item.policyId} className="rounded-xl border border-slate-100 bg-slate-50 p-4 flex items-center justify-between gap-4">
                        <div>
                          <p className="text-sm font-semibold text-slate-800">{item.policyName}</p>
                          <p className="text-xs text-slate-400 mt-1">{item.policyId}</p>
                        </div>
                        <p className="text-2xl font-black text-indigo-600">{item.score}%</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">AI Ops Operating Model</h2>
                  <div className="space-y-3 text-sm text-slate-600">
                    {[
                      'Balanced benchmark stays isolated from the normal chat cache path.',
                      'Low-confidence and unresolved answers feed weekly HR review.',
                      'Resolved cases write back into the approved learning-case loop.',
                      'Policy changes remain blocked until benchmark accuracy clears the publish gate.',
                      'Follow-up success and false escalations are now visible as operating metrics.',
                    ].map((item) => (
                      <div key={item} className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'content' && (
            <div className="space-y-8">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div className="rounded-[2rem] border border-slate-100 bg-white p-8 shadow-sm">
                  <h2 className="text-xl font-bold text-slate-900">Launch Readiness Playbook</h2>
                  <p className="text-sm text-slate-500 mt-2">
                    Use this view to drive adoption: push guided journeys, keep benchmark gates honest, and review the issues most likely to hurt employee trust if left unresolved.
                  </p>
                  <div className="mt-6 space-y-4">
                    {guidedJourneys.map((journey) => (
                      <div key={journey.id} className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
                        <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest">{journey.category}</p>
                        <p className="text-sm font-semibold text-slate-800 mt-2">{journey.title}</p>
                        <p className="text-xs text-slate-500 mt-2">{journey.description}</p>
                        <p className="text-xs text-slate-400 mt-3">Prompt: {journey.prompt}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="rounded-[2rem] border border-slate-100 bg-white p-8 shadow-sm">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-slate-900">Benchmark Gate</h2>
                        <p className="text-sm text-slate-500 mt-2">
                          Mandatory publish control: policy changes should not go live until the quality gate clears 95%+.
                        </p>
                      </div>
                      <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div className="mt-6 grid grid-cols-2 gap-4">
                      <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Passing Policies</p>
                        <p className="text-3xl font-black text-emerald-600 mt-2">
                          {records.filter((record) => !record.benchmarkRequired || (record.benchmarkPassed && record.lastBenchmarkAccuracy >= 95)).length}
                        </p>
                      </div>
                      <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Blocked Policies</p>
                        <p className="text-3xl font-black text-amber-600 mt-2">
                          {records.filter((record) => record.benchmarkRequired && (!record.benchmarkPassed || record.lastBenchmarkAccuracy < 95)).length}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={onOpenBenchmark}
                      className="mt-6 px-5 py-3 rounded-xl bg-indigo-600 text-white text-sm font-bold disabled:bg-slate-300"
                      disabled={!onOpenBenchmark}
                    >
                      Open Full Benchmark
                    </button>
                  </div>

                  <div className="rounded-[2rem] border border-slate-100 bg-white p-8 shadow-sm">
                    <h2 className="text-xl font-bold text-slate-900 mb-4">Content Ops Queue</h2>
                    <div className="space-y-3 text-sm text-slate-600">
                      {contentOps.map((item) => (
                        <div key={item.id} className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-semibold text-slate-800">{item.title}</span>
                            <span className={`text-[10px] font-black uppercase ${
                              item.status === 'done'
                                ? 'text-emerald-600'
                                : item.status === 'blocked'
                                  ? 'text-rose-600'
                                  : item.status === 'in_progress'
                                    ? 'text-amber-600'
                                    : 'text-slate-500'
                            }`}>
                              {item.status}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-2">{item.detail}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
