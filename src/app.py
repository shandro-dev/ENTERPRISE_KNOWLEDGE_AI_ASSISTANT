import os
import threading
from dotenv import load_dotenv
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)
from langchain_chroma import Chroma

load_dotenv()


# EMBEDDINGS
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


# VECTOR DB
vectorstore = Chroma(
    persist_directory="./vector_db",
    embedding_function=embeddings
)


# LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)


# CHAT MEMORY
chat_history = []

FIRST_TURNS = 2
LAST_TURNS = 3


def _build_history_text():
    # Change 1: first 2 turns + last 3 turns instead of flat last 10 messages
    if not chat_history:
        return ""

    total_turns = len(chat_history) // 2
    first_msgs  = FIRST_TURNS * 2
    last_msgs   = LAST_TURNS * 2

    if total_turns <= FIRST_TURNS + LAST_TURNS:
        recent = chat_history
    else:
        first     = chat_history[:first_msgs]
        last      = chat_history[-last_msgs:]
        separator = [("...", "...")]
        recent    = first + separator + last

    return "\n".join(f"{role}: {text}" for role, text in recent)


# CHAT FUNCTION
def ask_question(question):

    global chat_history

    history_text = _build_history_text()

    # Change 2: rewrite + vector search run in parallel
    rewrite_result = [question]
    docs_result    = [None]

    def do_rewrite():
        if not history_text:
            return                          # Change 3: skip rewrite on first turn
        rewrite_prompt = f"""
Conversation History:
{history_text}

Current User Question:
{question}

Rewrite the question into a standalone search query.

Return only the rewritten query.
"""
        rewrite_result[0] = llm.invoke(rewrite_prompt).content.strip()

    def do_search():
        docs_result[0] = vectorstore.similarity_search(question, k=5)

    t1 = threading.Thread(target=do_rewrite)
    t2 = threading.Thread(target=do_search)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Retrieve Documents using rewritten query
    docs = vectorstore.similarity_search(rewrite_result[0], k=5)

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )


    # Final Answer
    response = llm.invoke(
        f"""
You are Enterprise Knowledge Assistant.

Your role is to answer employee questions about:
- HR policies
- Compliance policies
- Company procedures
- Employee benefits
- Company knowledge

Conversation History:
{history_text}

Knowledge Base:
{context}

User Question:
{question}

Rules:

1. Never mention:
   - context
   - document
   - provided information
   - knowledge base
   - source material

2. Answer naturally as if you already know the information.

3. Never say:
   - "Based on the provided context..."
   - "The document states..."
   - "According to the context..."
   - "The information provided indicates..."

4. If the answer can be reasonably inferred from the available company information, provide a helpful answer.

5. If the answer is related to company policies but the information is unavailable, say:
   "I couldn't find sufficient information regarding that policy."

6. If the question is unrelated to company information, HR, compliance, benefits, procedures, or internal knowledge, reply exactly:
   "I am not authorised to answer external questions."

7. If the question contains abusive, offensive, or inappropriate language, politely refuse.

Answer professionally.
"""
    )

    answer = response.content


    # Save Chat Memory
    chat_history.append(("User", question))
    chat_history.append(("Assistant", answer))

    return answer


# CHAT LOOP
while True:

    question = input("\nYou: ")

    if question.lower() in ["exit", "quit"]:
        break

    answer = ask_question(question)

    print("\nAssistant:")
    print(answer)