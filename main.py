import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from docx import Document
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from PyPDF2 import PdfReader
from typing import List

os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')

app = FastAPI()


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    user_message: str
    assistant_message: str


def parse_docx(data):
    document = Document(docx=data)
    content = ""
    for para in document.paragraphs:
        content += para.text
    return content


def get_text(docs):
    doc_text = ""
    for doc in docs:
        if doc.filename.endswith(".pdf"):
            pdf_reader = PdfReader(doc.file)
            for each_page in pdf_reader.pages:
                doc_text += each_page.extract_text()
            doc_text += "\n"
        elif doc.filename.endswith(".docx"):
            doc_text += parse_docx(data=doc.file.read())
    return doc_text


def get_chunks(data):
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=250, length_function=len
    )
    text_chunks = text_splitter.split_text(data)
    return text_chunks


def get_vector(chunks):
    return FAISS.from_texts(texts=chunks, embedding=OpenAIEmbeddings())


def get_llm_chain(vectors):
    llm_chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7),
        retriever=vectors.as_retriever(),
        memory=ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        ),
    )
    return llm_chain


@app.post("/upload_files/")
async def upload_files(files: List[UploadFile] = File(...)):
    doc_text = get_text(files)
    doc_chunks = get_chunks(doc_text)
    vectors = get_vector(doc_chunks)
    llm_chain = get_llm_chain(vectors)
    app.state.llm_chain = llm_chain
    return {"message": "Files processed successfully. You can now ask questions."}


@app.post("/ask_question/", response_model=QuestionResponse)
async def ask_question(question_request: QuestionRequest):
    if not hasattr(app.state, "llm_chain"):
        raise HTTPException(status_code=400, detail="Please upload files before asking questions.")

    llm_chain = app.state.llm_chain
    user_input = question_request.question
    bot_response = llm_chain({"question": user_input})

    chat_history = bot_response["chat_history"]
    user_message = chat_history[-2].content
    assistant_message = chat_history[-1].content

    return QuestionResponse(user_message=user_message, assistant_message=assistant_message)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)