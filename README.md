# 🤖 Autonomous AI Consultant

An enterprise-grade multi-agent AI consulting platform that transforms operational documents into strategic business insights, automation blueprints, ROI analysis, and executive consulting reports.

Built using LangGraph, FastAPI, Celery, Redis, ChromaDB, Gemini, Docker, and React, the platform demonstrates how autonomous AI agents can collaborate to solve real-world business consulting problems.

---

## 📌 Overview

Modern organizations often spend weeks analyzing operational workflows, identifying inefficiencies, and designing automation strategies.

This project demonstrates how a team of specialized AI agents can perform that workflow in minutes.

Instead of relying on a single prompt, the system decomposes the consulting process into multiple expert agents, each responsible for a specific domain of expertise.

The result is a structured consulting report comparable to an initial business process assessment performed by a technology consulting firm.

---

# 🚀 Features

### 📄 Multi-format Document Processing

- PDF Support
- DOCX Support
- TXT Support
- Automatic document parsing

---

### 🧠 Retrieval-Augmented Generation (RAG)

The uploaded documents are:

- Chunked
- Embedded
- Stored inside ChromaDB

This allows the consultant to retrieve only the most relevant business context before reasoning.

---

### 🤖 Multi-Agent Architecture

The platform consists of multiple specialized AI agents:

### Business Analyst

Responsible for:

- Understanding business operations
- Identifying bottlenecks
- Extracting current technology stack
- Detecting repetitive manual processes

---

### Solutions Architect

Responsible for:

- Designing automation strategies
- Recommending technologies
- Building implementation roadmaps
- Suggesting infrastructure

---

### ROI Analyst

Responsible for:

- Estimating implementation effort
- Predicting operational savings
- Estimating annual ROI
- Calculating payback period

---

### Executive Report Generator

Responsible for:

- Combining outputs from all agents
- Writing executive summaries
- Producing management-ready consulting reports

---

### AI Consultant Chat

After the report is generated, users can continue interacting with the consultant through natural language.

The consultant answers follow-up questions using:

- Generated consulting report
- Retrieved document context
- Previous consulting memory

---

# 🏗 System Architecture

```
                Upload Business Documents
                           │
                           ▼
                   Document Parser
                           │
                           ▼
                  ChromaDB Vector Store
                           │
                           ▼
                    LangGraph Workflow
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
 Business Analyst                     Context Retrieval
         │
         ▼
      Bridge Node
      ┌──────────┐
      ▼          ▼
 Architect    ROI Analyst
      │          │
      └────┬─────┘
           ▼
 Executive Report Generator
           │
           ▼
   Consulting Memory Storage
           │
           ▼
     Interactive AI Consultant
```

---

# ⚙ Tech Stack

## Backend

- Python
- FastAPI
- LangGraph
- Celery
- Redis
- ChromaDB

---

## AI

- Google Gemini
- Retrieval-Augmented Generation (RAG)
- Vector Embeddings

---

## Frontend

- React
- Vite
- Tailwind CSS

---

## Infrastructure

- Docker
- Docker Compose

---

# 📂 Project Structure

```
app/
│
├── advisor.py
├── consultant.py
├── consultant_memory.py
├── vector_store.py
├── nodes.py
├── state.py
├── prompts.py
├── schemas.py
├── celery_worker.py
└── main.py

frontend/

chroma_db/

storage/

docker-compose.yml
Dockerfile
```

---

# ⚡ Workflow

## 1. Upload

The user uploads:

- PDF
- DOCX
- TXT

---

## 2. Parsing

The backend extracts raw text.

---

## 3. Vectorization

The document is:

- Chunked
- Embedded
- Stored in ChromaDB

---

## 4. Multi-Agent Execution

LangGraph orchestrates multiple AI agents.

Planner

↓

Business Analyst

↓

Solutions Architect

↓

ROI Analyst

↓

Executive Report Generator

---

## 5. Report Generation

A consulting-style executive report is generated.

---

## 6. Persistent Memory

The report is stored as consulting memory.

---

## 7. AI Consultation

Users can continue asking business questions.

The consultant combines:

- Retrieved business context
- Executive report
- ROI analysis
- Previous consulting memory

to answer strategic questions.

---

# 📊 Example Use Cases

- Manufacturing Operations
- Logistics
- Healthcare Administration
- Retail Supply Chains
- Finance Operations
- HR Automation
- Customer Support
- Internal Enterprise Workflows

---

# 💡 Engineering Challenges Solved

During development the following engineering problems were addressed:

- Multi-agent orchestration
- Distributed task execution
- Asynchronous AI pipelines
- Long-running workflows
- Vector retrieval
- Dockerized deployment
- Persistent consulting memory
- Parallel agent execution
- API quota management
- Structured LLM outputs
- Workflow state management

---

# 📈 Future Improvements

- Deterministic ROI calculations
- Industry benchmarking
- Human approval workflow
- Multi-user authentication
- Cloud deployment
- Knowledge graph integration
- Live business KPI dashboards
- MCP Integration
- Streaming responses
- Multi-document consulting

---

# ▶ Running Locally

Clone the repository

```bash
git clone <repository-url>
cd Autonomous-AI-Consultant
```

Install dependencies

```bash
pip install -r requirements.txt
```

Start Docker

```bash
docker compose up --build
```

Frontend

```
http://localhost:3001
```

Backend

```
http://localhost:8000
```

---

# 📷 Demo

Coming Soon

- Full walkthrough
- Architecture explanation
- Live consulting example

---

# 🎯 Why This Project?

Most AI business tools rely on a single LLM prompt.

This project explores a different approach.

Instead of one model doing everything, a team of specialized AI agents collaborates to solve different aspects of a consulting engagement, closely mirroring how enterprise consulting teams operate.

The goal was not simply to generate text, but to design an extensible AI system capable of structured reasoning, orchestration, and business process analysis.

---

# 👨‍💻 Author

**Varad Adhyapak**

Computer Science (AI & ML)

Interested in:

- AI Engineering
- Agentic AI
- Backend Systems
- LLM Infrastructure
- Distributed Systems

---

## ⭐ If you found this project interesting, consider giving it a star!
