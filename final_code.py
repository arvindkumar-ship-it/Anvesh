import os
import httpx
import json
import time
from functools import wraps
from typing import Tuple, Union
from dotenv import load_dotenv

def safe_get(
    data: dict | list | None,
    *keys,
    default=None
):
    """
    Safely access nested dict/list without KeyError/IndexError.
    (Same as EMPTY_RESPONSE template — reuse)
    """
    if data is None:
        return default
    try:
        result = data
        for key in keys:
            if result is None:
                return default
            elif isinstance(result, dict):
                result = result.get(key, default)
            elif isinstance(result, list):
                if not isinstance(key, int):
                    return default
                if not (-len(result) <= key < len(result)):
                    return default
                result = result[key]
            else:
                return default
        return result
    except Exception:
        return default


def check_nested_errors(
    data: Union[dict, list, None],
    endpoint: str = ""
) -> Tuple[bool, str]:
    """
    Check if HTTP 200 response contains hidden errors.

    Returns: (has_error: bool, error_message: str)

    Common patterns:
    {"success": false, "message": "..."}
    {"status": "error", "error": "..."}
    {"error": {"code": 1042, "message": "..."}}
    """
    if data is None or not isinstance(data, dict):
        return False, ""

    # Pattern 1: success field
    if data.get("success") is False:
        msg = (
            data.get("message")
            or data.get("error")
            or "Request failed"
        )
        return True, str(msg)

    # Pattern 2: status field
    status = data.get("status", "")
    if str(status).lower() in ["error", "failed", "failure"]:
        msg = (
            data.get("message")
            or data.get("error")
            or f"Status: {status}"
        )
        return True, str(msg)

    # Pattern 3: error field exists and is truthy
    error_field = data.get("error")
    if error_field:
        if isinstance(error_field, dict):
            msg = error_field.get("message", str(error_field))
        else:
            msg = str(error_field)
        return True, msg

    # Pattern 4: code field indicating error (4xx range)
    code = data.get("code", 0)
    if isinstance(code, int) and 400 <= code < 600:
        msg = data.get("message", f"Error code: {code}")
        return True, msg

    return False, ""


def make_request_with_retry(
    client,
    method: str,
    url: str,
    max_retries: int = 3,
    timeout=10,
    **kwargs
):
    """
    Make HTTP request with timeout retry.

    httpx.TimeoutException → wait → retry
    httpx.ConnectError → fail immediately (server unreachable)
    """
    for attempt in range(max_retries):
        try:
            response = client.request(method, url, timeout=timeout, **kwargs)
            return response

        except httpx.TimeoutException:
            wait = 2 ** attempt
            # Exponential: 1s, 2s, 4s
            print(
                f"Timeout on attempt {attempt+1}. "
                f"Waiting {wait}s..."
            )
            if attempt < max_retries - 1:
                time.sleep(wait)

        except httpx.ConnectError as e:
            print(f"Connection failed: {e}")
            print(f"Check URL: {url}")
            raise

    raise httpx.TimeoutException(
        f"All {max_retries} attempts timed out for {url}"
    )


def fetch_all_pages(
    client,
    url: str,
    headers: dict,
    params: dict = {},
    data_key: str = "data",
    max_pages: int = 100
) -> list:
    """
    Fetch all pages from a paginated endpoint.

    Supports multiple pagination styles:
    - cursor-based: {"next_cursor": "abc123"}
    - page-based: {"page": 2, "has_more": true}
    - URL-based: {"next": "https://api.../page=2"}
    """
    all_items = []
    current_url = url
    page_num = 1

    while current_url and page_num <= max_pages:

        response = make_request_with_retry(client, 'GET', current_url, headers=headers, params=params if page_num == 1 else {})
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            # Direct array response → no pagination
            all_items.extend(data)
            break

        elif isinstance(data, dict):
            # Extract items
            items = (
                data.get(data_key)
                or data.get("items")
                or data.get("results")
                or data.get("records")
                or []
            )
            all_items.extend(items)

            # Next page determine karo
            current_url = (
                data.get("next")
                or data.get("next_url")
                or data.get("next_page_url")
                or None
            )

            # Cursor-based pagination
            cursor = data.get("next_cursor") or data.get("cursor")
            if cursor and not current_url:
                params["cursor"] = cursor
                # URL same, cursor param update

            # has_more check
            has_more = data.get("has_more", False)
            if not has_more and not current_url and not cursor:
                break

        page_num += 1
        print(f"  Page {page_num-1} fetched, "
              f"total so far: {len(all_items)}")

    if page_num > max_pages:
        print(f"Warning: Stopped at {max_pages} pages limit")

    return all_items


def safe_parse_response(
    response,
    endpoint: str = ""
) -> dict | list | None:
    """
    Safely parse API response.
    Handles: empty body, null, non-JSON, empty dict/list.
    """
    # Empty body check
    if not response.content:
        print(f"Warning: Empty response body from {endpoint}")
        return None

    # JSON parse attempt
    try:
        data = response.json()
    except Exception:
        print(f"Warning: Non-JSON response from {endpoint}")
        print(f"Raw response: {response.text[:200]}")
        return None

    # Null check
    if data is None:
        print(f"Warning: Null response from {endpoint}")
        return None

    return data


def handle_auth_error(
    response,
    endpoint: str = ""
) -> bool:
    """
    Check if response is 401 auth error.
    Returns True if auth failed (caller should stop).
    """
    if response.status_code == 401:
        error_data = {}
        try:
            error_data = safe_parse_response(response)
        except Exception:
            pass

        error_msg = (
            error_data.get("error")
            or error_data.get("message")
            or "Unauthorized"
        )
        print(f"Auth error at {endpoint}: {error_msg}")
        print("Check API key/token in .env file")
        return True  # Auth failed

    return False  # Auth OK


def retry_on_rate_limit(
    max_retries: int = 3,
    backoff_factor: int = 2
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                response = func(*args, **kwargs)

                if response.status_code == 429:
                    retry_after = int(
                        response.headers.get(
                            "Retry-After",
                            backoff_factor ** (attempt + 1)
                        )
                    )
                    print(
                        f"Rate limited. "
                        f"Waiting {retry_after}s "
                        f"(attempt {attempt+1}/{max_retries})..."
                    )
                    time.sleep(retry_after)
                    continue

                return response

            raise Exception(
                f"Max retries ({max_retries}) exceeded. "
                f"Rate limit persists."
            )
        return wrapper
    return decorator


@retry_on_rate_limit()
def create_pet_impl(name: str, status: str) -> httpx.Response:
    client = httpx.Client(timeout=httpx.Timeout(30.0))
    url = "https://petstore.swagger.io/v2/pet"
    headers = {
        'Content-Type': 'application/json',
        'api_key': os.getenv("API_KEY")
    }
    data = {
        "name": name,
        "status": status
    }
    return make_request_with_retry(client, 'POST', url, max_retries=5, headers=headers, json=data)


def create_pet(name: str, status: str) -> dict:
    response = create_pet_impl(name, status)
    if handle_auth_error(response, "create_pet"):
        return None
    data = safe_parse_response(response, "create_pet")
    if data is None:
        return None
    has_err, err_msg = check_nested_errors(data, "create_pet")
    if has_err:
        print(f"Error in create_pet response: {err_msg}")
        return None
    return safe_get(data, "id")


@retry_on_rate_limit()
def find_pets_by_status_impl(status: list) -> list:
    url = "https://petstore.swagger.io/v2/pet/findByStatus"
    headers = {
        'Content-Type': 'application/json',
        'api_key': os.getenv("API_KEY")
    }
    client = httpx.Client(timeout=httpx.Timeout(30.0))
    return fetch_all_pages(client, url, headers=headers, params={'status': status})


def find_pets_by_status(status: list) -> dict:
    data = find_pets_by_status_impl(status)
    if data is None:
        return None
    # Even though fetch_all_pages returns a list, some APIs may return a dict with error info
    if isinstance(data, (dict, list)):
        has_err, err_msg = check_nested_errors(data, "find_pets_by_status")
        if has_err:
            print(f"Error in find_pets_by_status response: {err_msg}")
            return None
    return data


@retry_on_rate_limit()
def get_pet_impl(pet_id: int) -> httpx.Response:
    url = f"https://petstore.swagger.io/v2/pet/{pet_id}"
    headers = {
        'Content-Type': 'application/json',
        'api_key': os.getenv("API_KEY")
    }
    client = httpx.Client(timeout=httpx.Timeout(30.0))
    return make_request_with_retry(client, 'GET', url, headers=headers)


def get_pet(pet_id: int) -> dict:
    response = get_pet_impl(pet_id)
    if handle_auth_error(response, "get_pet"):
        return None
    data = safe_parse_response(response, "get_pet")
    if data is None:
        return None
    has_err, err_msg = check_nested_errors(data, "get_pet")
    if has_err:
        print(f"Error in get_pet response: {err_msg}")
        return None
    return safe_get(data, "id")


def main() -> None:
    load_dotenv()
    print("Creating a pet...")
    pet = create_pet("Fluffy", "available")
    print(f"Created pet ID: {pet}")

    if pet:
        fetched = get_pet(pet)
        print(f"Fetched pet ID: {fetched}")

    status_pets = find_pets_by_status(["available"])
    print(f"Found {len(status_pets)} available pets.")


if __name__ == '__main__':
    main()