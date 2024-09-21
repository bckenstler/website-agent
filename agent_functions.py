import json
import os
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.endpoint import DEFAULT_TIMEOUT
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


def fetch_and_read(url: str) -> str:
    """
    Fetches a web page from the given URL and parses its content.

    Parameters:
        url (str): The URL of the web page to fetch.

    Returns:
        str: The text content of the web page, or None if an error occurs.
    """
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract text from the parsed HTML
        text = soup.get_text(separator='\n', strip=True)

        return text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the URL: {e}")
        return None


def post_to_lambda(subject: str, body: str, email: str, name: str, occupation: str, phone_number: str = None) -> dict:
    """
    Posts a request to an AWS Lambda function URL with the given payload.

    Parameters:
        subject (str): The subject of the request.
        body (str): The body content of the request.
        email (str): The email address to associate with the request.
        name (str): The name of the person making the request.
        occupation (str): The occupation of the person making the request.
        phone_number (str, optional): The phone number to include, if available.

    Returns:
        dict: A dictionary containing the response from the Lambda function,
              or an error message in case of failure.
    """
    # Define the payload based on the inputs
    payload = {
        "subject": subject,
        "body": body,
        "email": email,
        "name": name,
        "occupation": occupation
    }

    # Include the phone number if provided
    if phone_number:
        payload["phone_number"] = phone_number

    # Lambda Function URL
    lambda_url = "https://l3i2ysl3fp2qkei5cu4nxtguuu0nlqxt.lambda-url.us-east-1.on.aws/"

    # AWS Region
    region = "us-east-1"

    # Get AWS credentials from environment variables
    session = boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS"),
        aws_secret_access_key=os.environ.get("AWS_SECRET")
    )
    credentials = session.get_credentials()
    current_credentials = credentials.get_frozen_credentials()

    # Create an AWSRequest
    request = AWSRequest(
        method='POST',
        url=lambda_url,
        data=json.dumps(payload),
        headers={'Content-Type': 'application/json'}
    )

    # Sign the request using AWS SigV4Auth
    SigV4Auth(
        current_credentials,
        'lambda',
        region
    ).add_auth(request)

    # Convert AWSRequest to a format compatible with the 'requests' library
    prepared_request = requests.Request(
        method=request.method,
        url=request.url,
        headers=dict(request.headers),
        data=request.body
    ).prepare()

    # Send the request and handle the response
    session = requests.Session()
    try:
        response = session.send(prepared_request, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()  # Return the response as JSON
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while posting to Lambda: {e}")
        return {"error": str(e)}


def execute_required_function(func_name: str, arguments: dict):
    """
    Executes the function corresponding to the given func_name.

    Parameters:
        func_name (str): The name of the function to execute.
        arguments (dict): A dictionary of arguments required by the function.

    Returns:
        The result of the executed function, or None if no matching function is found.
    """
    if func_name == "send_email_to_Brad":
        return post_to_lambda(
            subject=arguments["subject"],
            body=arguments["body"],
            email=arguments["email"],
            name=arguments["name"],
            occupation=arguments["occupation"],
            phone_number=arguments.get("phone_number", "")
        )
    elif func_name == "fetch_project_material_from_url":
        return fetch_and_read(arguments["url"])
    else:
        print(f"No function found with the name: {func_name}")
        return None
