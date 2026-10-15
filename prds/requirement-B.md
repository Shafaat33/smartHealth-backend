SmartHealth — Intelligent Healthcare Operations & Patient Engagement Platform [Part - B]
MediNova is building SmartHealth, an intelligent large-scale healthcare platform designed to support modern hospitals, clinics, diagnostic centers, telemedicine providers, and enterprise healthcare networks.
The company is experiencing rapid growth in patients, healthcare providers, appointments, and medical operations, which has exposed several limitations in their current systems:
Appointment scheduling and patient onboarding workflows are slow and partially manual.
Patient records, appointments, billing, and clinical operations are spread across disconnected systems.
High traffic periods create delays in appointment booking and provider availability updates.
Notifications such as appointment reminders, cancellations, and follow-ups are unreliable.
Operational data across clinics and departments is inconsistent.
Rich patient interaction and service data is generated daily but remains underutilized.
MediNova now wants to evolve SmartHealth into an intelligent healthcare platform powered by GenAI.
Description / Problem Statement
This phase focuses on solving patient engagement and operational efficiency challenges through GenAI.
Current issues include:
Patients struggle to find the right services or specialties
Appointment journeys are static and non-personalized
Staff spend time answering repetitive queries
Clinical and operational data is underused for insights
Follow-up communication is mostly manual
This phase introduces:
AI healthcare assistant
Intelligent appointment support
Automated patient communication generation
Semantic knowledge retrieval
Streaming AI responses
Business Goals & Vision
Intelligent Patient Experience
Patients should be able to ask:
Which specialist should I consult for my symptoms?
What preparation is needed before my test?
Show available appointments this week
Explain my appointment steps
The platform should provide contextual and helpful responses.
Operational Productivity Enhancement
Teams should be able to generate:
Appointment summaries
Follow-up communication drafts
FAQ responses
Operational performance summaries
Patient engagement campaigns
Smooth Real-Time Interactions
Long-running AI responses should support streaming or asynchronous delivery and must not block core healthcare operations.

Core Functional Requirements
Content / Data Preparation Workflow
When healthcare operational data is updated:
Relevant data should be chunked
Embeddings should be generated
Searchable vector records should be stored
Data should become available for semantic retrieval
Intelligent Healthcare Assistant
A. Contextual Patient Q&A
Users ask healthcare service-related questions.
The system should:
Retrieve relevant service, provider, and operational information
Use contextual understanding
Generate meaningful responses
Handle incomplete or vague queries
B. Engagement & Recommendation Support
Generate:
Appointment reminders
Follow-up guidance
Service recommendations
Preventive care suggestions
Operational assistance responses
C. Report & Summary Generation
Generate:
Daily appointment summaries
Department utilization reports
Patient engagement summaries
Executive operational snapshots
Responses may be long and should support incremental delivery.
Analytics Metrics
AI Assistant Usage
Questions Asked / Answered
Booking Conversion After AI Interaction
Generated Communication Usage
Average AI Response Time
Engagement Improvement Metrics
Observability
Ability to diagnose failures in:
AI assistant interactions
Retrieval pipeline
Streaming responses
External LLM provider calls
Expected Outcomes
Intelligent healthcare assistant
Better patient engagement
Context-aware appointment guidance
Automated communication workflows
Scalable AI processing layer
PRD Requirement
AI use-cases
Functional / non-functional requirements
Delivery milestones
Feature traceability
Tech Stack
LangGraph / LangChain
LLM Provider (OpenAI / Groq / Anthropic)
Vector DB

