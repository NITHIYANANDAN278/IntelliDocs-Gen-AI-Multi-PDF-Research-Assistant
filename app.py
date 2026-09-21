import os
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA


load_dotenv()

st.set_page_config(
    page_title="IntelliDocs",
    page_icon="📚",
    layout="wide"
)

st.title("📚 IntelliDocs")
st.subheader("GenAI Multi-PDF Research Assistant")

st.write(
    "Upload multiple PDF documents and ask questions based on their content."
)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("Please configure your OPENAI_API_KEY in the .env file.")
    st.stop()


uploaded_files = st.file_uploader(
    "Upload PDF documents",
    type=["pdf"],
    accept_multiple_files=True
)


if uploaded_files:

    all_text = ""

    for uploaded_file in uploaded_files:

        reader = PdfReader(uploaded_file)

        for page in reader.pages:
            text = page.extract_text()

            if text:
                all_text += text + "\n"

    if not all_text.strip():
        st.error("No readable text found in the uploaded PDFs.")
        st.stop()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_text(all_text)

    embeddings = OpenAIEmbeddings(
        api_key=api_key
    )

    vector_store = FAISS.from_texts(
        chunks,
        embedding=embeddings
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vector_store.as_retriever(
            search_kwargs={"k": 4}
        ),
        chain_type="stuff"
    )

    st.success(
        f"{len(uploaded_files)} PDF(s) processed successfully!"
    )

    question = st.text_input(
        "Ask a question about your documents:"
    )

    if question:

        with st.spinner("Searching documents..."):

            answer = qa_chain.invoke(
                {"query": question}
            )

        st.markdown("### 💡 Answer")
        st.write(answer["result"])
