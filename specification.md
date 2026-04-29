# Project Specification: Automated ATS & Hunt Analytics Platform

## 1. The Core Objective
To build a personalized, automated Applicant Tracking System (ATS) that handles the end-to-end lifecycle of the job hunt. The system will autonomously ingest job postings, intelligently match and tag requirements, manage modular CV generation, and track application statuses via email integration.

**Primary Goal:** Reduce the friction of applying to jobs while creating a flagship, enterprise-grade portfolio piece demonstrating proficiency in modern data engineering, distributed systems, and full-stack development.

---

## 2. Architecture & Tech Stack
The project utilizes a polyglot microservices architecture, fully containerized for local deployment.

| Component | Technology Choice | Purpose |
| :--- | :--- | :--- |
| **Orchestration** | Apache Airflow | Trigger Python scrapers and manage the daily BigQuery sync. |
| **Ingestion/Scraping** | Python (Strategy Pattern) | Modular scrapers for job boards (e.g., Welcome to the Jungle, Indeed) pushing raw data to Kafka. |
| **Message Broker** | Apache Kafka | Stream raw scraped data between ingestion and processing layers. |
| **Operational DB** | PostgreSQL | Source of truth for job listings, CV tags, and UI state. |
| **Data Warehouse** | Google BigQuery | Storage for analytical data (cost-effective, highly scalable). |
| **Transformation** | dbt (Data Build Tool) | Clean and model BigQuery data for the dashboard. |
| **Backend/API** | Java Spring Boot | REST API, handling business logic, database ORM (Spring Data JPA), and consuming Kafka topics (Spring Kafka). |
| **Frontend/UI** | Angular | Component-driven UI, state management (RxJS), handling CV block CRUD and the analytics dashboard display. |
| **Infrastructure** | Docker & Docker Compose | Containerize all services for one-click local deployment. |

---

## 3. Service Perimeter 

### Pillar 1: Data Acquisition (The Scraper)
* **In Scope:** Scrapers built using a Strategy Pattern to easily add new job boards. Airflow handles the scheduling. Raw jobs are pushed as JSON events to a Kafka topic.
* **Out of Scope:** Bypassing complex CAPTCHAs or building residential proxy networks. (Keep scraping to accessible public data).

### Pillar 2: Data Processing & Storage (Backend)
* **In Scope:** A Spring Boot backend featuring a `@KafkaListener` that reads raw jobs, applies an NLP/rule-based auto-tagger (extracting keywords like "Java", "Angular", "Senior"), maps them to entities, and writes the enriched data to PostgreSQL using Spring Data JPA.
* **Out of Scope:** Training custom Machine Learning models from scratch. Simple string matching or lightweight NLP libraries are sufficient for keyword extraction.

### Pillar 3: Modular CV & UI (Frontend)
* **In Scope:** An Angular UI to input, read, update, and delete "CV Blocks." The UI will allow the user to select specific blocks, associate them with a scraped job, and generate a final LaTeX document (triggered via the Spring Boot backend).
* **Out of Scope:** A drag-and-drop WYSIWYG editor. Text-based blocks and backend LaTeX compilation are perfectly fine.

### Pillar 4: Email Tracking & Analytics
* **In Scope:** * An IMAP integration (handled by Spring Boot) that reads a designated inbox, attempting to match emails to jobs in PostgreSQL using a progressive strategy (Domain match -> Subject Line NLP -> Manual UI Fallback). 
  * A dbt pipeline moving data to BigQuery to power a "Hunt Analytics" funnel dashboard displayed on the Angular frontend.
* **Out of Scope:** Automatically replying to recruiters or sending automated follow-up emails.

---

## 4. Definition of Done (Deliverables)
To officially call this project "finished," the following must be delivered:
1. **A Clean GitHub Repository:** Featuring a comprehensive `README.md` with an architectural diagram.
2. **`docker-compose up` Functionality:** A user/recruiter should be able to clone the repo and spin up Airflow, Kafka, Postgres, the Spring Boot API, and the Angular UI with a single command (requires at least 8GB-12GB Docker memory allocation).
3. **The Analytics Dashboard:** A visual representation of the application funnel (Jobs Scraped -> Jobs Matched -> Applied -> Interview -> Offer).

---

## 5. Phased Implementation Plan (Recommended)
To prevent overwhelming technical debt and port conflicts, build sequentially:

* **Phase 1 (MVP Foundation):** Python Scraper -> direct write to PostgreSQL. (Verify data acquisition works).
* **Phase 2 (The Enterprise App):** Build the Java Spring Boot REST API and the Angular UI to display the data from Phase 1 and manage CV Blocks.
* **Phase 3 (Event-Driven Integration):** Introduce Dockerized Kafka. Refactor the Python scraper to produce to Kafka, and the Spring Boot app to consume from Kafka.
* **Phase 4 (Analytics & Orchestration):** Add Airflow to schedule the Python scraper. Add the BigQuery dump and dbt transformation pipeline for the analytics dashboard.