SmartHealth — Intelligent Healthcare Operations & Patient Engagement Platform [Part - A]
MediNova is building SmartHealth, an intelligent large-scale healthcare platform designed to support modern hospitals, clinics, diagnostic centers, telemedicine providers, and enterprise healthcare networks.
The company is experiencing rapid growth in patients, healthcare providers, appointments, and medical operations, which has exposed several limitations in their current systems:
Appointment scheduling and patient onboarding workflows are slow and partially manual.
Patient records, appointments, billing, and clinical operations are spread across disconnected systems.
High traffic periods create delays in appointment booking and provider availability updates.
Notifications such as appointment reminders, cancellations, and follow-ups are unreliable.
Operational data across clinics and departments is inconsistent.
Rich patient interaction and service data is generated daily but remains underutilized.
To address these challenges, MediNova is commissioning a new backend for SmartHealth with the following business goals.
Description / Problem Statement
This part focuses on building the foundational backend system of SmartHealth, solving scalability, consistency, and reliability challenges in patient management, appointment scheduling, provider operations, billing workflows, notifications, and analytics.
The goal is to solve:
Slow and manual appointment scheduling workflows
Inconsistent patient and provider operational data
High latency during traffic spikes
Lack of reliable background processing for operational tasks
Weak observability and failure recovery mechanisms
Business Goals & Vision
SmartHealth must provide:
A Robust Patient & Provider Management System
Healthcare staff should be able to register patients, manage appointments, configure provider schedules, maintain department availability, and track service operations.
Patients should be able to book appointments, reschedule visits, receive reminders, and access booking history.
Providers should be able to manage schedules, appointments, consultation slots, and service workflows.
A Scalable and Reliable Operations Backbone
Booking or updating an appointment may trigger multiple internal processes such as:
Provider slot reservation
Calendar synchronization
Billing pre-check workflows
Reminder scheduling
Notification delivery
Operational analytics updates
Cancelling or rescheduling appointments may trigger:
Slot release workflows
Waitlist movement
Refund or billing updates
Patient notifications
Consistent and Accurate Healthcare Data
The state of patients, appointments, provider schedules, payments, visit history, notifications, and service records must be accurate, durable, and easy to query.
A Foundation for Long-Term Scalability
As SmartHealth grows, the platform should handle:
Tens of thousands of appointment requests
Concurrent provider schedule updates
Peak booking windows
Multi-clinic operations
Reliable background workflows under heavy load
Core Functional Requirements
1. Patient & User Management
Patient registration and profile management
Provider registration and specialty management
User registration with appropriate roles:
patient
provider
front desk staff
admin
Department and clinic management
Audit trail for profile and operational changes
Each update should ensure consistency across all connected systems.
2. Appointment Scheduling Workflow
When a patient books or updates an appointment:
Patient eligibility and details should be validated
Provider slot should be reserved
Schedule conflicts should be prevented
Notifications should be scheduled
Billing pre-check may be initiated
Appointment should be marked as confirmed only after successful processing
Partial failures must not corrupt the scheduling state.
3. Visit & Service Workflow
When an appointment occurs:
Check-in should be recorded
Visit progress should be updated
Completion should be stored
Billing workflows may be triggered
Follow-up reminders may be scheduled
Analytics should be updated
This workflow must support:
High volume operational updates
Idempotent retries
Recovery from failures
Duplicate prevention
Real-time status visibility
4. Distributed & Event-Driven Behaviors
Examples include:
Appointment booked events
Cancellation or reschedule events
Provider schedule changes
Reminder notifications
Billing status updates
Visit completion events
Analytics processing events
These tasks should:
Run independently from user-facing flows
Be traceable and recoverable
Handle failures gracefully
Avoid double-processing
Support workload spikes efficiently
5. Analytics Metrics
Total Patients
Appointments Booked Over Time
Completed Visits
Cancellation Rate
Average Wait Time



6. System Observability & Reliability Expectations
Clear separation of responsibilities between services/modules
Monitoring and logging for all critical flows
Ability to diagnose failures in:
Appointment booking workflows
Provider availability sync
Billing workflows
Reminder notifications
Background workers
High consistency across all operational data models
Expected Outcomes
Support complete patient lifecycle operations
Reliable booking and service workflows
High scalability during load spikes
Strong consistency and recoverability
Maintainable production-grade architecture
PRD Requirement
Key use-cases
Functional and non-functional requirements
Delivery timeline / milestones
Traceability between features and deliverables
Tech Stack
Backend
Python
FastAPI
PostgreSQL
NoSQL DB
Redis
Celery Workers with RabbitMQ
Kafka + Schema Registry
Temporal (workflows)
Observability
Prometheus + Grafana
Jaeger
OpenTelemetry
DevOps
Docker
Docker Compose

