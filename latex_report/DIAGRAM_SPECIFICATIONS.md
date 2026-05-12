# DocInsight Chapter 3: Diagram Specifications for Draw.io

## Overview
All diagrams should use a professional color scheme:
- **Primary Blue**: #1E3A8A
- **Secondary Blue**: #3B82F6
- **Light Blue**: #DBEAFE
- **Gray**: #6B7280
- **Success Green**: #10B981
- **Process Fill**: #F3F4F6
- **Text**: #1F2937

---

## Diagram 1: Three-Tier System Architecture
**File Reference**: Plan of Work, Section: System Architecture  
**Figure Label**: Fig 1.1 - Three-Tier System Architecture of DocInsight  
**Canvas Size**: 1000 × 800 px

### Layout Structure (Left to Right):
```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: PRESENTATION LAYER (Left Third)                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ React 18 + Vite (Port 5173)                                 ││
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        ││
│  │ │ Upload   │ │ Chat     │ │Document  │ │Session   │        ││
│  │ │ Zone     │ │Interface │ │List      │ │Manager   │        ││
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘        ││
│  │ ┌──────────┐ ┌──────────┐                                   ││
│  │ │ PDF      │ │Confidence│                                   ││
│  │ │ Viewer   │ │Indicator │                                   ││
│  │ └──────────┘ └──────────┘                                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                    ↓ REST/SSE (Port proxy)                       │
├─────────────────────────────────────────────────────────────────┤
│  TIER 2: APPLICATION LAYER (Middle Third)                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ FastAPI + Uvicorn (Port 8000)                               ││
│  │  ROUTERS              │   SERVICES                          ││
│  │  ┌──────────────────┐ │  ┌──────────────────────────────┐  ││
│  │  │ • upload.py      │ │  │ rag_chain.py               │  ││
│  │  │ • chat.py        │ │  │ vector_store.py            │  ││
│  │  │ • documents.py   │ │  │ llm.py                     │  ││
│  │  │ • sessions.py    │ │  │ document_loader.py         │  ││
│  │  │ • advanced.py    │ │  │ chat_store.py              │  ││
│  │  │                  │ │  │ document_store.py          │  ││
│  │  │                  │ │  │ hybrid_search.py           │  ││
│  │  │                  │ │  │ pdf_exporter.py            │  ││
│  │  └──────────────────┘ │  └──────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
│         ↓ Filesystem I/O & HTTPS        ↓ REST/SSE              │
├─────────────────────────────────────────────────────────────────┤
│  TIER 3: DATA PERSISTENCE LAYER (Right Third)                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ LocalFileSystem (backend/)                                  ││
│  │ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────┐││
│  │ │ ChromaDB         │ │ File Store       │ │ Session Store ││
│  │ │ (chroma_db/)     │ │ (uploads/)       │ │(chat_sessions/││
│  │ │                  │ │                  │ │               ││
│  │ │ • Embeddings     │ │ • PDF/DOCX/TXT   │ │ • JSON         ││
│  │ │ • Vectors        │ │ • Metadata       │ │  Messages     ││
│  │ │ • HNSW Index     │ │ • Retention      │ │ • Chat        ││
│  │ │                  │ │                  │ │  History      ││
│  │ └──────────────────┘ └──────────────────┘ └───────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│                 External: Groq API (HTTPS) ──→ LLaMA 3.3 70B   │
└─────────────────────────────────────────────────────────────────┘
```

### Draw.io Specifications:

**Component Boxes** (Use Rectangle Shape):
- **Tier 1 (Presentation) - Light Blue Background**
  - Main container: 920 × 180 px, Top-left (40, 40)
  - Title: "Tier 1 — Presentation Layer: React 18 + Vite (Port 5173)" | Font: 11pt Bold
  - Component sub-boxes (each 80 × 40 px):
    - UploadZone (70, 70)
    - ChatInterface (170, 70)
    - DocumentList (270, 70)
    - SessionManager (370, 70)
    - PDFViewerPanel (70, 130)
    - ConfidenceIndicator (170, 130)

- **Tier 2 (Application) - Primary Blue Background**
  - Main container: 920 × 140 px, at (40, 240)
  - Title: "Tier 2 — Application Layer: FastAPI + Uvicorn (Port 8000)" | Font: 11pt Bold
  - Left section "ROUTERS" (80 × 120 px at 70, 270):
    - List items: upload.py, chat.py, documents.py, sessions.py, advanced.py | Font: 9pt
  - Right section "SERVICES" (800 × 120 px at 180, 270):
    - Two rows of service modules, 6pt font, grid layout

- **Tier 3 (Data) - Secondary Blue Background**
  - Main container: 920 × 140 px, at (40, 400)
  - Title: "Tier 3 — Data Persistence Layer: ChromaDB + File Storage" | Font: 11pt Bold
  - Three subsystem boxes (each ~280 × 110 px):
    - ChromaDB (70, 430): Embeddings, Vectors, HNSW Index
    - File Store (370, 430): PDF/DOCX/TXT, Metadata, Retention
    - Session Store (670, 430): JSON Messages, Chat History

**Arrows/Connectors**:
- Tier 1 → Tier 2: Straight arrow, labeled "REST/SSE (Port proxy)" | Font: 9pt
- Tier 2 → Tier 3: Straight arrow, labeled "Filesystem I/O & HTTPS" | Font: 9pt
- External: Groq API arrow from Tier 2, labeled "HTTPS" pointing to "LLaMA 3.3 70B"

**Styling**:
- Borders: 2px, Tier colors
- Text alignment: Center
- Font family: Helvetica

---

## Diagram 2: Level 0 DFD - Context Diagram
**File Reference**: Data Flow Design, Level 0  
**Figure Label**: Fig 2.1 - Level 0 DFD — System Context Diagram  
**Canvas Size**: 900 × 700 px

### Layout:
```
                              ┌─────────────────┐
                              │  External LLM   │
                              │   Provider      │
                              │   (Groq/Ollama) │
                              └────────┬────────┘
                                       │
                   Prompt + Context    │    Generated Answer
                   ──────────────────→ │ ←──────────────────
                                       │
                       ┌───────────────────────────────┐
                       │      DOCINSIGHT             │
                       │   (Single Process)          │
    User ─────────────→│                             │←─────────── User
    (Queries/Docs)     │  RAG Pipeline               │   (Answers/
                       │                             │    Citations/
                       │                             │    Confidence)
                       └───────────────────────────────┘
                               │
                               ↓
                    ┌──────────────────────┐
                    │  Local File System   │
                    │  • Documents        │
                    │  • Embeddings       │
                    │  • Sessions         │
                    └──────────────────────┘
```

### Draw.io Specifications:

**External Entities** (Oval/Circle Shapes):
- User (Left): Circle 60 × 60 px at (50, 300) | Font: 11pt Bold | Fill: #E8F4F8
- Groq API (Top): Circle 60 × 60 px at (400, 50) | Font: 10pt Bold | Fill: #F3E8FF
- File System (Bottom): Rectangle 120 × 60 px at (350, 600) | Font: 11pt Bold | Fill: #FEF3C7

**Central Process**:
- Main bubble: Circle 100 × 100 px, centered at (400, 320) | Fill: #3B82F6 | Text: "DocInsight" (White, 14pt Bold)
- Label below: "Single System Process" | Font: 9pt Italic

**Data Flows** (Arrows with Labels):
- User → DocInsight: Arrow (100, 330) → (300, 330)
  - Label: "Document Files + Natural Language Queries" (9pt, positioned above)
- DocInsight → User: Arrow (300, 350) → (100, 350)
  - Label: "Answers + Sources + Confidence + History" (9pt, positioned below)
- DocInsight ↔ Groq: Bidirectional arrows
  - Down arrow label: "Constructed Prompt + Context" (9pt)
  - Up arrow label: "Generated Answer Tokens (Streaming)" (9pt)
- DocInsight ↔ File System: Bidirectional arrows
  - Label: "Documents, Embeddings, Session JSON" (9pt)

**Styling**:
- Arrow style: Solid, 2px
- Text boxes: No fill, 9pt font
- Process circle: 3px border, #1E3A8A

---

## Diagram 3: Level 1 DFD - Major Process Decomposition
**File Reference**: Data Flow Design, Level 1  
**Figure Label**: Fig 3.1 - Level 1 DFD — Major System Processes  
**Canvas Size**: 1200 × 600 px

### Layout (Two Separate Paths):

**Upload/Ingestion Path (Top Row):**
```
User ──→ [P1]      [P2]      [P3]      [P4]      ──→ [D1]
       Document  Chunking  Embedding  Storage     ChromaDB
       Processing
```

**Query/Response Path (Bottom Row):**
```
User ──→ [P5]      [P6]      [P7]      [P8]      ──→ User
       Query      Retrieval Answer    Response
       Processing             Generation Formatting
       
[D1] ChromaDB ──→ [P6] (reads for retrieval)
[D2] Chat Sessions ↔ [P5] & [P8]
```

### Draw.io Specifications:

**Processes** (Rectangle Shapes - 100 × 70 px each):
- **Ingestion Path** (Y = 80):
  - P1 Document Processing: (50, 80) | Fill: #DBEAFE
  - P2 Text Chunking: (200, 80) | Fill: #DBEAFE
  - P3 Embedding Generation: (350, 80) | Fill: #DBEAFE
  - P4 Vector Storage: (500, 80) | Fill: #DBEAFE

- **Query Path** (Y = 280):
  - P5 Query Processing: (50, 280) | Fill: #D1FAE5
  - P6 Semantic Retrieval: (200, 280) | Fill: #D1FAE5
  - P7 Answer Generation: (350, 280) | Fill: #D1FAE5
  - P8 Response Formatting: (500, 280) | Fill: #D1FAE5

**Data Stores** (Parallel Lines - 2 horizontal lines 80 × 8 px):
- D1 ChromaDB: (700, 85) | Label: "ChromaDB Vector Store" (below, 9pt)
- D2 Chat Sessions: (700, 285) | Label: "Chat Sessions Store" (below, 9pt)

**External Entities** (Ovals):
- User (Input): (0, 165) | Circle 50 × 50 px
- User (Output): (1150, 165) | Circle 50 × 50 px

**Data Flows** (Arrows with Labels):
- P1 → P2: Straight arrow (150, 115) | Label: "Extracted Text" (9pt)
- P2 → P3: Straight arrow (300, 115) | Label: "Chunks" (9pt)
- P3 → P4: Straight arrow (450, 115) | Label: "Vectors" (9pt)
- P4 → D1: Straight arrow (600, 120) | Label: "Store" (9pt)

- User → P5: Arrow (50, 165) | Label: "Query" (9pt)
- P5 → P6: Straight arrow (150, 315) | Label: "Reformulated Query" (9pt)
- P6 → P7: Straight arrow (300, 315) | Label: "Retrieved Chunks" (9pt)
- P7 → P8: Straight arrow (450, 315) | Label: "Generated Answer" (9pt)
- P8 → User: Arrow (600, 165) | Label: "Response" (9pt)

- D1 → P6: Arrow (700, 150) → (300, 280) | Label: "Read" (9pt)
- D2 ↔ P5: Bidirectional arrows | Label: "Read/Write" (9pt)
- P8 → D2: Arrow (500, 300) → (700, 310) | Label: "Persist" (9pt)

**Title Box** (Top):
- Text: "Level 1 DFD: Document Ingestion Path (Top) and Query Response Path (Bottom)"
- Position: (50, 20) | Font: 12pt Bold

**Styling**:
- Process boxes: 2px border, respective color fill
- Data stores: 1px gray border
- Arrows: Solid 2px, #1E3A8A
- Text: 9pt Helvetica, centered within/near elements

---

## Diagram 4: Level 2 DFD - RAG Inference Chain Details
**File Reference**: Data Flow Design, Level 2  
**Figure Label**: Fig 4.1 - Level 2 DFD — Detailed RAG Inference Sub-Processes  
**Canvas Size**: 1400 × 700 px

### Hierarchical Expansion (P4 → P8 Sub-processes):

```
P4 (Query Processing):
  ├─→ P4.1: Load Chat History (D2)
  ├─→ P4.2: Question Reformulation (LLM)
  └─→ P4.3: Query Embedding

P5 (Semantic Retrieval):
  ├─→ P5.1: Similarity Search (HNSW)
  ├─→ P5.2: Score-based Ranking
  ├─→ P5.3: Document Filtering
  └─→ P5.4: Top-K Selection (k=3)

P6 (Context Assembly):
  ├─→ P6.1: Chunk Deduplication
  ├─→ P6.2: Content Truncation (500 chars)
  ├─→ P6.3: Source Annotation
  └─→ P6.4: Prompt Construction

P7 (Answer Generation):
  ├─→ P7.1: LLM Inference (Groq)
  ├─→ P7.2: Token Processing (SSE)
  ├─→ P7.3: Confidence Scoring
  └─→ P7.4: Follow-up Generation

P8 (Response Delivery):
  ├─→ P8.1: Source Re-ranking
  ├─→ P8.2: Suggestion Generation
  ├─→ P8.3: Response Construction
  └─→ P8.4: Session Persistence
```

### Draw.io Specifications:

**Column Layout** (5 Columns):
- Column 1 (X=50): P4 sub-processes
- Column 2 (X=300): P5 sub-processes
- Column 3 (X=550): P6 sub-processes
- Column 4 (X=800): P7 sub-processes
- Column 5 (X=1050): P8 sub-processes

**Sub-process Boxes** (70 × 50 px each):
- Rows: Vertically spaced 100 px apart, starting Y=80
- Fill: Light gradient blue (#E0F2FE)
- Border: 1.5px #0284C7
- Font: 8pt, centered

**Parent Process Labels** (Top of each column):
- Y = 30, Font: 11pt Bold, Color: #1E3A8A
- Text: "P4: Query\nProcessing", "P5: Semantic\nRetrieval", etc.

**Vertical Flow Arrows**:
- Connect sub-processes within each column
- Arrow style: Thin (1px), #3B82F6
- Labels: Minimal (if any)

**Data Store References** (On left/right):
- D1 (ChromaDB): Right side at (1300, 250) | 2-line symbol
  - Arrow from P5 sub-processes
- D2 (Chat Sessions): Left side at (0, 200) | 2-line symbol
  - Bidirectional arrows with P4 and P8

**Horizontal Flow** (Bottom of diagram):
- Major flow arrow: P4 → P5 → P6 → P7 → P8 (Y=600)
- Arrow style: 2px solid, labeled with intermediate data
- Labels: "Query" → "Retrieved Chunks" → "Prompt" → "Answer" → "Response"

**Key Measurements**:
- Sub-process box width: 70 px
- Column spacing: 250 px
- Row spacing: 100 px
- Data store symbols: 40 × 60 px

---

## Diagram 5: End-to-End Pipeline Flow
**File Reference**: End-to-End Processing Pipeline  
**Figure Label**: Fig 5.1 - End-to-End DocInsight Processing Pipeline  
**Canvas Size**: 1100 × 500 px

### Two-Path Layout:

**Top Path (Ingestion - Green):**
```
Upload → Extract → Chunk → Embed → Store
  ↓        ↓        ↓       ↓       ↓
 S1       S2       S3      S4      S5
```

**Bottom Path (Query - Blue):**
```
Query → Reformulate → Retrieve → Assemble → Generate → Format
  ↓        ↓            ↓         ↓          ↓         ↓
 S6       S6           S6        S7        S7        S8
```

**Central Hub:**
```
           ChromaDB (Vector Store)
                ▲    │
                │    ↓
            (S5)    (S6)
```

### Draw.io Specifications:

**Stage Boxes** (Each 90 × 60 px):

**Ingestion Path (Top Row - Y = 50):**
- S1 Upload: (50, 50) | Fill: #D1FAE5 | Icon: ⬆
- S2 Extract: (180, 50) | Fill: #D1FAE5 | Icon: 📄
- S3 Chunk: (310, 50) | Fill: #D1FAE5 | Icon: ✂
- S4 Embed: (440, 50) | Fill: #D1FAE5 | Icon: 🔢
- S5 Store: (570, 50) | Fill: #D1FAE5 | Icon: 💾

**Query/Response Path (Bottom Row - Y = 250):**
- S6 Query: (50, 250) | Fill: #DBEAFE | Icon: ❓
- S6b Reformulate: (180, 250) | Fill: #DBEAFE | Icon: ✏
- S6c Retrieve: (310, 250) | Fill: #DBEAFE | Icon: 🔍
- S7 Assemble: (440, 250) | Fill: #DBEAFE | Icon: 📋
- S7b Generate: (570, 250) | Fill: #DBEAFE | Icon: 💬
- S8 Format: (700, 250) | Fill: #DBEAFE | Icon: 📤

**Central ChromaDB Hub** (120 × 80 px):
- Position: (570, 140)
- Shape: Rounded rectangle
- Fill: #F3E8FF
- Border: 2px, #6D28D9
- Label: "ChromaDB\nVector\nStore" (11pt Bold, centered)

**Flow Arrows**:
- **Horizontal (Stage to Stage)**:
  - S1 → S2 → S3 → S4 → S5: Arrows Y=80, 2px #10B981
  - S6 → S6b → S6c → S7 → S7b → S8: Arrows Y=280, 2px #3B82F6
  
- **Vertical (to/from ChromaDB)**:
  - S5 ↓ to ChromaDB: Arrow (615, 110) → (615, 140) | Label: "Write Vectors" (8pt, right-aligned)
  - ChromaDB ↓ to S6c: Arrow (615, 220) → (355, 250) | Label: "Read Vectors" (8pt, left-aligned)

**Stage Labels** (Below boxes):
- Font: 9pt, centered below each stage
- Text: "Stage 1: Upload", "Stage 2: Extract", etc.

**Legend Box** (Top-right):
- Position: (850, 50)
- Size: 200 × 150 px
- Fill: #F9FAFB
- Border: 1px #D1D5DB
- Content:
  ```
  ▓ Ingestion Path (Stages 1-5)
  ░ Query/Response Path (Stages 6-8)
  ◇ Central Vector Store Hub
  
  Flow Direction: Left to Right
  ```

**Title Box** (Top-left):
- Position: (50, 20)
- Text: "Horizontal Two-Path Pipeline Architecture"
- Font: 12pt Bold

---

## Diagram 6: Gantt Chart - 16-Week Implementation Timeline
**File Reference**: Implementation Timeline  
**Figure Label**: Fig 6.1 - Project Implementation Schedule — Gantt Chart  
**Canvas Size**: 1300 × 500 px

### Timeline Structure:

```
Week:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
      Jan7-21         Jan22-Mar4      Mar5-Apr1   Apr2-May7
      └─Phase1─┘      └────Phase 2────┘ └─Phase3─┘ └─Phase 4─┘
```

### Draw.io Specifications:

**Grid Setup**:
- Columns: 16 weeks (each ~75 px wide)
- Rows: 5 activities + Phase headers

**Header Row** (Y = 20):
- Title: "DocInsight Project Timeline — 16 Weeks (January 7 — May 7, 2026)"
- Font: 12pt Bold, #1F2937

**Week Column Headers** (Y = 50):
- Labels: "W1 (Jan7-21)", "W2", "W3", ... "W16 (Apr2-May7)"
- Font: 8pt, centered
- Vertical lines: Thin dividers at each week boundary

**Phase Rows with Bars**:

**Phase 1: Requirements Analysis (W1-2)** [Y = 100]
- Bar: (50, 100) to (200, 130) | Fill: #3B82F6 | Border: 1px #1E3A8A
- Label: "Phase 1: Requirements Analysis"
- Activities (indented):
  - Lit Review | (60, 120) | Tiny bar
  - Tech Selection | (100, 120) | Tiny bar
  - Environment Setup | (140, 120) | Tiny bar
  - Repo Init | (180, 120) | Tiny bar

**Phase 2: Backend & RAG (W3-8)** [Y = 160]
- Bar: (200, 160) to (700, 190) | Fill: #10B981 | Border: 1px #047857
- Label: "Phase 2: Backend & RAG Pipeline Implementation"
- Activities:
  - Router Impl | (210, 180)
  - Service Layer | (280, 180)
  - Ingestion Pipeline | (380, 180)
  - RAG Chain | (520, 180)
  - Session Mgmt | (630, 180)
  - Unit Testing | (680, 180)

**Phase 3: Frontend & Integration (W9-12)** [Y = 220]
- Bar: (700, 220) to (950, 250) | Fill: #F59E0B | Border: 1px #D97706
- Label: "Phase 3: Frontend Integration & System Assembly"
- Activities:
  - UI Components | (710, 240)
  - API Integration | (800, 240)
  - SSE Consumer | (880, 240)
  - Session UI | (920, 240)

**Phase 4: Optimization & Deployment (W13-16)** [Y = 280]
- Bar: (950, 280) to (1200, 310) | Fill: #EC4899 | Border: 1px #BE185D
- Label: "Phase 4: System Optimization & Deployment"
- Activities:
  - System Testing | (960, 300)
  - Perf Profiling | (1050, 300)
  - Optimization | (1130, 300)
  - Deployment Docs | (1190, 300)

**Milestone Markers** (Vertical Dashed Lines):
- Exit Criterion lines at end of each phase
- Y = 0 to 350
- Style: Dashed 2px, #9CA3AF
- Labels (above line): "Exit Criteria", Font: 7pt

**Legend Box** (Bottom-right) [Y = 400]:
- Position: (950, 400)
- Size: 250 × 80 px
- Content:
  ```
  ■ Phase 1  ■ Phase 2  ■ Phase 3  ■ Phase 4
  
  Duration: 16 weeks total
  Start: January 7, 2026
  End: May 7, 2026
  ```

**Critical Path Indicator**:
- Highlight Phase 2 with thicker border (2px)
- Note below: "Critical Path: Phase 2 (highest effort concentration)"

**Exit Criteria Labels** (Below chart):
- Y = 340
- W2: "Env Ready" | W8: "Core Features" | W12: "Full Integration" | W16: "Production Ready"
- Font: 8pt, #4B5563

---

## Implementation Notes for Draw.io

### General Styling Guidelines:
1. **Font Family**: Helvetica or Arial (sans-serif)
2. **Font Sizes**:
   - Main titles: 12pt Bold
   - Section labels: 11pt Bold
   - Component names: 9-10pt
   - Sub-items: 8-9pt
   - Annotations: 7-8pt

3. **Colors (Hex Codes)**:
   - Process boxes: #DBEAFE (light blue)
   - Data stores: #FEF3C7 (light yellow)
   - External entities: #E8F4F8 (pale blue)
   - Successful items: #D1FAE5 (light green)
   - Warnings: #FED7AA (light orange)
   - Flow arrows: #1E3A8A (dark blue)

4. **Spacing Rules**:
   - Box padding: 5-10 px internal
   - Gap between elements: 10-20 px
   - Arrow curve radius: 5 px (for better aesthetics)

5. **Export Settings** (when exporting from Draw.io):
   - Format: PNG (for LaTeX)
   - Resolution: 300 DPI
   - Background: White
   - Width/Height: As specified above (will scale to fit)

### File Organization:
- Create one Draw.io file per diagram OR
- Create single multi-page Draw.io file with tabs for each diagram

### LaTeX Integration:
```latex
\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{images/diagram-X-NAME.png}
\caption{Title}
\label{fig:diagram_X}
\end{figure}
```

Replace placeholder text boxes in plan_of_work.tex with `\includegraphics` commands pointing to exported PNG files in `images/` subdirectory.

---

## Quick Checklist for Draw.io Creation:
- [ ] Create new Draw.io file or open existing
- [ ] Set canvas size for each diagram as specified
- [ ] Place all components per coordinates
- [ ] Add connectors/arrows with labels
- [ ] Apply colors per style guide
- [ ] Add title and figure labels
- [ ] Verify alignment and spacing
- [ ] Export as PNG at 300 DPI
- [ ] Place in `latex_report/images/` folder
- [ ] Update LaTeX references in plan_of_work.tex
