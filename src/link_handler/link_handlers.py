from urllib.parse import urljoin
from src.filter import default_filter, wikipedia_filter
from src.crawler.input_queue import InputQueue


def default_handler(url: str, link: str, input_queue: InputQueue, **kwargs):
    input_queue.safe_put(link, filter_fun=default_filter)


def wikipedia_handler(url: str, link: str, input_queue: InputQueue, **kwargs):
    # Handle internal Wikipedia links
    if link.startswith("/wiki/"):
        full_link = urljoin(url, link)
        input_queue.safe_put(full_link, filter_fun=wikipedia_filter)
    else:
        input_queue.safe_put(link, filter_fun=wikipedia_filter)
