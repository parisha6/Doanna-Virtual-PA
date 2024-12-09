import os
import re
from tqdm.auto import tqdm  # For progress bars
import fitz  # PyMuPDF library for working with PDF files
import pandas as pd  # For creating and manipulating dataframes
from spacy.lang.en import English  # NLP library for English language processing
from sentence_transformers import SentenceTransformer  # For embeddings


def text_formatter(text: str) -> str:
    """
    Cleans and formats the input text by removing unnecessary whitespace and line breaks.

    Args:
        text (str): The input text to format.

    Returns:
        str: The formatted text.
    """
    return text.replace("\n", " ").strip()


def open_and_read_pdf(directory_path: str) -> list[dict]:
    """
    Reads all PDF files in the specified directory, extracts text from each page,
    and collects statistics about the extracted content.

    Args:
        directory_path (str): The path to the directory containing PDF files.

    Returns:
        list[dict]: A list of dictionaries containing text and statistics for each page.
    """
    pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
    pages_and_texts = []

    for pdf_file in tqdm(pdf_files, desc="Processing all PDFs"):
        pdf_path = os.path.join(directory_path, pdf_file)
        doc = fitz.open(pdf_path)

        for page_number, page in tqdm(
            enumerate(doc, start=1),
            desc=f"Processing {pdf_file}",
            total=len(doc)
        ):
            text = page.get_text()
            formatted_text = text_formatter(text)

            pages_and_texts.append({
                "filename": pdf_file,
                "page_number": page_number,
                "page_char_count": len(formatted_text),
                "page_word_count": len(formatted_text.split()),
                "page_sentence_count_raw": len(formatted_text.split(". ")),
                "page_token_count": len(formatted_text) // 4,  # Approximate token count
                "text": formatted_text
            })

    return pages_and_texts


def split_list(input_list: list[str], slice_size: int) -> list[list[str]]:
    """
    Splits a list into smaller sublists of a specified size.

    Args:
        input_list (list): The list to split.
        slice_size (int): The size of each sublist.

    Returns:
        list[list[str]]: A list of sublists.
    """
    return [input_list[i:i + slice_size] for i in range(0, len(input_list), slice_size)]


def process_pdf_data(directory_path: str, num_sentence_chunk_size: int, min_token_length: int) -> pd.DataFrame:
    """
    Processes PDF files in the directory to extract text, split it into sentence chunks,
    and generate statistics for each chunk.

    Args:
        directory_path (str): Path to the directory containing PDF files.
        num_sentence_chunk_size (int): Number of sentences per chunk.
        min_token_length (int): Minimum token length to filter chunks.

    Returns:
        pd.DataFrame: A dataframe containing processed sentence chunks and their statistics.
    """
    pages_and_texts = open_and_read_pdf(directory_path)

    nlp = English()
    nlp.add_pipe("sentencizer")

    for item in tqdm(pages_and_texts, desc="Processing sentences with spaCy"):
        sentences = [str(sentence) for sentence in nlp(item["text"]).sents]
        item["sentences"] = sentences
        item["page_sentence_count_spacy"] = len(sentences)

    for item in pages_and_texts:
        sentence_chunks = split_list(item["sentences"], num_sentence_chunk_size)
        item["sentence_chunks"] = sentence_chunks
        item["num_chunks"] = len(sentence_chunks)

    pages_and_chunks = []
    for item in pages_and_texts:
        for sentence_chunk in item["sentence_chunks"]:
            sentence_text = "".join(sentence_chunk).replace("  ", " ").strip()
            formatted_text = re.sub(r'\.([A-Z])', r'. \1', sentence_text)

            pages_and_chunks.append({
                "page_number": item["page_number"],
                "sentence_chunk": formatted_text,
                "chunk_char_count": len(formatted_text),
                "chunk_word_count": len(formatted_text.split()),
                "chunk_token_count": len(formatted_text) // 4
            })

    df = pd.DataFrame(pages_and_chunks)
    df = df[df["chunk_token_count"] > min_token_length]  # Filter based on token length

    return df


def generate_embeddings(df: pd.DataFrame, model_name: str = "all-mpnet-base-v2") -> pd.DataFrame:
    """
    Generates sentence embeddings for the chunks in the dataframe.

    Args:
        df (pd.DataFrame): Dataframe containing sentence chunks.
        model_name (str): Pre-trained model name for generating embeddings.

    Returns:
        pd.DataFrame: Updated dataframe with generated embeddings.
    """
    embedding_model = SentenceTransformer(model_name)
    embedding_model.to("cuda")  # Use GPU if available

    text_chunks = df["sentence_chunk"].tolist()
    embeddings = embedding_model.encode(
        text_chunks,
        batch_size=32,
        convert_to_tensor=True
    )
    df["embedding"] = embeddings.tolist()
    return df


def main():
    """
    Main function to process PDF files, extract text, split into chunks, generate embeddings,
    and save the results to a CSV file.
    """
    directory_path = r"/home/mishr199/Donna_PFW_Docs"
    num_sentence_chunk_size = 30  # Number of sentences per chunk
    min_token_length = 3  # Minimum token length for filtering

    print("[INFO] Processing PDF data...")
    processed_df = process_pdf_data(directory_path, num_sentence_chunk_size, min_token_length)

    print("[INFO] Generating embeddings...")
    result_df = generate_embeddings(processed_df)

    save_path = "text_chunks_and_embeddings_df.csv"
    print(f"[INFO] Saving results to {save_path}...")
    result_df.to_csv(save_path, index=False)


if __name__ == "__main__":
    main()
