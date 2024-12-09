import requests
from bs4 import BeautifulSoup
from docx import Document

def fetch_webpage_content(url):
    """
    Fetches the content of a webpage given its URL.
    
    Parameters:
    url (str): The URL of the webpage to fetch.
    
    Returns:
    str: The text content of the webpage.
    """
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text from the webpage, removing unwanted tags like script, style, etc.
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Get text from the parsed HTML and clean extra whitespaces
            return soup.get_text(strip=True)
        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def save_to_word(content, filename):
    """
    Saves the extracted content into a Word document.
    
    Parameters:
    content (str): The content to be written into the Word file.
    filename (str): The name of the Word file to save the content.
    """
    # Create a new Document
    doc = Document()
    
    # Add the content to the Word document
    doc.add_paragraph(content)
    
    # Save the document with the given filename
    doc.save(filename)
    print(f"Content successfully saved to {filename}")


def main():
    """
    Main function that coordinates the extraction of webpage content and saving it to a Word file.
    """
    url = input("Enter the URL of the webpage: ")
    
    # Fetch the content of the webpage
    content = fetch_webpage_content(url)
    
    if content:
        # Ask for the output Word filename
        filename = input("Enter the filename to save the Word document (e.g., output.docx): ")
        
        # Save the content to the Word file
        save_to_word(content, filename)


if __name__ == '__main__':
    main()
