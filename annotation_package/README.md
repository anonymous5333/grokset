# Conversation Annotation Tool

This package contains the Streamlit application and the dataset sample required for human annotation.

## Prerequisites
Ensure that you have Python installed on your system.

## Setup Instructions

1. Open a terminal or command prompt in this extracted folder.
2. (Optional but recommended) Create and activate a virtual environment:
   - **Mac/Linux:**
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```
   - **Windows:**
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

1. Start the Streamlit application by running:
   ```bash
   streamlit run annotation_app.py
   ```
2. The application will open automatically in your browser.
3. Annotate the conversations using the provided UI.
4. Progress is saved locally as you hit "Save & Next".
5. When finished, or mid-way, you can use the "Download Current Results (CSV)" button in the app to extract your annotations!
