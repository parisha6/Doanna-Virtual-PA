from typing import List, Dict
import pandas as pd
from spacy.lang.en import English
from tqdm import tqdm

def process_text_pages(pages_and_texts: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Process a list of page texts to split them into sentences and count them using spaCy's sentencizer.

    Args:
        pages_and_texts (List[Dict[str, str]]): A list of dictionaries containing page texts under the 'text' key.

    Returns:
        pd.DataFrame: A DataFrame with processed data, including sentence splits and sentence counts.
    """
    # Initialize spaCy English pipeline with sentencizer
    nlp = English()
    nlp.add_pipe("sentencizer")
    
    # Process each text, split into sentences, and count sentences
    for item in tqdm(pages_and_texts, desc="Processing pages"):
        # Apply NLP pipeline to split into sentences
        item["sentences"] = [str(sentence) for sentence in nlp(item["text"]).sents]
        
        # Count the sentences
        item["page_sentence_count_spacy"] = len(item["sentences"])

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(pages_and_texts)
    return df
