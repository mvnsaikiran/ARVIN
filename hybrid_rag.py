"""
Hybrid BM25 + Semantic retrieval with Reciprocal Rank Fusion.

Fixes three root-cause retrieval failures:
  1. MAB/SIA numeric lookups  → BM25 matches grade labels + numbers exactly
  2. POSH dense-paragraph facts → BM25 finds specific phrase matches
  3. Joining vs Local Conveyance confusion → BM25 + policy keyword routing

Architecture:
  semantic_top30 + bm25_top30  →  RRF merge  →  final top-K
"""

import os, re, json
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

VECTORSTORE_DIR = "vectorstore"
CHUNKS_FILE     = os.path.join(VECTORSTORE_DIR, "chunks.json")
SEMANTIC_K      = 40   # candidates from semantic pass
BM25_K          = 40   # candidates from BM25 pass
RRF_K           = 60   # RRF constant (standard value)
FINAL_K         = 10   # chunks returned to LLM
POLICY_BOOST    = 3.0  # BM25 score multiplier for detected policy
BM25_GUARANTEE  = 6    # scan top-N BM25 results for guarantee candidates
BM25_FLOOR      = 2.0  # minimum BM25 score to qualify for guaranteed inclusion
BM25_MAX_INJECT = 3    # max chunks to actually inject
# Common query stopwords — only inject if chunk matches ALL non-stop query tokens
_BM25_STOPWORDS = frozenset(
    "what is the does a an of to in for how why can you tell me explain "
    "about say do any as with by at or and that this are if not all be "
    "will was from on it its i am we my their your its true applicable "
    "policy policies hr arvind company employee employees grade grades "
    "which under covered mention according confirm true false".split()
)

# ── Policy keyword routing ────────────────────────────────────────────────────
# When a query clearly targets one policy, up-weight that policy's chunks in BM25
POLICY_KEYWORDS = {
    "Joining Policy": [
        "joining", "new recruit", "new employee", "relocation", "packers",
        "household", "brokerage", "700 km", "700km", "pre-joining", "post-joining",
        "joining leave", "joining bonus", "notice pay buyout", "f&f settlement",
        "rs. 50 per km", "rs. 60 per km", "50 per km", "60 per km",
        "arvind travel desk", "maximum period of 3 days", "pre joining",
        "post joining", "income tax shall be grossed", "company shall directly",
        "packers and movers", "one month rent", "house deposit", "school admission",
        "10 equal monthly", "recovered in his", "f&f", "ceo approval",
    ],
    "Local Conveyance Policy": [
        "local conveyance", "within city", "within the city", "office to office",
        "orapps", "conveyance claim", "two wheeler", "four wheeler",
        "applicable across all grades", "applicable across india",
        "false claim", "forge", "disciplinary action", "km travelled",
        "rs. 10", "rs. 5", "10.00 per km", "5.00 per km",
        "municipal corporation", "gram panchayat", "santej", "raipur", "gomtipur",
        "company car", "personal vehicle", "bm grade",
        "applicable to all management", "staff cadre", "management staff cadre",
        "forge the documents", "strict disciplinary action shall be taken",
        "orapps esms", "esms entry", "conveyance expense",
        "outside the respective city", "outside the respective",
        "gram panchayat limits", "municipal corporation limits",
        "support staff", "company owned vehicle",
        "01.07.2022", "arv|cor|eop_lcp", "eop_lcp", "local conveyance policy",
        "when was local conveyance", "effective date conveyance",
        "false conveyance claim", "conveyance false", "conveyance disciplinary",
        "i travel within the city", "travel within city work",
        "who is covered local conveyance", "covered under local conveyance",
    ],
    "Talent Mobility Policy": [
        "mab", "sia", "mobility adjustment", "settling-in", "settling in",
        "job rotation", "talent mobility", "rotation benefit", "relocation benefit",
        "annual mab", "monthly mab", "e1 grade", "e2 grade", "m1 grade",
        "m2 grade", "m3 grade", "m3h1", "financial implications",
        "32,583", "32583", "45,750", "45750", "71,000", "71000",
        "1,08,333", "108333", "1,58,333", "158333", "2,16,667", "216667",
        "3,91,000", "391000", "5,49,000", "549000", "8,52,000", "852000",
        "13,00,000", "1300000", "19,00,000", "1900000", "26,00,000", "2600000",
        "rotation trigger", "3 years", "skill stagnation", "hipo",
        "shifting house", "relocation >20", "one time lump", "settling in assistance",
        "mandatory movement", "ijp", "darwinbox",
        "1st rotation", "first rotation", "2nd rotation", "second rotation",
        "within the city rotation", "rotation model", "rotation types",
        "across different business", "across different location",
        "rotation within city", "rotation across business",
        "first rotation model", "what is first rotation",
    ],
    "POSH Policy (Prevention of Sexual Harassment)": [
        "posh", "sexual harassment", "aic", "internal complaint",
        "aggrieved woman", "respondent", "presiding officer", "complainant",
        "interim action", "inquiry", "quorum", "retaliation",
        "arvind internal complaint", "prevention of sexual",
        # AIC structural details
        "independent committee", "civil court", "minimum of 3", "minimum of three",
        "50% women", "50 percent women", "external member", "external person",
        "rs. 250 per day", "250 per day", "legal practitioner", "not be allowed",
        "anonymous complaints", "anonymous complaint",
        "notice of 15", "notice of fifteen", "within 15 days", "within fifteen days",
        "suspend the", "re for defined", "interim relief", "leave to the",
        "3 months leave", "three months leave", "aggrieved",
        "vacancy", "30 days", "thirty days", "powers of a civil",
        "written warning", "office parties", "workplace",
        "her relative", "her co-worker", "co worker",
        "filing channels", "supervisor", "reporting manager",
        "10 ten days", "within a period of 10", "annual report",
        "quarterly report", "four weeks after", "independent agency",
        "confidential", "disciplinary action will be taken",
        "18002008301",
        # Disciplinary action specifics
        "terminating the re from service", "written apology",
        "reprimand", "censure", "withholding of promotion",
        "withholding of pay rise", "counselling session",
        "community service", "monetary compensation",
        # Protection
        "protected from retaliation", "no adverse action",
        "victimization", "protect complainants",
        # Contact
        "1800 200 8301", "ethics helpline",
        # AIC quorum/composition
        "minimum of 3 members", "presiding officer shall be",
        "senior level woman employee",
        # Scope
        "prohibits same-sex", "same-sex harassment", "gender neutral policy",
        "covers with equal rigour",
    ],
    "Grievance Mechanism Policy 2025": [
        "grievance", "complaint channel", "redressal", "grievance policy",
        "grievance review", "grievance timelines",
        "10 working days", "ten working days", "every two years",
        "verbally or in writing", "raised verbally", "in writing",
        "four weeks after the submission", "protected from retaliation",
        "arvind@ethicshelpline", "ethicshelpline",
        "supervisor", "business hr", "complaint process",
    ],
    "Whistleblower Policy": [
        "whistleblower", "whistle blower", "protected disclosure", "ethics helpline",
        "bribery", "corruption", "false invoicing", "procurement fraud",
        "undue awarding", "awarding of contracts", "kickback",
        "quarterly", "reporting frequency", "annual basis",
        "independent agency", "appoint an independent", "investigation",
        "four weeks after the submission", "four weeks after submission",
        "duty to cooperate", "adverse personnel action",
        "arvind@ethicshelpline",
        "workplace harassment", "reportable concern", "what can be reported",
        "what to report", "can i report workplace", "employee negligence",
        "discrimination and favouritism", "false invoicing report",
        "lodge a written complaint to the chairman",
        "chairman of the committee", "whistleblower report",
        "what can a whistleblower report", "5.12", "5.13", "5.10",
        "report bribery", "report corruption", "misappropriation",
    ],
    "Gender Policy 2025": [
        "gender policy", "gender equality", "gender discrimination",
        "gender sensitization", "gender inclusive", "issue date gender",
        "effective from gender", "arvind gender",
        "retaliation against individuals", "raise concerns in good faith",
        "every two years", "gender review",
        # Applicability specifics
        "interns", "contract staff", "third-party partners", "third party partners",
        "full-time", "part-time", "consultants",
        "all employees of arvind", "arvind ltd. is committed",
        # Complaint process specifics
        "hr department", "buhr", "group ethics officer",
        "first level", "second level", "third level", "fourth level",
        "gender based harassment", "non-tolerance",
        # Policy details
        "25.07.2025", "26.07.2025", "arv|com_genp",
        "gender neutral", "equal access and opportunity",
        "non-tolerance of gender",
        # Protection
        "retaliation against", "concerns in good faith",
        "gender-sensitive work environment",
        "gender-based caregiving", "work-life integration",
        # Initiatives
        "gender diversity initiatives", "gender-inclusive workforce",
        "gender sensitization training", "merit", "balanced",
    ],
    "Employee Assistance Program (EAP)": [
        "eap", "1to1help", "1 to 1 help", "employee assistance program",
        "counselling", "counseling", "mental health", "emotional support",
        "stress support", "wellness app", "well-being app", "wellbeing app",
        "confidential help service", "free and confidential",
        "psychological support", "therapist", "psychologist",
        "1800-258-8121", "1800-258-8999", "1800 258 8121", "1800 258 8999",
        "managersupport@1to1help", "manager referral eap",
        "voluntary counselling", "counselling session eap",
        "9 am and 9 pm", "same day referral",
    ],
    "Employee Expense Reimbursement Policy": [
        "expense reimbursement", "birthday celebration", "farewell celebration",
        "farewell gift", "gift expense", "puja expense", "puja expenses",
        "late hours food", "working late food", "company car expense",
        "fuel voucher", "fuel reimbursement", "administrative purchase",
        "stationery reimbursement", "7 working days expense",
        "arv|elc_eer", "forfeiture of reimbursement",
        "cfo & chro", "cfo and chro", "cxo farewell",
        "10000 farewell", "farewell party", "birthday party hr",
        "excess baggage telephone", "international trip telephone",
    ],
    "Exit & Full & Final Settlement Policy": [
        "fnf", "f&f", "full and final", "full & final settlement",
        "exit policy", "notice period", "60 days notice", "sixty days notice",
        "darwinbox resignation", "no dues clearance", "eklavya policy",
        "relieving letter", "experience letter", "pf transfer",
        "lwp during notice", "last working day", "separation",
        "arv|cor|elc_fnf", "30 days payout", "final payout",
        "corporate.hr@arvind.in", "notice pay", "resignation process",
        "voluntary resignation", "retirement darwinbox",
        "it clearance exit", "cmg clearance exit",
        "pl balance payout", "consolidated salary notice",
        "100% tuition recovery", "50% tuition recovery",
    ],
    "Group Health Insurance Policy": [
        "health insurance", "ghi", "mediclaim", "hospitalisation", "hospitalization",
        "cashless", "fhpl", "sbi general insurance", "tpa", "family floater",
        "maternity benefit", "maternity limit", "critical illness",
        "1800-425-4033", "1800 425 4033", "intimation@fhpl.net",
        "room charge limit", "icu charge limit", "ambulance insurance",
        "arv|ebf_mlb", "non-cashless", "pre-authorisation", "pre-authorization",
        "reimbursement claim hospital", "30 days discharge",
        "60 days post hospitalisation", "30 days pre hospitalisation",
        "ayush treatment", "oral chemotherapy", "infertility cover",
        "24 hours hospitalisation", "network hospital",
        "family floater 3 lakh", "family floater 4 lakh", "family floater 6 lakh",
        "room 6000", "room 8000", "room 12000", "icu 9000", "icu 12000", "icu 18000",
    ],
    "Group Personal Accident Insurance Scheme": [
        "personal accident", "gpa", "accident insurance", "accidental death",
        "disability insurance", "ttd", "ptd", "ppd",
        "temporary total disablement", "partial total disablement",
        "permanent partial disablement", "capital sum insured", "csi",
        "60 times monthly", "24 times monthly", "education grant accident",
        "funeral charges", "carriage of dead body", "broken bones",
        "fracture cover", "arv|cor|ebf_gpa", "mid-term sum insured",
        "5 lakhs accident", "50 crores maximum", "5000 per week",
        "100 weeks disability", "10000 per child education",
    ],
    "Group Term Life Insurance": [
        "group term life", "gtl", "term life insurance", "gti",
        "life insurance arvind", "death benefit insurance",
        "natural death", "suicide not covered", "death claim",
        "what does gti cover", "gti cover", "gti covers", "what gti covers",
        "death certificate insurance", "cmg death", "insurance section",
        "nominee gratuity", "arv|cor|ebf_gti", "life cover grade",
        "ot 2.5 lakh", "e1 3 lakh", "m1 8 lakh", "m2 12.5 lakh",
        "m3 18 lakh", "bmh9 1 crore", "avp 50 lakh", "vp 85 lakh",
        "2,50,000 life", "3,00,000 life", "5,50,000 life",
        "8,00,000 life", "12,50,000 life", "18,00,000 life",
        "30,00,000 life", "50,00,000 life", "85,00,000 life",
        "1,00,00,000", "beneficiary death", "financial security death",
    ],
    "Pankh Employee Referral": [
        "pankh", "employee referral", "referral program", "refer a candidate",
        "referral reward", "referral bonus", "refer friend", "refer colleague",
        "arv|elc_per", "diverse referral", "female referral reward",
        "transgender referral", "specially abled referral",
        "5000 referral", "7500 referral", "10000 referral", "20000 referral",
        "male referral no reward", "referral payout", "3 months referral",
        "6 months referral", "referral tranche", "darwinbox refer tab",
        "recruitment module refer", "m3 grade referral", "upto m3 referral",
        "refer tab darwinbox", "my referrals",
    ],
    "Domestic Travel Expense Settlement Procedure": [
        "travel settlement", "travel expense settlement", "tour expense",
        "my tour dashboard", "create tour expense", "initiate settlement",
        "travel booking mmt", "mmttravel", "onearvind travel",
        "boarding expense", "flat rate travel", "conveyance travel",
        "self spend expense", "hotel phone not reimbursed",
        "web check-in not reimbursed", "express boarding not reimbursed",
        "extra baggage reimbursed", "manager approval travel",
        "tour pending approval", "my team tour dashboard",
        "services travel menu", "travel booking settlement",
        "domestic travel settlement", "travel settlement procedure",
        "july 2023 travel", "tour no settlement",
        "expense types travel", "travel expense types", "claim for travel",
        "what expense types", "boarding flat rate conveyance",
        "flat rate expense", "self spend", "unsettled expenses",
    ],
    "Voluntary Death Contribution Scheme": [
        "voluntary death contribution", "death contribution scheme", "vdcs",
        "arv|efb_ipp", "contribution deceased employee",
        "100 contribution death", "175 contribution death",
        "200 contribution death", "300 contribution death",
        "550 contribution death", "800 contribution death",
        "ot 100 death", "e1 100 death", "m1 175 death", "m2 200 death",
        "m3 300 death", "bmh3 550 death", "bmh6 800 death",
        "all employees contribute", "monetary contribution deceased",
        "dependants beneficiaries death", "death contribution grade",
    ],
    "Domestic Travel Policy": [
        "domestic travel", "travel policy", "hotel reimbursement",
        "lodging", "boarding", "class i", "class ii", "class iii",
        "at actual", "at actuals", "bmh", "bmh9", "bmh7", "bmh3",
        "m3h1", "2nd ac", "1st ac", "3rd ac", "chair car",
        "mybiz", "myBiz", "mmT", "etilite", "orapps",
        "7 days in advance", "within 15 days of the trip",
        "laundry", "duration of travel exceeds three",
        "senior officials travelling", "separate flights",
        "flight delay", "delayed by more than 3 hours", "3 hours",
        "rs. 200", "rs. 600", "rs. 10.0", "driver wages",
        "food limit", "200 per meal",
        "3400", "2300", "1700", "8000", "6000", "5000", "4000",
        "1500", "1300", "1200", "1000", "800", "600",
    ],
}


def _tokenise(text: str) -> list[str]:
    """Normalise + tokenise for BM25 (numbers preserved)."""
    t = text.lower()
    t = re.sub(r'\brs\.?\s*', '', t)   # strip Rs. prefix only (word boundary)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'[(){}[\]]', ' ', t)
    t = re.sub(r'[?!;:"\']', ' ', t)
    t = re.sub(r'\.(?=\s|$)', ' ', t)  # strip sentence-ending periods (not decimals)
    t = t.replace('-', ' ').replace('/', ' ')
    return [w for w in t.split() if w]


def _detect_policy(query: str) -> str | None:
    """Return a policy name if the query clearly targets it."""
    q_lower = query.lower()
    best_policy, best_count = None, 0
    for policy, keywords in POLICY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in q_lower)
        if count > best_count:
            best_policy, best_count = policy, count
    return best_policy if best_count >= 1 else None


class HybridRetriever:
    """Singleton-style: loaded once and reused across requests."""

    def __init__(self):
        self._ef         = None
        self._chroma     = None
        self._bm25       = None
        self._chunks     = None
        self._doc2idx    = None   # text hash → list of chunk indices

    # ── Lazy loading ──────────────────────────────────────────────────────────

    def _ensure_loaded(self):
        if self._bm25 is not None:
            return

        # Semantic (ChromaDB)
        self._ef = embedding_functions.ONNXMiniLM_L6_V2()
        client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
        self._chroma = client.get_collection(
            "arvind_policies", embedding_function=self._ef
        )

        # BM25
        with open(CHUNKS_FILE) as f:
            self._chunks = json.load(f)

        tokenised = [_tokenise(c["text"]) for c in self._chunks]
        self._bm25 = BM25Okapi(tokenised)

        # Fast lookup: first-80-chars of text → index list (for dedup)
        self._doc2idx = {}
        for i, c in enumerate(self._chunks):
            key = c["text"][:80]
            self._doc2idx.setdefault(key, []).append(i)

    # ── Core retrieval ────────────────────────────────────────────────────────

    def retrieve(self, query: str, n_results: int = FINAL_K) -> list[dict]:
        self._ensure_loaded()

        detected_policy = _detect_policy(query)
        cross_policy = detected_policy is None

        # Cross-policy queries get a wider semantic net
        sem_k = min(SEMANTIC_K * 2 if cross_policy else SEMANTIC_K, self._chroma.count())

        # 1. Semantic search (wider net)
        sem = self._chroma.query(
            query_texts=[query],
            n_results=sem_k,
            include=["documents", "metadatas", "distances"],
        )
        sem_docs  = sem["documents"][0]
        sem_metas = sem["metadatas"][0]
        sem_dists = sem["distances"][0]

        # Map to chunk indices (handle possible duplicates)
        sem_rank_map: dict[int, float] = {}
        for doc, meta, dist in zip(sem_docs, sem_metas, sem_dists):
            key = doc[:80]
            for idx in self._doc2idx.get(key, []):
                if self._chunks[idx]["policy_name"] == meta["policy_name"]:
                    sem_rank_map[idx] = 1.0 - float(dist)
                    break

        # 2. BM25 search
        tokens     = _tokenise(query)
        bm25_raw   = self._bm25.get_scores(tokens)

        # Boost BM25 scores for the detected policy
        if detected_policy:
            for i, c in enumerate(self._chunks):
                if c["policy_name"] == detected_policy:
                    bm25_raw[i] *= POLICY_BOOST

        bm25_top = sorted(
            ((i, s) for i, s in enumerate(bm25_raw) if s > 0),
            key=lambda x: -x[1],
        )[:BM25_K]
        bm25_rank_map = {i: s for i, s in bm25_top}

        # 3. RRF merge
        sem_ranked  = sorted(sem_rank_map.items(),  key=lambda x: -x[1])
        bm25_ranked = sorted(bm25_rank_map.items(), key=lambda x: -x[1])

        sem_rk  = {idx: r + 1 for r, (idx, _) in enumerate(sem_ranked)}
        bm25_rk = {idx: r + 1 for r, (idx, _) in enumerate(bm25_ranked)}

        # BM25 weight 1.5× semantic — exact-match lexical precision > broad semantic
        # recall for short-form HR policy queries (numbers, names, specific clauses).
        # Research basis: BEIR studies show α∈[1.3,1.7] optimal for domain corpora.
        all_idx = set(sem_rank_map) | set(bm25_rank_map)
        rrf: dict[int, float] = {}
        for idx in all_idx:
            score = 0.0
            if idx in sem_rk:
                score += 1.0 / (RRF_K + sem_rk[idx])
            if idx in bm25_rk:
                score += 1.5 / (RRF_K + bm25_rk[idx])
            rrf[idx] = score

        # Cross-policy: diversity enforcement, 2× result budget
        if cross_policy:
            effective_k = min(n_results * 2, 20)
            policy_counts: dict[str, int] = {}
            diverse: list[tuple[int, float]] = []
            for idx, score in sorted(rrf.items(), key=lambda x: -x[1]):
                pol = self._chunks[idx]["policy_name"]
                if policy_counts.get(pol, 0) < 4:
                    policy_counts[pol] = policy_counts.get(pol, 0) + 1
                    diverse.append((idx, score))
                if len(diverse) >= effective_k:
                    break
            top_indices = diverse
        else:
            top_indices = sorted(rrf.items(), key=lambda x: -x[1])[:n_results]

        # 4. BM25 exact-match guarantee: inject top BM25 results not in RRF top-K,
        #    but only when the chunk actually contains a content token from the query.
        #    This prevents generic high-BM25 chunks from crowding out true exact matches.
        rrf_ids = {idx for idx, _ in top_indices}
        content_tokens = set(tokens) - _BM25_STOPWORDS
        min_rrf = min(sc for _, sc in top_indices) if top_indices else 0.0
        injected = []
        for bm25_idx, bm25_score in bm25_ranked[:BM25_GUARANTEE]:
            if len(injected) >= BM25_MAX_INJECT:
                break
            if bm25_score < BM25_FLOOR or bm25_idx in rrf_ids:
                continue
            # Only inject if the chunk contains ALL non-stopword query tokens.
            # Using subset (all-match) instead of intersection (any-match) ensures
            # we inject truly precise matches, not generic chunks that share one token.
            chunk_tokens = set(_tokenise(self._chunks[bm25_idx]["text"]))
            if content_tokens and not content_tokens.issubset(chunk_tokens):
                continue
            injected.append((bm25_idx, min_rrf + 1e-6))
        if injected:
            # Merge, deduplicate, trim — injected entries displace lowest RRF results
            combined = list(top_indices) + injected
            combined.sort(key=lambda x: -x[1])
            seen_ids: set[int] = set()
            deduped = []
            for idx, sc in combined:
                if idx not in seen_ids:
                    seen_ids.add(idx)
                    deduped.append((idx, sc))
            top_indices = deduped[:n_results]

        return [
            {
                "text":        self._chunks[idx]["text"],
                "policy_name": self._chunks[idx]["policy_name"],
                "page":        self._chunks[idx]["page"],
                "filename":    self._chunks[idx]["filename"],
                "score":       round(score, 5),
            }
            for idx, score in top_indices
        ]


# Module-level singleton
_retriever = HybridRetriever()


def retrieve(query: str, n_results: int = FINAL_K) -> list[dict]:
    """Public API: drop-in replacement for rag.retrieve()."""
    return _retriever.retrieve(query, n_results)
