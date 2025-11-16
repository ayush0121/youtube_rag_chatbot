# rag_pipeline.py

import os
import shutil
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

# Configuration
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
PERSIST_DIR = "./chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 4

# Optimized prompt template with multilingual support
PROMPT_TEMPLATE = PromptTemplate(
    template="""You are a helpful AI assistant analyzing a YouTube video transcript.

Your task is to answer questions based on the provided transcript context. Follow these rules:
- Answer directly and concisely in the SAME LANGUAGE as the question
- If the question is in Hindi, respond in Hindi
- If the question is in English, respond in English
- Use information ONLY from the context provided
- For summary requests, provide a comprehensive summary of the context given
- For specific questions, find and extract the relevant information
- If you cannot find specific information to answer the question, respond with: "I cannot find that specific information in the video transcript." (or in Hindi: "मुझे वीडियो ट्रांसक्रिप्ट में यह विशिष्ट जानकारी नहीं मिली।")
- Do not make assumptions or add external knowledge

Context from video transcript:
{context}

Question: {question}

Answer:""",
    input_variables=["context", "question"],
)


def clear_vector_store():
    """Clear the persisted Chroma database."""
    if os.path.exists(PERSIST_DIR):
        try:
            shutil.rmtree(PERSIST_DIR)
            print(f"✅ Cleared vector store at {PERSIST_DIR}")
        except Exception as e:
            print(f"⚠️ Could not clear vector store: {e}")


def process_transcript(transcript: str) -> Chroma:
    """
    Process transcript into vector store.
    
    Args:
        transcript: Raw transcript text
        
    Returns:
        Chroma vector store with embedded transcript chunks
    """
    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty")
    
    # Clear old vector store
    clear_vector_store()
    
    # Split transcript into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_text(transcript)
    print(f"📄 Created {len(chunks)} chunks from transcript")
    
    # Create documents with metadata
    documents = [
        Document(
            page_content=chunk,
            metadata={"chunk_id": i, "source": "youtube_transcript"}
        )
        for i, chunk in enumerate(chunks)
    ]
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Create vector store
    print("🔄 Creating vector store...")
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )
    
    # Persist to disk
    vector_store.persist()
    print("✅ Vector store created and persisted")
    
    return vector_store


def get_answer(question: str, vector_store: Chroma, llm) -> str:
    """
    Get answer to question using RAG pipeline.
    
    Args:
        question: User's question
        vector_store: Chroma vector store with transcript
        llm: Language model instance
        
    Returns:
        Answer string
    """
    if not question or not question.strip():
        return "Please ask a valid question."
    
    try:
        # Check if this is a summary/overview request
        summary_keywords = [
            'summarize', 'summary', 'overview', 'gist', 'brief', 
            'what is this video about', 'main topic', 'main points',
            'सारांश', 'संक्षेप', 'मुख्य बिंदु', 'विषय', 'बारे में'
        ]
        
        is_summary_request = any(keyword in question.lower() for keyword in summary_keywords)
        
        # For summary requests, get more chunks
        k_results = 8 if is_summary_request else TOP_K_RESULTS
        
        # Retrieve relevant documents using invoke (newer LangChain API)
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k_results}
        )
        
        # Use invoke instead of get_relevant_documents
        relevant_docs = retriever.invoke(question)
        
        if not relevant_docs:
            return "I cannot find relevant information in the video transcript to answer your question."
        
        # Combine context from retrieved documents
        context = "\n\n".join([
            f"[Chunk {doc.metadata.get('chunk_id', 'N/A')}]: {doc.page_content}"
            for doc in relevant_docs
        ])
        
        # Format prompt
        formatted_prompt = PROMPT_TEMPLATE.format(
            context=context,
            question=question
        )
        
        # Get LLM response - using .invoke()
        response = llm.invoke(formatted_prompt)
        
        # Extract content from response
        if isinstance(response, str):
            return response.strip()
        elif hasattr(response, "content"):
            return response.content.strip()
        else:
            return str(response).strip()
            
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        return f"An error occurred while processing your question: {str(e)}"


def get_transcript_summary(vector_store: Chroma, llm, max_chunks: int = 10) -> str:
    """
    Generate a summary of the transcript.
    
    Args:
        vector_store: Chroma vector store with transcript
        llm: Language model instance
        max_chunks: Maximum chunks to use for summary
        
    Returns:
        Summary string
    """
    try:
        # Get first few chunks
        all_docs = vector_store.get()
        sample_docs = all_docs['documents'][:max_chunks]
        context = "\n\n".join(sample_docs)
        
        summary_prompt = f"""Provide a concise summary of this YouTube video transcript:

{context}

Summary:"""
        
        response = llm.invoke(summary_prompt)
        
        if isinstance(response, str):
            return response.strip()
        elif hasattr(response, "content"):
            return response.content.strip()
        else:
            return str(response).strip()
            
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return "Could not generate summary."