import os
from langchain_mistralai import ChatMistralAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone as PineconeClient
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

# ---- Initialize all components once ----
llm = ChatMistralAI(
    model="open-mistral-nemo",
    api_key=os.environ["MISTRAL_API_NEW"],
    temperature=0.3
)

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
pc = PineconeClient(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("bra")

mem = ConversationBufferWindowMemory(
    memory_key="chat_history",
    k=10,
    return_messages=True
)

db = PineconeVectorStore(
    index=index,
    embedding=embedding_model,
    text_key="text"
).as_retriever()

chatbot = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=db,
    memory=mem
)

# ---- Prompt helper ----
def create_prompt(metrics: dict, user_input: str) -> str:
    formatted_metrics = "\n".join(f"{k}: {v}" for k, v in metrics.items() if v)

    normal_ranges = """
Normal Ranges:
- Hemoglobin: 13–17 g/dL
- RBC: 4.5–5.0 ×10⁶/µL
- MCV: 80–100 fL
- MCH: 27–32 pg
- MCHC: 32–35 g/dL
- Platelet Count: 150–450 ×10³/µL
"""

    prompt = f"""
You are a medical insights assistant providing general, educational information
about blood reports. Never give diagnostic statements or prescriptions.

Given the following blood metrics, follow these steps:
1. Identify which metrics are abnormal (based on the normal ranges).
2. Explain possible causes, symptoms, and remedies.
3. Do not answer for missing metrics.
4. Use clear, layperson language.
5. End with: "These insights are for educational purposes only. Please consult a doctor for confirmation."

{normal_ranges}

Patient Blood Report:
{formatted_metrics}

User Question:
{user_input}
"""
    return prompt.strip()


def chat_with_blood_ai(metrics: dict, user_input: str) -> str:
    """Run the conversational RAG chatbot on blood report metrics."""
    prompt_text = create_prompt(metrics, user_input)
    result = chatbot.invoke({"question": prompt_text})
    return result["answer"]