from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/run-python-script', methods=['POST'])
def run_python_script():
    """
    Endpoint to execute a Python script with input provided via a POST request.

    The endpoint expects a JSON payload with a key 'message', which contains the 
    input text to be passed as an argument to the external Python script.

    Returns:
        JSON: A response containing the script's standard output, error output, 
              and return code. If an exception occurs, a JSON error message 
              with a 500 status code is returned.
    """
    try:
        # Get the input text from the request
        input_text = request.json.get('message', '')

        # Execute the Python script using subprocess and pass the input text as an argument
        result = subprocess.run(
            ['python3', 'DonnaRagCMD.py', input_text],  # Pass the input text as an argument
            capture_output=True,
            text=True
        )

        # Return the result of the script execution
        return jsonify({
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        # Handle and log any exceptions
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    """
    Entry point for the Flask application.

    Runs the Flask development server in debug mode.
    """
    app.run(debug=True)
