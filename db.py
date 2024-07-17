import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from docx import Document
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from PyPDF2 import PdfReader
from typing import List
import databases
import sqlalchemy
import boto3

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
S3_BUCKET = os.getenv('S3_BUCKET')

DATABASE_URL = os.getenv('DATABASE_URL')  # Postgres URL from .env
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

documents = sqlalchemy.Table(
    "documents",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("filename", sqlalchemy.String, unique=True),
    sqlalchemy.Column("content", sqlalchemy.Text),
    sqlalchemy.Column("s3_url", sqlalchemy.String),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean, default=False),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

app = FastAPI()

vectors = None
llm_chain = None


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    user_message: str
    assistant_message: str


@app.on_event("startup")
async def startup():
    await database.connect()
    await initialize_vectors()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


async def initialize_vectors():
    global vectors, llm_chain
    query = documents.select().where(documents.c.is_active == True)
    rows = await database.fetch_all(query)
    if rows:
        doc_text = "".join([row["content"] for row in rows])
        doc_chunks = get_chunks(doc_text)
        vectors = get_vector(doc_chunks)
        llm_chain = get_llm_chain(vectors)


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
    for file in files:
        content = get_text([file])
        s3_url = upload_to_s3(file)
        query = documents.insert().values(
            filename=file.filename,
            content=content,
            s3_url=s3_url,
            is_active=False
        )
        await database.execute(query)
    await initialize_vectors()
    return {"message": "Files processed and stored successfully. You can now ask questions."}


def upload_to_s3(file):
    s3_key = file.filename
    s3_client.upload_fileobj(file.file, S3_BUCKET, s3_key)
    s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"
    return s3_url


@app.post("/set_active_file/")
async def set_active_file(filename: str):
    # Deactivate all files
    deactivate_query = documents.update().values(is_active=False)
    await database.execute(deactivate_query)

    # Activate the specified file
    activate_query = documents.update().where(documents.c.filename == filename).values(is_active=True)
    await database.execute(activate_query)

    await initialize_vectors()
    return {"message": f"File {filename} is now active."}


@app.post("/ask_question/", response_model=QuestionResponse)
async def ask_question(question_request: QuestionRequest):
    if not llm_chain:
        raise HTTPException(status_code=503, detail="Service not ready. Please try again later.")

    user_input = question_request.question
    bot_response = llm_chain({"question": user_input})

    chat_history = bot_response["chat_history"]
    user_message = chat_history[-2].content
    assistant_message = chat_history[-1].content

    return QuestionResponse(user_message=user_message, assistant_message=assistant_message)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
