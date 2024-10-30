import random
import torch
import numpy as np
import pandas as pd
from time import perf_counter as timer
import fitz  # pymupdf library
import matplotlib.pyplot as plt
from sentence_transformers import util, SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"

def load_embeddings_from_csv(file_path: str) -> tuple:
    """
    Load embeddings from a CSV file and convert them into a PyTorch tensor.

    Args:
        file_path (str): The path to the CSV file containing text chunks and embeddings.

    Returns:
        tuple: A tensor of embeddings and a list of text chunks as dictionaries.
    """
    df = pd.read_csv(file_path)
    df["embedding"] = df["embedding"].apply(lambda x: np.fromstring(x.strip("[]"), sep=" "))
    embeddings = torch.tensor(np.stack(df["embedding"].tolist(), axis=0), dtype=torch.float32).to(device)
    return embeddings, df.to_dict(orient="records")

def initialize_model(model_name: str) -> SentenceTransformer:
    """
    Initialize and return a SentenceTransformer model.

    Args:
        model_name (str): The name or path of the model to load.

    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    return SentenceTransformer(model_name_or_path=model_name, device=device)

def embed_query(query: str, model: SentenceTransformer) -> torch.Tensor:
    """
    Embed the input query using the provided model.

    Args:
        query (str): The query to embed.
        model (SentenceTransformer): The embedding model.

    Returns:
        torch.Tensor: The embedded query as a tensor.
    """
    return model.encode(query, convert_to_tensor=True).to(device)

def retrieve_relevant_resources(query: str,
                                embeddings: torch.Tensor,
                                model: SentenceTransformer,
                                n_resources_to_return: int = 5,
                                print_time: bool = True) -> tuple:
    """
    Embed a query and return the top k scores and indices from embeddings.

    Args:
        query (str): The query to search for.
        embeddings (torch.Tensor): The embeddings to search through.
        model (SentenceTransformer): The embedding model.
        n_resources_to_return (int, optional): Number of top results to return. Defaults to 5.
        print_time (bool, optional): Whether to print the time taken for scoring. Defaults to True.

    Returns:
        tuple: Scores and indices of the top resources.
    """
    query_embedding = embed_query(query, model)

    start_time = timer()
    dot_scores = util.dot_score(query_embedding, embeddings)[0]
    end_time = timer()

    if print_time:
        print(f"[INFO] Time taken to get scores on {len(embeddings)} embeddings: {end_time - start_time:.5f} seconds.")

    scores, indices = torch.topk(input=dot_scores, k=n_resources_to_return)
    return scores, indices

def reindex_pages_and_chunks(pages_and_chunks: list) -> list:
    """
    Reindex the pages_and_chunks list to ensure sequential indexing.

    Args:
        pages_and_chunks (list): The list of text chunks and their corresponding data.

    Returns:
        list: The reindexed list of pages_and_chunks.
    """
    reindexed_chunks = [{**chunk, "new_index": idx} for idx, chunk in enumerate(pages_and_chunks)]
    return reindexed_chunks

def print_top_results_and_scores(query: str,
                                 embeddings: torch.Tensor,
                                 pages_and_chunks: list,
                                 n_resources_to_return: int = 5):
    """
    Find relevant passages given a query and print them out along with their scores.

    Args:
        query (str): The query to search for.
        embeddings (torch.Tensor): The embeddings to search through.
        pages_and_chunks (list): A list of dictionaries containing text chunks and page numbers.
        n_resources_to_return (int, optional): Number of top results to return. Defaults to 5.
    """
    scores, indices = retrieve_relevant_resources(query=query,
                                                  embeddings=embeddings,
                                                  model=embedding_model,
                                                  n_resources_to_return=n_resources_to_return)

    for score, idx in zip(scores, indices):
        print(f"Score: {score:.4f}")
        print("Text:")
        print_wrapped(pages_and_chunks[idx]["sentence_chunk"])
        print(f"Page number: {pages_and_chunks[idx]['page_number']}\n")

def visualize_page_from_pdf(pdf_path: str, page_number: int):
    """
    Load and display a page from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.
        page_number (int): The page number to load (1-based).
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number - 1)  # fitz uses 0-based indexing

    img = page.get_pixmap(dpi=300)
    img_array = np.frombuffer(img.samples_mv, dtype=np.uint8).reshape((img.h, img.w, img.n))
    
    plt.figure(figsize=(13, 10))
    plt.imshow(img_array)
    plt.title(f"Query: '{query}' | Most relevant page:")
    plt.axis("off")
    plt.show()
    
    doc.close()

def main():
    """
    Main function to execute the overall logic of loading embeddings,
    initializing the model, processing the query, and visualizing results.
    """
    # Load embeddings and initialize the model
    embeddings, pages_and_chunks = load_embeddings_from_csv("text_chunks_and_embeddings_df.csv")
    embedding_model = initialize_model("all-mpnet-base-v2")

    # Reindex pages and chunks
    pages_and_chunks = reindex_pages_and_chunks(pages_and_chunks)

    # Define and embed the query
    query = input("PLease provide an input")
    print(f"Query: {query}")

    # Print top results
    print_top_results_and_scores(query, embeddings, pages_and_chunks)

    # Visualize the most relevant page (assuming the first result is the most relevant)
    top_k_indices = retrieve_relevant_resources(query, embeddings, embedding_model, n_resources_to_return=5)[1]
    most_relevant_page = pages_and_chunks[top_k_indices[0]]["page_number"]
    visualize_page_from_pdf("human-nutrition-text.pdf", most_relevant_page)

if __name__ == "__main__":
    main()
