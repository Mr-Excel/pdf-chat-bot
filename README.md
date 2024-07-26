
# Document Q&A Bot

Welcome to the Document Q&A Bot! This application allows you to upload `.pdf` and `.docx` files and ask questions based on the content of those documents using OpenAI's GPT-3.5-turbo model. The application leverages FastAPI for the backend, FAISS for vector search, and LangChain for conversational retrieval.

## Features

- Upload `.pdf` and `.docx` files
- Process and extract text from the uploaded documents
- Split the text into manageable chunks
- Create embeddings using OpenAI's API
- Store embeddings in a FAISS vector store
- Ask questions based on the content of the documents
- Maintain conversation context for better Q&A

## Installation

Follow these steps to set up and run the application:

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Clone the Repository

```sh
git clone https://github.com/yourusername/document-qa-bot.git
cd document-qa-bot
```

### Create a Virtual Environment

```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```sh
pip install -r requirements.txt
```

### Set Up Environment Variables

Create a `.env` file in the root directory and add your OpenAI API key:

```sh
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Start the FastAPI Server

```sh
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### Upload Files

You can upload `.pdf` and `.docx` files by making a POST request to `/upload_files/`. Use tools like Postman or `curl` to upload files.

#### Example using `curl`:

```sh
curl -X POST "http://127.0.0.1:8000/upload_files/" -F "files=@path_to_your_file1.pdf" -F "files=@path_to_your_file2.docx"
```

### Ask Questions

After uploading files, you can ask questions by making a POST request to `/ask_question/` with your question in the request body.

#### Example using `curl`:

```sh
curl -X POST "http://127.0.0.1:8000/ask_question/" -H "Content-Type: application/json" -d '{"question": "What is the main topic of the document?"}'
```

### Response

The response will include the user's message and the assistant's message.

```json
{
  "user_message": "What is the main topic of the document?",
  "assistant_message": "The main topic of the document is..."
}
```

## API Endpoints

### POST `/upload_files/`

- Description: Upload `.pdf` and `.docx` files for processing.
- Parameters: `files` - List of files to upload.
- Response: Message indicating the files were processed successfully.

### POST `/ask_question/`

- Description: Ask a question based on the content of the uploaded documents.
- Parameters: `question` - The question to ask.
- Response: JSON object containing the user's message and the assistant's message.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://github.com/hwchase17/langchain)
- [OpenAI](https://www.openai.com/)
- [FAISS](https://github.com/facebookresearch/faiss)

## Contact

For any questions or suggestions, please contact us at [your-email@example.com].

---

Thank you for using Document Q&A Bot! We hope this tool makes your document analysis easier and more efficient.

---

## Connect with Mr-Excel

<p align="center">
  <a href="https://www.linkedin.com/in/ahmad-raza-0b134b149/">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
  <a href="https://github.com/mr-excel">
    <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
  <a href="mailto:ahmadraza600@gmail.com">
    <img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email">
  </a>
</p>

<p align="center">
  <img src="https://visitor-badge.laobi.icu/badge?page_id=mr-excel.visitor-badge" alt="Visitor Badge">
</p>

---

<p align="center">
  Made with ❤️ by Mr-Excel
</p>
