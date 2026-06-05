# Video Presentation Script & Strategy: OpsPilot Demo

If you are recording a video presentation for this project, the goal is to prove that you didn't just build a simple chat interface, but rather a **complete, cloud-deployed, AI-driven automation architecture**. 

Here is your exact, step-by-step playbook on what to show, what to click, and exactly what to say.

---

## 🎬 Phase 1: The Hook & Architecture (0:00 - 2:00)

**What to show on screen:**
Start with your live `internal-ops-automation.onrender.com` dashboard open. Then, switch to the `docs/Part_1_AI_Research_Evaluation.md` file in GitHub, and finally show your n8n Cloud workflows page.

**What to say:**
> *"Hello! Today I'm demonstrating OpsPilot, an internal operations automation platform I built. The problem I set out to solve is that IT and HR teams waste hundreds of hours manually triaging tickets, approving standard leave requests, and extracting tasks from meetings.*
> 
> *Before writing any code, I conducted a deep research evaluation—which you can see in my repository—comparing OpenAI, Gemini, Ollama, and n8n to find the most cost-effective and secure stack.*
>
> *Based on that research, I built a Hybrid AI architecture. The frontend and backend are hosted live on Render. The core reasoning engine uses Google Gemini for high-speed logic, and I am using n8n Cloud as my background automation orchestrator."*

---

## 🎬 Phase 2: Live Feature Demonstration (2:00 - 5:00)

### 1. The Dashboard & Interactive UI
**Action:** Click around the main dashboard. Click the "Open" task badges to show how they instantly turn to "Done". 
**What to say:** 
> *"This is the central command center. Notice how it's fully interactive—I can mark tasks as done directly from the badges, and the backend instantly updates the SQLite database."*

### 2. Smart IT Ticketing (LangGraph Orchestration)
**Action:** Go to the **Tickets** tab. Submit a new ticket:
- *Title:* Payroll portal is crashing for the finance team.
- *Description:* Nobody in finance can run the end-of-month payroll.
**What to say:** 
> *"Let's look at IT Support. When I submit this ticket about payroll crashing, it doesn't just save to a database. It runs through a multi-step AI pipeline. The AI classifies the category, assesses the operational risk (marking this as Critical), routes it to the Finance Ops team, and generates a suggested resolution."*

### 3. HR Leave Automation
**Action:** Go to the **Leave** tab. Submit a leave request for "Annual Leave" starting tomorrow for 14 days. 
**What to say:** 
> *"For HR, we automate PTO triage. If I submit a request for 14 days of leave starting tomorrow, the AI immediately flags it. Instead of auto-approving, the AI recommendation is 'Review' because the notice period is too short for a 2-week absence. Notice how I can click the badge to manually override it to 'Approved'."*

### 4. Meeting Task Extraction
**Action:** Go to the **Meetings** tab and paste a short transcript (e.g., "Rahul: I will fix the database by Friday. Neha: I will email the client today.")
**What to say:** 
> *"Instead of ops managers reading meeting transcripts, OpsPilot extracts actionable items. It pulls out exact tasks, assigns owners, and pushes them directly to our Task Board."*

---

## 🎬 Phase 3: The "Magic" Features (5:00 - 7:00)

### 1. RAG Document Q&A
**Action:** Go to the **Docs Q&A** tab. Add a quick document about "Company Remote Work Policy" (e.g., "Remote work is allowed on Tuesdays and Thursdays"). Then ask a question: *"What days can I work from home?"*
**What to say:** 
> *"I also implemented a Retrieval-Augmented Generation (RAG) system. Employees can ask questions about company policies, and the AI will only answer based on indexed documents, returning the exact source to prevent hallucinations."*

### 2. The Ops Agent & Daily Reports
**Action:** Go to the **Reports** tab and click "Generate daily report." Then, use the chat box on the right side of the screen. Ask: *"How many critical tickets do we have right now?"*
**What to say:** 
> *"Finally, Ops Managers have an on-demand AI Assistant. Because this agent is plugged directly into our database context, I can ask it for real-time metrics, and it will read the live database state to answer me."*

---

## 🎬 Phase 4: Behind the Scenes (7:00 - 8:00)

**What to show:** Open your n8n Cloud tab showing your 5 active workflows.
**What to say:**
> *"To tie this all together, I didn't want to hardcode every single automation in Python. So, I integrated **n8n Cloud**. I built 5 distinct workflow templates that listen for webhooks and scheduled triggers. This means non-developers can log into n8n and visually adjust automations without touching my Python codebase.*
>
> *Thank you for watching the demo. The entire codebase, including deployment blueprints and my detailed AI research report, is available on my GitHub."*

---

## 💡 Key Tips for the Video
1. **Don't rush the research part:** The fact that you *evaluated* different tools (Gemini vs. Ollama) proves you think like a Senior Engineer/Architect, not just a junior coder. Point out your markdown report.
2. **Focus on Business Value:** Keep mentioning *why* you built it (saving time, reducing HR bottlenecks, automating task tracking).
3. **Keep the pace up:** Have your text for the ticket and meeting transcripts ready to copy-paste so you aren't awkwardly typing during the video.
