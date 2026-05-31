# SETUP GUIDE

This guide walks you through setting up a Google Cloud Project from scratch, enabling the Google Drive API, generating a Service Account credential file, and granting your codebase read access to a specific Google Drive folder.

---

## Step 1: Create a Google Cloud Account & Project

Before configuring APIs, you need a Google Cloud workspace (Project) to hold your credentials.

1. **Log In:** Go to the [Google Cloud Console](https://console.cloud.google.com/) and sign in using your Google/Gmail account.
2. **Accept Terms:** If this is your first time using the console, select your country, check the **Terms of Service** box, and click **Agree and Continue**.
3. **Create a Project:**
   * Click the **Select a project** dropdown menu at the very top of the screen (next to the "Google Cloud" logo).
   * In the top-right corner of the popup window, click **New Project**.
   * Enter a **Project Name** (e.g., `Fintech-Drive-Ingestion`).
   * Leave the Location/Organization as default and click **Create**.
   * Wait a few seconds for the creation notification, then ensure your new project is selected in the top dropdown menu.

---

## Step 2: Enable the Google Drive API

By default, all Google Cloud APIs are turned off for security. You must explicitly activate the Google Drive service.

1. **Open the API Library:** Click the **Navigation Menu** (three horizontal lines in the top-left corner). Hover over **APIs & Services** and select **Library**.
2. **Search for Drive:** In the center search bar, type `Google Drive API` and press **Enter**.
3. **Enable the Service:** Click on the **Google Drive API** search result and click the blue **ENABLE** button.
4. Once activated, the page will automatically redirect you to the Google Drive API Dashboard.

---

## Step 3: Create a Service Account & Generate JSON Key

A Service Account acts as a virtual "bot" user that your application code uses to securely log in to Google services.

1. **Navigate to Service Accounts:** Click the top-left **Navigation Menu** again. Go to **IAM & Admin** > **Service Accounts**.
2. **Configure the Account:** Click **`+ CREATE SERVICE ACCOUNT`** from the top menu bar.
   * Enter a **Service account name** (e.g., `drive-file-reader`).
   * Click **Create and Continue**.
   * Click **Continue** on the optional role configuration step, then click **Done**.
3. **Generate the Key File:** 
   * In the Service Accounts list, locate your newly created account and click on its **Email address**.
   * Switch to the **Keys** tab at the top of the details page.
   * Click the **Add Key** dropdown button and choose **Create new key**.
   * Ensure **JSON** is selected (default) and click **Create**.
   * *Result:* A private authentication file ending in `.json` will automatically download to your computer.

---

## Step 4: Configure Your Local Codebase

Now, provide this downloaded file to your local development environment.

1. **Create File:** Open your code editor and navigate to the **parent/root folder** of your project repository.
2. **File Setup:** Create a brand new file named exactly `credentials.json`.
3. **Populate Secrets:** Open the `.json` key file that was downloaded by Google Cloud in a standard text editor (like Notepad, TextEdit, or VS Code). Copy its entire text contents and paste them completely inside your new `credentials.json` file. Save the file.

---

## Step 5: Configure Google Drive Folder and Access

To allow your script to access the specific files it needs, you must authorize the service account and set up your environment variables.

### 1. Share the Google Drive Folder
1. Open your newly created `credentials.json` file and look for the `"client_email"` key. Copy the email address listed there (it will look like `drive-file-reader@...gserviceaccount.com`).
2. Go to your Google Drive and locate the folder you are using to store the company PDF files.
3. Right-click the folder, select **Share**, and paste the copied client email address.
4. Set the permissions role to **Viewer** and click **Send** (you can uncheck "Notify people" since it's a bot account).

### 2. Extract the Folder ID
1. Open the shared Google Drive folder in your browser.
2. Look at the browser's address bar. The URL will look something like this:
   `https://drive.google.com/drive/folders/1A2b3C4d5E6f7G8h9I0j_KLMnOpQrStUv`
3. Copy **only** the long alphanumeric string at the end of the URL (after `/folders/`). This is your unique Folder ID.

### 3. Update the Environment Variables
Create or open your `.env` file in the root directory of your codebase and append the following configurations:

```env
# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=your_extracted_folder_id_here

# Google AI Studio Configuration
GOOGLE_API_KEY=your_gemini_api_key_here