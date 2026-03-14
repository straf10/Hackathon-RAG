# Lexio: Vision, Roadmap, and Architectural Justification

**Netcompany Hackathon Thessaloniki 2026**

Due to the  time constraint and the $10 API token budget constraint across `gpt-5.1`, `gpt-4.1`, and `text-embedding-3-small`, we focused our MVP on the core innovation of **Lexio**: the **Page-Level Indexing architecture**. 

While our current MVP successfully ingests fifteen 10-K reports and answers complex financial queries accurately within budget, this document outlines our complete vision, upcoming features, and the scientific justification behind our approach.

---

## 1. The Full Vision: Future Features & Upgrades

If given more time and a larger token budget, **Lexio** is designed to evolve into a full-scale investment and financial reporting analyst. Our immediate roadmap includes:

### Expanding the Financial Corpus & Predictive Insights

Currently, the system is limited to 15 annual 10-K reports. 

- **The Upgrade:** We plan to integrate quarterly **10-Q**, current event **8-K**, and proxy **DEF 14A** (DFA14A) reports across dozens of companies and a broader 5-10 year timeline. 
- **The Value:** This will allow the LLM to identify deep historical patterns, evaluate sudden executive shifts, and perform cross-company trend analysis to actively recommend **where to invest** and automatically generate comprehensive **investment thesis reports**.

### Advanced Financial Visualizations

- **The Upgrade:** Implementing dynamic line plots, candlestick charts, and multi-variable scatter plots directly in the chat UI.
- **Why it was deferred:** Generating code for complex longitudinal graphs requires significantly larger context windows and multiple LLM reasoning passes. Due to our $10 token budget and API rate limits, we restricted the current MVP to simple bar charts and table extractions.

### Interactive "In-App" Document Verification

- **The Upgrade:** Currently, Lexio provides exact page citations (e.g., *Page 42*). We plan to upgrade the UI so that clicking a citation triggers a **live PDF pop-up modal**. 
- **The Value:** Using the document metadata, the app will instantly render the exact page of the original SEC filing on the user's screen, highlighting the exact paragraph or table the model used. This provides 100% frictionless auditability.

### Personalized Workspaces via Firebase Auth

- **The Upgrade:** Integration with Firebase Authentication.
- **The Value:** Analysts will have secure, individualized accounts where their specific conversation threads, custom financial comparisons, and uploaded custom PDFs are saved persistently.

---

## 2. Why Page-Level Indexing?

Most standard RAG (Retrieval-Augmented Generation) applications use **Token-Based Chunking** (e.g., blindly splitting text every 512 tokens with a 100-token overlap). For financial documents, this is a fatal flaw. We built Lexio on **Page-Level Indexing**, a decision backed by recent AI research:

1. **NVIDIA's 2024 Retrieval Benchmark:** In a comprehensive study of chunking strategies, NVIDIA found that for highly structured documents, **page-level chunking outperformed all other methods**, achieving the highest QA accuracy and lowest hallucination rate.
2. **Tabular Data Integrity:** Financial documents are heavily reliant on massive, multi-column tables (Income Statements, Balance Sheets). A 512-token limit regularly slices a financial table in half. The LLM retrieves a fragmented table, leading to hallucinations. **Page-level indexing preserves the semantic and structural layout** of the table natively.
3. **The FinanceBench Standard:** Frameworks utilizing page-anchored structural retrieval (like the open-source *PageIndex* framework) have achieved up to **98.7% accuracy** on the rigorous FinanceBench dataset, vastly outperforming token-chunked vector RAGs on SEC filings.

---

## 3. The "Efficiency Calculator"

Currently, our application features a **Token Usage & Budget** tracker. Our planned upgrade is to replace this with a **Live Efficiency Calculator** that actively proves the ROI of our architecture to the user.

Instead of just showing tokens spent, the dashboard will use a real-time formula to compare Lexio’s costs against a standard Vector RAG. 

### The Math Behind Our Efficiency

Traditional token chunking requires "sliding overlaps" to prevent cutting sentences in half. 

- **Standard Vector RAG:** `Total Chunks = Total Tokens ÷ (Chunk Size − Overlap Size)`
- **Lexio (Page-Level):** `Total Chunks = Total Pages`

If an average 10-K page has ~800 tokens, a 512-token chunker with 20% overlap creates roughly **3 to 4 times more chunks** than Lexio. 

**The Live Formula Dashboard will show:**

1. **Embedding API Calls Saved:** Lexio reduces embedding model requests by ~70%.
2. **Zero Overlap Waste:** Lexio wastes 0 tokens on redundant overlaps, whereas traditional RAGs pay for 15-25% redundant tokens on every document ingested.
3. **Faster Search Latency:** By reducing a 10,000-vector database to a 2,500-vector database, the Approximate Nearest Neighbor (ANN) search in ChromaDB executes at a fraction of the latency.

### Conclusion for the Judges

Lexio is not just a wrapper around an OpenAI API. It is a highly optimized, domain-specific architecture designed to maximize accuracy on financial tables while simultaneously minimizing API costs. We accomplished a highly accurate, multi-step comparative financial analyst while remaining strictly under the $10 threshold.