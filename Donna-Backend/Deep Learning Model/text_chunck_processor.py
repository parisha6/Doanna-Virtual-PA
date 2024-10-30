from typing import List, Dict, Any
import pandas as pd
from tqdm import tqdm
import re

# Define the default split size for sentence chunks
DEFAULT_CHUNK_SIZE = 10
MIN_TOKEN_LENGTH = 30  # Minimum token length to filter chunks

def split_list(input_list: List[str], slice_size: int = DEFAULT_CHUNK_SIZE) -> List[List[str]]:
    """
    Splits a list into smaller chunks of a specified size.

    This function takes a list of strings (or any items) and splits it into 
    smaller lists (chunks) of a specified slice size. If the list size is not 
    perfectly divisible by the slice size, the last chunk will contain the remaining items.

    Parameters
    ----------
    input_list : List[str]
        The list to be split into chunks.
    slice_size : int, optional
        The size of each chunk, defaulting to 10.

    Returns
    -------
    List[List[str]]
        A list of lists, where each sublist represents a chunk of the original list.
    """
    return [input_list[i:i + slice_size] for i in range(0, len(input_list), slice_size)]

def process_pages_and_texts(pages_and_texts: List[Dict[str, Any]], chunk_size: int = DEFAULT_CHUNK_SIZE) -> pd.DataFrame:
    """
    Processes a list of dictionaries with sentences and adds chunked sentences and chunk counts.

    This function iterates over a list of dictionaries containing sentences, splitting 
    each list of sentences into chunks of a specified size, and adds the chunked sentences 
    and their counts to each dictionary. Finally, it converts the list of dictionaries 
    into a pandas DataFrame.

    Parameters
    ----------
    pages_and_texts : List[Dict[str, Any]]
        A list of dictionaries, each containing a "sentences" key with a list of sentences.
    chunk_size : int, optional
        The size of each sentence chunk, defaulting to 10.

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame with chunked sentences and their counts.
    """
    for item in tqdm(pages_and_texts):
        item["sentence_chunks"] = split_list(input_list=item["sentences"], slice_size=chunk_size)
        item["num_chunks"] = len(item["sentence_chunks"])
    return pd.DataFrame(pages_and_texts)

def process_and_filter_chunks(pages_and_texts: List[Dict[str, Any]], 
                              chunk_size: int = DEFAULT_CHUNK_SIZE, 
                              min_token_length: int = MIN_TOKEN_LENGTH) -> List[Dict[str, Any]]:
    """
    Processes pages and texts by splitting them into sentence chunks, 
    calculating chunk statistics, and filtering out chunks with fewer tokens than specified.

    Parameters
    ----------
    pages_and_texts : List[Dict[str, Any]]
        A list of dictionaries, each containing a "sentences" key with a list of sentences.
    chunk_size : int, optional
        The size of each sentence chunk, defaulting to 10.
    min_token_length : int, optional
        The minimum number of tokens required for a chunk to be retained, defaulting to 30.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries representing chunks that meet the minimum token count requirement.
    """
    # Process pages and create a DataFrame with chunks
    df = process_pages_and_texts(pages_and_texts, chunk_size=chunk_size)
    pages_and_chunks = []
    
    # Split each chunk into its own item with calculated stats
    for item in tqdm(df.to_dict(orient="records")):
        for sentence_chunk in item["sentence_chunks"]:
            chunk_dict = {
                "page_number": item.get("page_number", None),
                "sentence_chunk": re.sub(r'\.([A-Z])', r'. \1', 
                                         "".join(sentence_chunk).replace("  ", " ").strip()),
                "chunk_char_count": len("".join(sentence_chunk)),
                "chunk_word_count": len("".join(sentence_chunk).split(" ")),
                "chunk_token_count": len("".join(sentence_chunk)) / 4  # 1 token ~ 4 chars
            }
            pages_and_chunks.append(chunk_dict)

    # Filter chunks based on minimum token length
    filtered_chunks = [chunk for chunk in pages_and_chunks if chunk["chunk_token_count"] > min_token_length]
    return filtered_chunks
