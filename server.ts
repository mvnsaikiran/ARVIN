import express from "express";
import { createServer as createViteServer } from "vite";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { generateGeminiText, type GeminiGenerateRequest } from "./src/server/geminiProxy.js";
import { ingestPolicies } from "./src/services/policyIngestionService.js";
import multer from "multer";

const POLICIES_DIR = path.join(process.cwd(), "src", "policies");
const ORIGINAL_POLICIES_DIR = path.join(process.cwd(), "public", "original-policies");
const UPLOADED_POLICIES_DIR = path.join(process.cwd(), "public", "uploaded-policies");
const SUPPORTED_POLICY_EXTENSIONS = new Set([".pdf", ".doc", ".docx", ".txt", ".md"]);
const BACKEND_BASE_URL = "http://127.0.0.1:8001";

function sanitizeFileName(fileName: string) {
  return path.basename(fileName).trim();
}

function buildPolicyId(fileName: string) {
  return sanitizeFileName(fileName)
    .replace(/\.[^/.]+$/, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function buildUploadedPolicyUrl(fileName: string) {
  return `/uploaded-policies/${encodeURIComponent(sanitizeFileName(fileName))}`;
}

function ensureDirectoryExists(dirPath: string) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

function isSupportedPolicyFile(fileName: string) {
  return SUPPORTED_POLICY_EXTENSIONS.has(path.extname(fileName).toLowerCase());
}

async function mirrorPoliciesToPublic(policiesPath: string) {
  ensureDirectoryExists(UPLOADED_POLICIES_DIR);
  const files = fs.readdirSync(policiesPath).filter((file) => !file.startsWith("."));
  for (const file of files) {
    const sourcePath = path.join(policiesPath, file);
    const stats = fs.statSync(sourcePath);
    if (!stats.isFile()) continue;
    fs.copyFileSync(sourcePath, path.join(UPLOADED_POLICIES_DIR, file));
  }
}

async function triggerPythonIngestion() {
  try {
    await fetch(`${BACKEND_BASE_URL}/api/ingest`, { method: "POST" });
    return true;
  } catch (err) {
    console.warn("Could not trigger Python backend ingestion:", err);
    return false;
  }
}

async function synchronizePolicies() {
  ensureDirectoryExists(POLICIES_DIR);
  ensureDirectoryExists(UPLOADED_POLICIES_DIR);
  await mirrorPoliciesToPublic(POLICIES_DIR);
  const ingestedChunks = await ingestPolicies(POLICIES_DIR);
  const pythonSynchronized = await triggerPythonIngestion();
  return { ingestedChunks, pythonSynchronized };
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    ensureDirectoryExists(POLICIES_DIR);
    cb(null, POLICIES_DIR);
  },
  filename: (req, file, cb) => {
    cb(null, sanitizeFileName(file.originalname));
  }
});
const upload = multer({ storage });

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function readQueryValue(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

async function startServer() {
  const app = express();
  const PORT = parseInt(process.env.PORT || "3000", 10);

  app.use(express.json({ limit: "10mb" }));
  app.use("/original-policies", express.static(ORIGINAL_POLICIES_DIR));
  app.use("/uploaded-policies", express.static(UPLOADED_POLICIES_DIR));
  app.use("/api", (_req, res, next) => {
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Content-Type-Options", "nosniff");
    next();
  });

  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", version: "6.0-hybrid-lightrag-orchestrator" });
  });

  app.get("/api/search", async (req, res) => {
    try {
      const q = readQueryValue(req.query.q);
      if (!q) return res.json([]);
      if (q.length < 2) {
        return res.status(400).json({ error: "Query must be at least 2 characters." });
      }

      const { bm25Search } = await import("./src/data/policies.js");
      const results = bm25Search(q, 5);
      res.json(results.map((chunk) => ({
        id: chunk.id,
        policyId: chunk.policyId,
        policyName: chunk.policyName,
        pageNum: chunk.pageNum,
        snippet: chunk.text.slice(0, 400),
      })));
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.get("/api/policy/rules/search", async (req, res) => {
    try {
      const q = readQueryValue(req.query.q);
      if (!q) return res.json([]);
      if (q.length < 2) {
        return res.status(400).json({ error: "Query must be at least 2 characters." });
      }

      const { rankStructuredPolicyRules } = await import("./src/services/structuredRuleEngine.js");
      const results = rankStructuredPolicyRules(q, 5);
      res.json(results.map((entry) => ({
        id: entry.rule.id,
        policyId: entry.rule.policyId,
        policyName: entry.rule.policyName,
        section: entry.rule.section,
        clause: entry.rule.clause,
        ruleType: entry.rule.ruleType,
        page: entry.rule.page,
        score: entry.score,
        matchedCriteria: entry.matchedCriteria,
        answer: entry.rule.answer,
      })));
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.post("/api/gemini/generate", async (req, res) => {
    try {
      if (!req.body || !Array.isArray(req.body.contents) || req.body.contents.length === 0) {
        return res.status(400).json({ error: "Gemini request contents are required." });
      }

      const text = await generateGeminiText(req.body as GeminiGenerateRequest);
      res.json({ text });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : String(error),
      });
    }
  });

  app.post("/api/admin/ingest-policies", async (_req, res) => {
    try {
      const syncResult = await synchronizePolicies();
      res.json({ success: true, ...syncResult });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  async function handlePolicyUpload(req: express.Request, res: express.Response) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }

      const fileName = sanitizeFileName(req.file.originalname);
      if (!isSupportedPolicyFile(fileName)) {
        fs.unlinkSync(req.file.path);
        return res.status(400).json({ error: "Unsupported policy file type. Upload PDF, DOC, DOCX, TXT, or MD files." });
      }

      const syncResult = await synchronizePolicies();
      res.json({
        success: true,
        ...syncResult,
        fileName,
        fileUrl: buildUploadedPolicyUrl(fileName),
        policyId: buildPolicyId(fileName),
        sourceDocumentName: fileName,
      });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  }

  app.post("/api/policies/upload", upload.single("file"), handlePolicyUpload);
  app.post("/api/admin/upload-policy", upload.single("file"), handlePolicyUpload);

  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", async () => {
    console.log(`\nArvind HR Pulse v3.1 -> http://localhost:${PORT}`);
    console.log("   Retrieval: BM25 + structured policy rules");
    console.log(`   Gemini: ${process.env.GEMINI_API_KEY ? "configured" : "missing GEMINI_API_KEY"}`);
    
    // Auto-ingest policies on startup
    try {
      const syncResult = await synchronizePolicies();
      console.log(`   Policy Ingestion: ${syncResult.ingestedChunks} dynamic chunks loaded from src/policies/`);
      console.log(`   Python Backend Ingestion: ${syncResult.pythonSynchronized ? "Synchronized" : "Unreachable"}\n`);
    } catch (e) {
      console.error("   Policy Ingestion Failed:", e);
    }
  });
}

startServer().catch(console.error);
