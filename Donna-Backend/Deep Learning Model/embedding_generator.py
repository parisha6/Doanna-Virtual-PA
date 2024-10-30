import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def generate_and_save_embeddings(sentences, text_chunks, vector_db=None, model_name="all-mpnet-base-v2", device="cuda", batch_size=32, embeddings_file_path="text_chunks_and_embeddings_df.csv"):
    """
    Generate embeddings for sentences and text chunks using SentenceTransformer, 
    and optionally save them to a specified vector database and a CSV file.

    Args:
        sentences (list of str): List of sentences to be embedded.
        text_chunks (list of dict): List of dictionaries with text chunks.
            Each dictionary should contain a key "sentence_chunk" representing the text.
        vector_db (optional): A vector database instance where embeddings will be saved.
        model_name (str): Name of the pre-trained SentenceTransformer model to use.
        device (str): Device to run the embedding model on. Default is "cuda".
        batch_size (int): Batch size for embedding the text chunks.
        embeddings_file_path (str): File path to save the embeddings as CSV.

    Returns:
        embeddings_dict (dict): Dictionary mapping sentences to their embeddings.
        text_chunk_embeddings (torch.Tensor): Tensor of embeddings for text chunks.
    """
    # Load and set up the embedding model
    embedding_model = SentenceTransformer(model_name_or_path=model_name, device="cpu")
    embedding_model.to(device)

    # Encode sentences and create a dictionary of embeddings
    embeddings = embedding_model.encode(sentences)
    embeddings_dict = dict(zip(sentences, embeddings))

    # Add embeddings for each text chunk in 'text_chunks' and optionally save to vector database
    for item in tqdm(text_chunks):
        item["embedding"] = embedding_model.encode(item["sentence_chunk"])

        # If a vector database is specified, store the embedding there
        if vector_db:
            vector_db.insert(item["sentence_chunk"], item["embedding"])

    # Embed all text chunks in batches and convert to tensor
    text_chunk_embeddings = embedding_model.encode(
        [chunk["sentence_chunk"] for chunk in text_chunks],
        batch_size=batch_size,
        convert_to_tensor=True
    )

    # Save embeddings and text chunks to a CSV file
    text_chunks_and_embeddings_df = pd.DataFrame(text_chunks)
    text_chunks_and_embeddings_df.to_csv(embeddings_file_path, index=False)

    return embeddings_dict, text_chunk_embeddings
