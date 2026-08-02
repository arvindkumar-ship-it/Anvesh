# pipelines/rag_pipeline.py


from types import SimpleNamespace
from typing import Dict, List, Optional,Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from llm_config import get_llm_response
from langchain_core.prompts import ChatPromptTemplate
from vector_db.chroma_store import ChromaStore
from dotenv import load_dotenv
from pydantic import SecretStr
import os

load_dotenv()
# load_dotenv() kyun?
# .env file mein GROQ_API_KEY=xxx likha hai
# load_dotenv() use environment variables mein load karta hai
# os.getenv("GROQ_API_KEY") tab kaam karta hai


class HermesRAGPipeline:
    """
    2 main responsibilities:

    1. BUILD: IngestedDoc → ChromaDB
       (ek baar karo — expensive operation)

    2. QUERY: Question → Relevant answer
       (baar baar karo — fast operation)
    """

    def __init__(self):

        # HuggingFace free embeddings — OpenAI ki zaroorat nahi
        # all-MiniLM-L6-v2 → 384 dimensions
        # Fast, good quality, completely free
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        # # Groq — OpenAI se replace kiya
        # # Groq bahut fast hai (LPU hardware)
        # # Free tier available hai
        # # llama3-8b-8192 = fast + good quality
        # api_key = SecretStr(os.getenv("GROQ_API_KEY") or "")
        # self.llm = ChatGroq(
        #     model="llama-3.3-70b-versatile",
        #     temperature=0,
        #     # temperature=0 kyun?
        #     # temperature controls randomness
        #     # 0 = deterministic, consistent answers
        #     # 1 = creative, varied answers
        #     # RAG Q&A ke liye consistency chahiye → 0
        #     api_key=api_key
        #     # from langchain_core.utils import SecretStr
        # # api_key = SecretStr(os.getenv("GROQ_API_KEY") or "")
        # )
        self.store = ChromaStore()

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            # 500 chars ~= 125 tokens
            # Sweet spot: enough context, not too large
            # Too small → context missing
            # Too large → irrelevant info included

            chunk_overlap=50,
            # 50 chars overlap → ~10% of chunk size
            # Standard recommendation hai
            # Context boundary preserve hoti hai

            separators=["\n\n", "\n", ". ", " ", ""]
            # Priority order mein try karta hai:
            # 1. Double newline (paragraph break) try karo
            # 2. Single newline try karo
            # 3. Period+space (sentence end) try karo
            # 4. Space (word boundary) try karo
            # 5. Anywhere (last resort) try karo
        )

        self.is_built = False

    # ─────────────────────────────────────
    # BUILD: IngestedDoc → ChromaDB
    # ─────────────────────────────────────

    def build(self, ingested_doc) -> None:

        print("\n🔨 Building RAG pipeline...")

        self.store.clear()
        # Pehle clear kyun?
        # Naya API load karte waqt purana data
        # mix nahi hona chahiye

        all_chunks = []
        all_metadatas = []
        all_ids = []
        chunk_counter = 0

        for section_name, section_text in ingested_doc.sections.items():
            # .items() → (key, value) pairs iterate karo
            # section_name = "authentication"
            # section_text = "Use Bearer token..."

            if not section_text or len(section_text.strip()) < 50:
                continue
                # continue kyun?
                # Too short sections skip karo
                # Ye garbage data hai — noise add karega

            chunks = self.splitter.split_text(section_text)
            # split_text() → list of strings
            # ["chunk1 text", "chunk2 text", ...]

            print(f"   '{section_name}': {len(chunks)} chunks")

            for chunk in chunks:
                if len(chunk.strip()) < 20:
                    continue   # Very small chunks skip

                all_chunks.append(chunk)

                all_metadatas.append({
                    "source": ingested_doc.source_url,
                    "section": section_name,
                    # Section tag kyun?
                    # Baad mein filter kar sako:
                    # "Sirf authentication section se answer do"
                    "format": ingested_doc.format_type,
                    "chunk_index": chunk_counter
                })

                all_ids.append(f"chunk_{chunk_counter}")
                # IDs unique hone chahiye ChromaDB mein
                # Simple counter se guarantee milti hai

                chunk_counter += 1

        # ── Batch Embeddings ──
        print(f"\n   🔢 Embedding {len(all_chunks)} chunks...")

        batch_size = 100
        all_embeddings = []

        for i in range(0, len(all_chunks), batch_size):
            # range(0, total, 100) → 0, 100, 200, 300...
            # Batches: [0:100], [100:200], [200:300]...

            batch = all_chunks[i:i + batch_size]
            # Python slice → i se i+100 tak ke chunks

            batch_embeddings = self.embeddings.embed_documents(batch)
            # embed_documents() → list of lists
            # [[0.23, -0.11, ...], [0.45, 0.12, ...], ...]
            # Har chunk ka ek vector

            all_embeddings.extend(batch_embeddings)
            # .extend() vs .append()
            # .append([1,2,3]) → [[1,2,3]] (nested)
            # .extend([1,2,3]) → [1,2,3] (flat) ← ye chahiye

            print(f"   Batch {i//batch_size + 1} done "
                  f"({min(i+batch_size, len(all_chunks))}"
                  f"/{len(all_chunks)})")

        # ── Store in ChromaDB ──
        self.store.add_chunks(
            chunks=all_chunks,
            embeddings=all_embeddings,
            metadatas=all_metadatas,
            ids=all_ids
        )

        self.is_built = True
        print(f"\n✅ RAG ready! Chunks indexed: {self.store.count()}")

    # ─────────────────────────────────────
    # QUERY: Question → Answer from docs
    # ─────────────────────────────────────
    from typing import Dict, Optional,Any
    def query(
            self,
            question: str,
            section_filter: Optional[str] = None
            ) -> Dict[Any,Any]: # type: ignore

            if not self.is_built:
                raise ValueError("Pehle build() call karo!")
                # raise kyun?
                # Agar build() nahi hua toh ChromaDB empty hai
                # Meaningless results milenge
                # Better to fail loudly than silently

            # Step 1: Question ko embed karo
            query_embedding = self.embeddings.embed_query(question)
            # embed_query() → single vector
            # embed_documents() → list of vectors
            # Dono alag methods kyun?
            # Query aur documents differently normalized hote hain

            # Step 2: Similar chunks dhundo
            results = self.store.search(
                query_embedding=query_embedding,
                n_results=4,
                #section_filter=section_filter
            )

            retrieved_chunks = results["documents"][0]
            # results structure:
            # {
            #   "documents": [[chunk1, chunk2, chunk3, chunk4]],
            #   "metadatas": [[meta1, meta2, meta3, meta4]],
            #   "distances": [[0.12, 0.23, 0.45, 0.67]]
            # }
            # [0] kyun? Batch query ka pehla result
            # Hum sirf ek query karte hain

            retrieved_metadatas = results["metadatas"][0]

            if not retrieved_chunks:
                return {
                    "answer": "Documentation mein ye information nahi mili.",
                    "sources": [],
                    "confidence": "none"
                }

            # Step 3: Context banao
            context_parts = []
            for chunk in retrieved_chunks:
                context_parts.append(chunk)

            context = "\n\n---\n\n".join(context_parts)
            # --- separator kyun?
            # LLM ko clearly pata ho ki chunks alag hain
            # Context mein boundaries important hain

            # Step 4: LLM se answer lo
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an API documentation expert.
    Answer questions using ONLY the provided documentation context.
    If the answer is not in the context, say so clearly.
    Be specific and technical. Include exact values."""),

                ("human", """
    Documentation Context:
    {context}

    Question: {question}

    Answer based only on the above documentation:""")
            ])
            # ChatPromptTemplate kyun?
            # f-string use kar sakte the but:
            # Template reuse hota hai
            # Variables clearly defined hain
            # LangChain chain mein pipe karna easy hai

            # chain = prompt | self.llm
            # # Ye LCEL (LangChain Expression Language) hai
            # # prompt ka output → llm ka input
            # # Clean, readable, composable

            # response = chain.invoke({
            #     "context": context,
            #     "question": question
            # })
            # 1. Messages format karo
            raw_messages = prompt.format_messages(
                context=context, 
                question=question
            )
            # Objects ko LiteLLM compatible Dictionaries mein convert karo
            formatted_messages = [
                {"role": msg.type if msg.type != "human" else "user", "content": msg.content}
                for msg in raw_messages
            ]
            # 2. LiteLLM Fallback Call
            response_text = get_llm_response(formatted_messages)
            # 3. Dummy object taaki response.content (Line 277) na toote
            from types import SimpleNamespace
            response = SimpleNamespace(content=str(response_text))
            # invoke() → synchronous call
            # ainvoke() → async call (baad mein use karna ho toh)

            # Step 5: Sources
            sources = []
            for meta in retrieved_metadatas:
                sources.append(meta["section"])

            return {
                "answer": response.content,
                "sources": sources,
                "confidence": "high",
                "chunks_used": len(retrieved_chunks)
            }
    def get_relevant_chunks(
            self,
            question: str,
            n: int = 3
            ) -> list:
         if not self.is_built:
             raise ValueError("Pehle build() call karo!")
         query_embedding = self.embeddings.embed_query(question)
         query_embedding = self.embeddings.embed_query(question)
         results = self.store.search(
             query_embedding=query_embedding,
             n_results=n
             )
         chunks = results["documents"][0]
         metadatas = results["metadatas"][0]
         return [
             {"text": c, "section": m["section"]}
             for c, m in zip(chunks, metadatas)
             ]