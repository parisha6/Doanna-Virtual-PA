import argparse  # For command-line argument parsing
import textwrap  # For wrapping output text
import torch  # For tensor operations and GPU acceleration
import numpy as np  # For numerical operations
import pandas as pd  # For handling structured data
from sentence_transformers import SentenceTransformer, util  # For embeddings and similarity scoring
from transformers import AutoTokenizer, AutoModelForCausalLM  # For tokenization and LLM
from huggingface_hub import login  # For Hugging Face Hub authentication
import openai  # For OpenAI API calls

# Constants for API tokens
HF_TOKEN = <Hugging Face Token>
OPENAI_API_KEY = <OPENAI_API_KEY>

# Set device to CUDA if available
device = "cuda" if torch.cuda.is_available() else "cpu"

# Configure OpenAI API
openai.api_key = OPENAI_API_KEY

def print_wrapped(text: str, wrap_length: int = 80) -> None:
    """
    Print text wrapped at the specified line length.

    Args:
        text (str): The text to wrap and print.
        wrap_length (int): Maximum line length for wrapping. Default is 80.
    """
    wrapped_text = textwrap.fill(text, wrap_length)
    print(wrapped_text)

def retrieve_relevant_resources(query: str,
                                embeddings: torch.Tensor,
                                model: SentenceTransformer,
                                n_resources_to_return: int = 5):
    """
    Retrieve top-k relevant resources for a given query using embedding similarity.

    Args:
        query (str): The query string.
        embeddings (torch.Tensor): Pre-computed embeddings of resources.
        model (SentenceTransformer): Embedding model for encoding queries.
        n_resources_to_return (int): Number of resources to return. Default is 5.

    Returns:
        Tuple[torch.Tensor, torch.Tensor]: Scores and indices of the top-k resources.
    """
    query_embedding = model.encode(query, convert_to_tensor=True, device=embeddings.device)
    dot_scores = util.dot_score(query_embedding, embeddings)[0]
    scores, indices = torch.topk(dot_scores, k=n_resources_to_return)
    return scores, indices

def fetch_from_openai(query: str, model: str = "text-davinci-003", max_tokens: int = 256, temperature: float = 0.7) -> str:
    """
    Fetch context for a query from OpenAI's API.

    Args:
        query (str): Query string.
        model (str): OpenAI model to use. Default is "text-davinci-003".
        max_tokens (int): Maximum tokens in the response. Default is 256.
        temperature (float): Sampling temperature for response variability. Default is 0.7.

    Returns:
        str: OpenAI API response or an error message.
    """
    try:
        response = openai.Completion.create(
            model=model,
            prompt=f"Provide detailed context about the following query:\n\nQuery: {query}\n\nContext:",
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"[ERROR] OpenAI API call failed: {e}")
        return ""

def prompt_formatter(query: str, context_items: list, openai_context: str = "") -> str:
    """
    Format the query with context items and OpenAI-provided context.

    Args:
        query (str): The query string.
        context_items (list): Relevant context items.
        openai_context (str): Additional context from OpenAI.

    Returns:
        str: Formatted prompt string.
    """
    context = "- " + "\n- ".join([item["sentence_chunk"] for item in context_items])
    base_prompt = """Based on the following context items, please answer the query:
{context}

Additional context from OpenAI:
{openai_context}

User query: {query}
Answer:"""
    return base_prompt.format(context=context, openai_context=openai_context, query=query)

def ask(query: str,
        embeddings: torch.Tensor,
        tokenizer,
        model,
        pages_and_chunks: list,
        embedding_model: SentenceTransformer,
        temperature: float = 0.7,
        max_new_tokens: int = 512,
        format_answer_text: bool = True,
        return_answer_only: bool = True):
    """
    Process the query and generate an answer using relevant resources and LLM.

    Args:
        query (str): Query string.
        embeddings (torch.Tensor): Resource embeddings.
        tokenizer: Tokenizer for the LLM.
        model: LLM model.
        pages_and_chunks (list): Resource details as a list of dictionaries.
        embedding_model (SentenceTransformer): Embedding model.
        temperature (float): Sampling temperature. Default is 0.7.
        max_new_tokens (int): Max tokens for response. Default is 512.
        format_answer_text (bool): Whether to format the output text. Default is True.
        return_answer_only (bool): Whether to return only the answer. Default is True.

    Returns:
        str: Generated answer.
    """
    scores, indices = retrieve_relevant_resources(query, embeddings, embedding_model)
    context_items = [pages_and_chunks[i] for i in indices]
    openai_context = fetch_from_openai(query)
    prompt = prompt_formatter(query, context_items, openai_context)
    input_ids = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(**input_ids, temperature=temperature, do_sample=True, max_new_tokens=max_new_tokens)
    output_text = tokenizer.decode(outputs[0])
    if format_answer_text:
        output_text = output_text.replace(prompt, "").strip()
    if return_answer_only:
        return output_text
    return output_text, context_items

def parse_args():
    """
    Parse command-line arguments.

    Returns:
        Namespace: Parsed arguments containing the query.
    """
    parser = argparse.ArgumentParser(description="Query processing script")
    parser.add_argument('query', type=str, help="The query to ask the model")
    return parser.parse_args()

if __name__ == "__main__":
    print("[INFO] Loading resources...")
    text_chunks_and_embedding_df = pd.read_csv("text_chunks_and_embeddings_df.csv")
    text_chunks_and_embedding_df["embedding"] = text_chunks_and_embedding_df["embedding"].apply(
        lambda x: np.fromstring(x.strip("[]"), sep=" ")
    )
    pages_and_chunks = text_chunks_and_embedding_df.to_dict(orient="records")
    embeddings = torch.tensor(
        np.array(text_chunks_and_embedding_df["embedding"].tolist()), dtype=torch.float32
    ).to(device)

    print("[INFO] Initializing models...")
    embedding_model = SentenceTransformer("all-mpnet-base-v2", device=device)
    login(token=HF_TOKEN)
    model_id = "google/gemma-2b-it"
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=HF_TOKEN)
    llm_model = AutoModelForCausalLM.from_pretrained(model_id, token=HF_TOKEN).to(device)

    args = parse_args()
    query = args.query
    print(f"[INFO] Query: {query}")

    response = ask(query, embeddings, tokenizer, llm_model, pages_and_chunks, embedding_model)
    print("\n[INFO] Response:")
    print_wrapped(response)
