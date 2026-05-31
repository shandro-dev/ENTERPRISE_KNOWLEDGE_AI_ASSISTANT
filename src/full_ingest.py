import os
import io
from dotenv import load_dotenv

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from pypdf import PdfReader

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma


# =========================
# ENV
# =========================
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
VECTOR_DB_PATH = "./vector_db"


# =========================
# GOOGLE DRIVE AUTH
# =========================
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

service = build("drive", "v3", credentials=creds)


# =========================
# EMBEDDINGS
# =========================
embedding_model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY
)


# =========================
# LOAD EXISTING VECTOR DB
# =========================
vectorstore = Chroma(
    persist_directory=VECTOR_DB_PATH,
    embedding_function=embedding_model
)

print("Loaded existing vector DB")


# =========================
# GET ALREADY PROCESSED FILES
# =========================
existing_data = vectorstore.get()

processed_files = {}

if existing_data and existing_data.get("metadatas"):
    for meta in existing_data["metadatas"]:
        if meta and "file_id" in meta:
            processed_files[meta["file_id"]] = meta.get("modified_time")


print(f"Already indexed files: {len(processed_files)}")


# =========================
# LIST GOOGLE DRIVE FILES
# =========================
results = service.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed=false",
    fields="files(id,name,mimeType,modifiedTime)"
).execute()

files = results.get("files", [])

print(f"\nFound {len(files)} files in Drive\n")

# =========================
# TEXT SPLITTER
# =========================
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200
)


# =========================
# INGESTION LOOP
# =========================
for file in files:

    file_id = file["id"]
    file_name = file["name"]
    modified_time = file["modifiedTime"]

    if not file_name.lower().endswith(".pdf"):
        continue

    print(f"\nChecking: {file_name}")

    # =========================
    # 1. CHECK EXISTING FILE META FIRST (NO DELETE YET)
    # =========================
    existing_docs = vectorstore.get(where={"file_id": file_id})

    should_update = False

    if not existing_docs["ids"]:
        print("New file detected")
        should_update = True
    else:
        existing_meta = existing_docs["metadatas"][0]
        if existing_meta.get("modified_time") != modified_time:
            print("File updated")
            should_update = True
        else:
            print("Skipping unchanged file")
            continue  # IMPORTANT: do NOTHING

    # =========================
    # 2. ONLY NOW DELETE OLD CHUNKS (if updating)
    # =========================
    if should_update:
        vectorstore.delete(where={"file_id": file_id})
        print("Old chunks deleted")

    # =========================
    # 3. DOWNLOAD FILE
    # =========================
    request = service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()

    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    file_stream.seek(0)

    pdf = PdfReader(file_stream)

    text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    if not text.strip():
        continue

    # =========================
    # 4. PROCESS
    # =========================
    doc = Document(
        page_content=text,
        metadata={
            "source": file_name,
            "file_id": file_id, 
            "modified_time": modified_time
        }
    )

    chunks = splitter.split_documents([doc])
    ids = [f"{file_id}_{i}" for i in range(len(chunks))]

    vectorstore.add_documents(chunks, ids=ids)

    print(f"Ingested: {file_name}")


print("\n✅ Incremental ingestion completed successfully")