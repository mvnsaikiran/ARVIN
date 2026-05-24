import type { PolicyRouterChunk } from '../data/policyRouterChunks';
import { embedText } from './geminiService';

let dynamicChunks: PolicyRouterChunk[] = [];

export function buildPolicyIdFromFileName(fileName: string) {
  return fileName
    .replace(/\.[^/.]+$/, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function buildUploadedPolicyUrl(fileName: string) {
  return `/uploaded-policies/${encodeURIComponent(fileName)}`;
}

export function getDynamicChunks(): PolicyRouterChunk[] {
  return dynamicChunks;
}

async function extractDocxPages(filePath: string): Promise<Array<{ page_number: number; text: string }>> {
  const { spawnSync } = await import('child_process');
  const script = `
import json
import sys
from docx import Document

path = sys.argv[1]
doc = Document(path)
pages = []
current_page = []
page_num = 1

for para in doc.paragraphs:
    text = para.text.strip()
    if text:
        current_page.append(text)
    if any(getattr(run, "contains_page_break", False) for run in para.runs):
        if current_page:
            pages.append({"page_number": page_num, "text": "\\n".join(current_page)})
            current_page = []
            page_num += 1

for table in doc.tables:
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        rows.append(" | ".join(cells))
    if rows:
        current_page.append("\\n".join(rows))

if current_page:
    pages.append({"page_number": page_num, "text": "\\n\\n".join(current_page)})

print(json.dumps(pages))
`;

  const result = spawnSync("python", ["-c", script, filePath], {
    encoding: "utf-8",
    windowsHide: true,
  });

  if (result.status !== 0) {
    throw new Error(result.stderr?.trim() || "DOCX extraction failed.");
  }

  const parsed = JSON.parse(result.stdout || "[]");
  return Array.isArray(parsed) ? parsed : [];
}

// Reuse the normalisation maps from productionRagService to auto-tag metadata
const GRADE_ALIASES: Record<string, string[]> = {
  bmh9: ["bmh9", "bm-h9", "bmh 9"],
  bmh8: ["bmh8", "bm-h8", "bmh 8"],
  bmh7: ["bmh7", "bm-h7", "bmh 7"],
  bmh6: ["bmh6", "bm-h6", "bmh 6"],
  bmh5: ["bmh5", "bm-h5", "bmh 5"],
  bmh4: ["bmh4", "bm-h4", "bmh 4"],
  bmh3: ["bmh3", "bm-h3", "bmh 3"],
  m3h1: ["m3h1", "m3-h1", "m3 h1"],
  m3:   ["m3"],
  m2:   ["m2"],
  m1:   ["m1"],
  mt:   ["mt"],
  e2:   ["e2"],
  get:  ["get"],
  e1:   ["e1"],
  ot:   ["ot"],
};

const CITY_CLASS_MAP: Record<string, string> = {
  mumbai: "class i", delhi: "class i", bangalore: "class i",
  chennai: "class i", hyderabad: "class i", kolkata: "class i",
  pune: "class i", ahmedabad: "class i",
  surat: "class ii", jaipur: "class ii", lucknow: "class ii",
  nagpur: "class ii", bhopal: "class ii", patna: "class ii",
  ranchi: "class ii", indore: "class ii",
};

/**
 * Extracts all matching grades and city classes from the text to populate metadata tags.
 */
function extractMetadataTags(text: string) {
  const normalized = text.toLowerCase();
  const grades = new Set<string>();
  const cities = new Set<string>();

  for (const [grade, aliases] of Object.entries(GRADE_ALIASES)) {
    if (aliases.some(a => normalized.includes(a))) {
      grades.add(grade);
    }
  }

  for (const [city, cls] of Object.entries(CITY_CLASS_MAP)) {
    if (normalized.includes(city)) {
      cities.add(cls);
    }
  }
  if (/class\s*i(?!i)/.test(normalized)) cities.add("class i");
  if (/class\s*ii(?!i)/.test(normalized)) cities.add("class ii");
  if (/class\s*iii/.test(normalized)) cities.add("class iii");

  return { gradeTags: Array.from(grades), cityClasses: Array.from(cities) };
}

/**
 * Basic structural chunking based on double newlines and header patterns.
 */
function createChunksFromText(text: string, fileName: string, startId: number, pageNum = 1): PolicyRouterChunk[] {
  // Normalize spacing slightly
  const cleaned = text.replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n');
  const paragraphs = cleaned.split('\n\n').filter(p => p.trim().length > 20);
  
  const chunks: PolicyRouterChunk[] = [];
  let currentId = startId;
  let currentSection = "GENERAL";

  for (const para of paragraphs) {
    // If paragraph looks like a header (all caps, or starts with #)
    if (/^[A-Z0-9\s_&-]+$/.test(para.trim().split('\n')[0]) || para.trim().startsWith('#')) {
      currentSection = para.trim().split('\n')[0].replace(/#/g, '').trim();
    }

    // Attempt simple table detection (lines with multiple spaces separating items)
    let formattedText = para;
    if (para.includes('  ') && para.split('\n').length > 1) {
      formattedText = para.split('\n').map(line => {
        const parts = line.split(/\s{2,}/).filter(Boolean);
        return parts.length > 1 ? `| ${parts.join(' | ')} |` : line;
      }).join('\n');
    }

    const { gradeTags, cityClasses } = extractMetadataTags(formattedText);

    // Build the chunk
    chunks.push({
      id: currentId++,
      policyId: buildPolicyIdFromFileName(fileName),
      policyName: fileName.replace(/\.[^/.]+$/, ""),
      fileUrl: buildUploadedPolicyUrl(fileName),
      sourceDocumentName: fileName,
      pageNum,
      section: currentSection,
      chunkType: formattedText.includes('|') ? 'table' : 'context',
      text: formattedText,
      keywords: [], // Populated later if needed
      // @ts-ignore - The underlying array needs these even if the TS type doesn't have them in PolicyRouterChunk
      gradeTags,
      cityClasses,
    });
  }

  return chunks;
}

export async function ingestPolicies(policiesDir: string): Promise<number> {
  if (typeof window !== 'undefined') {
    return dynamicChunks.length;
  }

  const fs = await import('fs');
  const path = await import('path');
  // @ts-ignore
  const pdfjsLib = await import('pdfjs-dist/legacy/build/pdf.mjs');

  if (!fs.existsSync(policiesDir)) {
    return 0;
  }

  const files = fs.readdirSync(policiesDir);
  const newChunks: PolicyRouterChunk[] = [];
  let chunkIdCounter = 50000; // Start high to avoid collisions with static chunks

  for (const file of files) {
    if (file.startsWith('.')) continue; // skip hidden files

    const filePath = path.join(policiesDir, file);
    const ext = path.extname(file).toLowerCase();
    
    try {
      if (ext === '.txt' || ext === '.md') {
        const textContent = fs.readFileSync(filePath, 'utf-8');
        const chunks = createChunksFromText(textContent, file, chunkIdCounter);
        newChunks.push(...chunks);
        chunkIdCounter += chunks.length;
      } else if (ext === '.pdf') {
        const data = new Uint8Array(fs.readFileSync(filePath));
        const pdf = await pdfjsLib.getDocument({ data }).promise;
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const textContentPage = await page.getTextContent();
          
          // Basic heuristic to reconstruct paragraphs from PDF text items
          let pageText = '';
          let lastY = -1;
          for (const item of textContentPage.items as any[]) {
            if (lastY !== -1 && Math.abs(item.transform[5] - lastY) > 12) {
              pageText += '\n';
            }
            if (lastY !== -1 && Math.abs(item.transform[5] - lastY) > 24) {
              pageText += '\n'; // Double newline for larger gaps
            }
            pageText += item.str + ' ';
            lastY = item.transform[5];
          }
          
          const chunks = createChunksFromText(pageText, file, chunkIdCounter, i);
          newChunks.push(...chunks);
          chunkIdCounter += chunks.length;
        }
      } else if (ext === '.docx' || ext === '.doc') {
        const pages = await extractDocxPages(filePath);
        for (const page of pages) {
          const chunks = createChunksFromText(page.text, file, chunkIdCounter, page.page_number);
          newChunks.push(...chunks);
          chunkIdCounter += chunks.length;
        }
      }
    } catch (e) {
      console.error(`Failed to ingest policy file ${file}:`, e);
    }
  }

  // Generate vector embeddings for the newly ingested chunks
  for (const chunk of newChunks) {
    chunk.embedding = await embedText(chunk.text);
  }

  dynamicChunks = newChunks;
  return dynamicChunks.length;
}
