from flask import Blueprint, render_template, request, session, redirect, url_for
from app.chat.chat_utils import ask_openai
import fitz
import os
from docx import Document
from PIL import Image
import pytesseract

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat/<filename>", methods=["GET", "POST"])
def chat(filename):
    uploads_dir = os.path.join("app", "static", "uploads")
    file_path = os.path.join(uploads_dir, filename)

    file_text = extract_text_from_file(file_path)

    answer = None
    question = ""

    if request.method == "POST":
        question = request.form.get("question")
        answer = ask_openai(question, file_text)

    return render_template("chat.html", filename=filename, question=question, answer=answer)


@chat_bp.route("/project-chat", methods=["GET", "POST"])
def project_chat():
    uploads_dir = os.path.join("app", "static", "uploads")
    all_files = os.listdir(uploads_dir)
    selected_file = request.form.get("selected_file")
    combined_text = ""

    if request.method == "POST" and request.form.get("clear_chat"):
        session.pop("chat_history", None)
        return redirect(url_for('chat.project_chat'))

    if selected_file:
        path = os.path.join(uploads_dir, selected_file)
        combined_text = extract_text_from_file(path)
    else:
        for filename in all_files:
            path = os.path.join(uploads_dir, filename)
            combined_text += f"\n\n--- {filename} ---\n" + extract_text_from_file(path)

    chat_history = session.get("chat_history", [])
    if request.method == "POST" and request.form.get("question"):
        question = request.form.get("question")
        answer = ask_openai(question, combined_text)
        chat_history.append({"question": question, "answer": answer})
        session["chat_history"] = chat_history

    return render_template("project_chat.html", chat_history=chat_history, files=all_files, selected_file=selected_file)


def extract_text_from_file(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if not os.path.getsize(path):
            return "⚠️ File is empty."

        if ext == ".pdf":
            return extract_text_from_pdf(path)
        elif ext == ".docx":
            return extract_text_from_docx(path)
        elif ext == ".txt":
            return extract_text_from_txt(path)
        elif ext in [".png", ".jpg", ".jpeg"]:
            return extract_text_from_image(path)
        else:
            return "⚠️ Unsupported file type."
    except Exception as e:
        return f"⚠️ Error reading file: {e}"


def extract_text_from_pdf(path):
    doc = fitz.open(path)
    return "\n".join([page.get_text() for page in doc])


def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_text_from_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text_from_image(path):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    img = Image.open(path)
    return pytesseract.image_to_string(img)
