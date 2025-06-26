# Document Aggregation & Verification Engine

![Project Demo GIF](https://your-image-host.com/demo.gif) <!-- Optional: Create and upload a GIF of your app and link it here -->

This project is an AI-driven web application designed to provide a holistic and analytical view of a professional's identity. It ingests single or multiple resumes, scrapes public profiles from platforms like LinkedIn, GitHub, LeetCode, and Kaggle, and uses Large Language Models (LLMs) to perform a detailed comparison and generate a comprehensive verification report.

The system is built on a modern, asynchronous architecture using Flask and Celery to handle long-running data scraping and analysis tasks efficiently, providing a non-blocking, real-time user experience.

## Key Features

-   **Batch Resume Processing:** Upload one or more resumes at once for high-throughput verification.
-   **Multi-Source Aggregation:** Scrapes data from LinkedIn, GitHub, LeetCode, and Kaggle.
-   **AI-Powered Analysis:** Uses the Google Gemini API to parse resumes and generate a final detailed report.
-   **Consistency Scoring:** Quantifies the alignment between a candidate's resume and their online presence with a numerical score.
-   **Discrepancy & Highlight Reporting:** Identifies contradictions, data omissions, and unique highlights from each platform.
-   **Live Job Dashboard:** A history page that updates in real-time, showing the status of all verification jobs with sorting and filtering.
-   **PDF Report Generation:** Download any completed report as a clean, professional PDF.
-   **Resilient & Robust:** Built with automatic retries for network failures and graceful error handling.

## Tech Stack

-   **Backend:** Python, Flask, Celery
-   **Frontend:** HTML, CSS, Vanilla JavaScript
-   **Database:** MongoDB
-   **Task Queue Broker:** Redis
-   **Core AI:** Google Gemini API
-   **External Services:** Apify (for LinkedIn)
-   **Key Python Libraries:** `Flask`, `Celery`, `PyMongo`, `google-generativeai`, `apify-client`, `httpx`, `backoff`, `WeasyPrint`

---

## Local Setup & Installation Guide

Follow these steps to set up and run the project on your local machine.

### 1. Prerequisites: System-Level Dependencies

Before installing the Python packages, you must have the following software installed on your system:

-   **Python** (3.10+ recommended)
-   **MongoDB:** The database for storing job data. [Official Installation Guide](https://www.mongodb.com/docs/manual/installation/)
-   **Redis:** The message broker for Celery. [Official Installation Guide](https://redis.io/docs/getting-started/installation/)
-   **Google Tesseract OCR:** Required for the resume parsing pipeline. [Tesseract Installation Guide](https://github.com/UB-Mannheim/tesseract/wiki). Make sure to add the Tesseract installation directory to your system's `PATH`.

-   **(For Windows Users) GTK3 Runtime for PDF Generation:** This is required by the WeasyPrint library.
    1.  Install **MSYS2** from [msys2.org](https://msys2.org/).
    2.  After installation, open the **MSYS2 MinGW 64-bit** terminal (from your Start Menu).
    3.  Run the command: `pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-pango`
    4.  Add the GTK3 `bin` folder (e.g., `C:\msys64\mingw64\bin`) to your system's **`PATH` environment variable**. You must restart your terminals after this step.

### 2. Project Configuration

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/your-repository-name.git
    cd your-repository-name
    ```

2.  **Set Up a Python Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install All Python Dependencies:** This single command will install everything listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    -   Find the `.env.example` file and rename it to `.env`.
    -   Open the `.env` file and add your secret API keys.
    ```.env
    # Get from Google AI Studio
    GOOGLE_API_KEY="AIzaSy...your_google_api_key_here"

    # Get from the Apify Console
    APIFY_API_TOKEN="apify_api_...your_apify_token_here"
    ```

### 3. Running the Application

The application requires three separate processes to be running in three different terminals. **Ensure your virtual environment is activated in each terminal.**

**Terminal 1: Start Redis & MongoDB**
-   Make sure your **MongoDB** and **Redis** services are running in the background. If you didn't install them as services, you will need to start them manually according to their documentation.

**Terminal 2: Start the Celery Worker**
```bash
# For optimal performance, run with a concurrency limit (e.g., 2)
python -m celery -A tasks.celery worker --loglevel=info -P eventlet -c 2
```

**Terminal 3: Start the Flask Web Server**
```bash
python app.py
```

### 4. Using the Application
-   Open your web browser and navigate to **`http://127.0.0.1:5000/`**.
-   Upload one or more resumes to start a batch verification.
-   You will be redirected to the **History** page to monitor the progress of your jobs in real-time.

---
## Project Structure Overview
```
/
├── app.py              # Main Flask application
├── tasks.py            # Celery background tasks
├── requirements.txt    # All Python dependencies
├── .env.example        # Template for API keys
├── scrapers/           # Folder for all data scrapers
├── dataCompare/        # AI analysis and comparison logic
└── templates/          # HTML files for the UI
```