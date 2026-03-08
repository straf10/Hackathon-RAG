# Hackathon Thessaloniki 2026 - Challenge 2 Strategy
## Project: Financial Data Knowledge Base (RAG)

Αυτό το έγγραφο περιγράφει το πλάνο υλοποίησης βάσει των κανόνων του Hackathon PDF.

### 1. Dockerization Strategy (Υποχρεωτικό)
Σύμφωνα με τη σελίδα 4 και 7, η εφαρμογή **πρέπει** να τρέχει σε Linux environment μέσα σε Docker container. Αν δεν γίνεται compile/run με docker, η συμμετοχή ακυρώνεται.

**Προτεινόμενη Δομή:**
Επειδή θα χρειαστείτε Backend (RAG logic) και Database (Vector DB), η χρήση του `docker-compose` είναι η βέλτιστη λύση.

*   **Dockerfile (για το App):**
    *   Base Image: `python:3.10-slim` (ή παρόμοιο Linux image).
    *   Εγκατάσταση dependencies (`requirements.txt`).
    *   Copy του κώδικα.
    *   Command για εκκίνηση του server (π.χ. FastAPI/Streamlit).
*   **docker-compose.yml:**
    *   **Service 1 (App):** Το δικό σας container.
    *   **Service 2 (Vector DB):** Π.χ. `chromadb` ή `weaviate` (ΠΡΟΣΟΧΗ: Η σελίδα 4 τονίζει να χρησιμοποιείτε **μόνο official images** από το DockerHub).

### 2. Tech Stack (Βάσει σελίδας 17 & 13)
Για το Challenge 2 και συγκεκριμένα για Financial RAG, προτείνεται το παρακάτω stack που είναι συμβατό με τους κανόνες:

*   **Language:** Python (Προτείνεται έναντι του Node.js λόγω βιβλιοθηκών AI).
*   **Backend Framework:** FastAPI (γρήγορο, ασύγχρονο) ή Flask.
*   **Frontend / Visualization:**
    *   *Επιλογή A (Γρήγορη):* **Streamlit** (Αναφέρεται στη σελ. 13). Ιδανικό για να δείξετε dataframes και charts οικονομικών δεδομένων χωρίς πολύ frontend κώδικα.
    *   *Επιλογή B (Custom):* React (αν έχετε front-end dev στην ομάδα).
*   **AI Orchestration:** **LlamaIndex** (ιδανικό για "Search & Retrieval" που ζητάει το challenge) ή **LangChain**.
*   **Vector Database:** ChromaDB, FAISS ή Weaviate (τρέχουν εύκολα τοπικά με Docker).
*   **Embeddings:** OpenAI Embeddings (θα δοθούν keys) ή HuggingFace (δωρεάν/open source).

### 3. Επιλογές Dataset (Financial Domain)
Η σελίδα 4 αναφέρει: *"Use Officially provided public APIs or mock data that you’ve generated or curated."*

Για οικονομικά δεδομένα προτείνουμε:
1.  **Public APIs:**
    *   **Yahoo Finance (yfinance library):** Για ιστορικά δεδομένα μετοχών και νέα.
    *   **Alpha Vantage (Free tier):** Για market data.
    *   **EDGAR (SEC API):** Για επίσημα reports εταιρειών (10-K, 10-Q filings) -> **Ιδανικό για RAG** (μεγάλα κείμενα προς ανάλυση).
2.  **Mock Data / Curated:**
    *   Κατεβάστε 5-10 PDF ετήσιων απολογισμών (π.χ. Tesla, Apple, NVIDIA 2025 reports) και βάλτε τα σε έναν φάκελο `data/` μέσα στο repo. Αυτό θεωρείται "curated data".

### 4. Απαραίτητα Resources
*   **OpenAI API Keys:** Θα σας σταλούν στο email μετά το Kick-off (σελ. 7).
*   **GitHub Repository:** Πρέπει να ανεβάσετε τον κώδικα στο repo της Netcompany.
*   **Docker Desktop:** Για να τεστάρετε το containerization τοπικά.
*   **Hardware:** Laptop ικανό να τρέξει Docker (η βαριά επεξεργασία γίνεται στο API της OpenAI, οπότε δεν χρειάζεστε GPU τοπικά, εκτός αν τρέξετε local LLMs).

### 5. Βήματα Υλοποίησης (Roadmap)

**Φάση 1: Setup & Environment (Ημέρα 1)**
1.  Δημιουργία `git repo`.
2.  Στήσιμο `docker-compose.yml` με ένα 'hello world' python app και την Vector DB.
3.  Διασφάλιση ότι τρέχει με `docker-compose up`.

**Φάση 2: Data Ingestion & Indexing (Ο "Πυρήνας" του Challenge 2)**
1.  Συλλογή δεδομένων (π.χ. PDF financial reports ή News scraping).
2.  **Chunking:** Χωρισμός κειμένου σε κομμάτια.
3.  **Embedding:** Δημιουργία vector embeddings και αποθήκευση στη Vector DB.
4.  *Tip:* Η σελίδα 15 ζητάει *"Ingest and structure knowledge"*. Μην κάνετε απλά text dump. Προσπαθήστε να κρατήσετε metadata (π.χ. Ημερομηνία, Εταιρεία, Τύπος Εγγράφου).

**Φάση 3: RAG Implementation & Reasoning**
1.  Σύνδεση με OpenAI API.
2.  Υλοποίηση του Retrieval: Όταν ρωτάει ο χρήστης, βρες τα σχετικά chunks.
3.  **Advanced Logic (Σημαντικό για τη βαθμολογία - Σελ. 15):**
    *   Το σύστημα δεν πρέπει να είναι απλό chatbot.
    *   Πρέπει να κάνει **Reasoning**. Π.χ. *"Σύγκρινε τα έσοδα του 2024 με το 2025 βάσει των εγγράφων"*.
    *   *Bonus:* Structured Output (π.χ. επιστροφή αποτελέσματος σε JSON ή πίνακα).

**Φάση 4: User Interface & Feedback Loop**
1.  Φτιάξτε το UI (π.χ. Streamlit).
2.  **Requirement (Σελ. 15):** *"Learn from user interactions"*.
    *   Προσθέστε κουμπιά Like/Dislike στην απάντηση.
    *   Αποθηκεύστε το feedback (έστω σε ένα local JSON/SQLite) για να δείξετε ότι το σύστημα "μαθαίνει" τη σχετικότητα.

**Φάση 5: Documentation & Submission**
1.  Γράψτε το **README.md**:
    *   Concept Description (Financial Analyst Assistant).
    *   Setup / Run Instructions (απλά `docker-compose up`).
    *   Architecture Diagram (Mermaid.js ή εικόνα).
2.  Ετοιμάστε το Pitching (Video/Presentation) εξηγώντας γιατί η λύση σας δίνει Business Value (Σελ. 9 - 15% βαθμολογίας).