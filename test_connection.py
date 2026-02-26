import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

response = llm.invoke("list down name of prime-ministers of india after independence.")
print(response.content)
print("\n--- CONNECTION SUCCESSFUL ---")
print(f"Model: llama-3.3-70b-versatile")
print(f"Response length: {len(response.content)} characters")