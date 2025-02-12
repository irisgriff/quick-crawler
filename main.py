import multiprocessing
import time
import requests
import yaml
from pybloom_live import BloomFilter
from src.crawler import InputQueue, visit_page
import src.link_handler as link_handlers

# Configure the crawler
with open("config.yaml", "rb") as f:
    config: dict = yaml.safe_load(f)

NUM_CRAWLERS = config.get("num_crawlers", 2)
TIMEOUT_POLICY = config.get(
    "timeout_policy", 0.5
)  # Take no longer than 0.5 seconds on the first pass
RETRY_DELAY = config.get("retry_delay", 0.010)  # Seconds to wait before retrying
MAIN_BODY_XPATH = config.get(
    "main_body_xpath", "/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[1]"
)
START_URLS = config.get("start_urls", ["https://en.wikipedia.org/wiki/Statistics"])
VALID_DOMAINS = config.get("valid_domains", ["https://en.wikipedia.org"])
try:
    link_handler = getattr(
        link_handlers, config.get("link_handler", "wikipedia_handler")
    )
except AttributeError:
    raise AttributeError(
        "Invalid config.yaml: 'link_handler' must be one of ['default_handler', 'wikipedia_handler']"
    )


### Request handler
def handle_request(url: str, worker_num, input_queue: InputQueue, retry=False):
    """
    This function gets the content from a web page, write's the content onto
    the disk, and then enqueues any links that it contains (without duplication).
    """
    try:
        response = requests.get(url, timeout=TIMEOUT_POLICY)
        # If the response is good, extract the text and enqueue links.
        if response.status_code == 200:
            text_content = visit_page(
                response.text,
                url,
                input_queue,
                MAIN_BODY_XPATH,
                link_handler=link_handler,
            )
            print(f"{worker_num} Visited: {url}")
            # Write the page content to the buffer
            with open(
                f"crawl_data/{worker_num}_crawl.txt", "a", encoding="utf-8"
            ) as file_buffer:
                file_buffer.write(f">{url}\n{text_content}\n")
            # Save the visit pages to a different buffer
            with open(
                f"crawl_data/{worker_num}_visited_pages.txt", "a", encoding="utf-8"
            ) as file_buffer:
                file_buffer.write(f"{worker_num}:{url}\n")
        # Otherwise, retry if timed out or throttled
        elif response.status_code == 408:
            if retry:
                print(f"{worker_num} Timed out, retrying: {url}")
                time.sleep(RETRY_DELAY)
                handle_request(url, worker_num, input_queue, retry=False)
            else:
                print(f"{worker_num} Timed out: {url}")
        elif response.status_code == 429:
            if retry:
                print(f"{worker_num} Throttled, retrying: {url}")
                time.sleep(RETRY_DELAY)
                handle_request(url, worker_num, input_queue, retry=False)
            else:
                print(f"{worker_num} Throttled: {url}")
        else:
            print(f"{worker_num} Status code {response.status_code}: {url}")
    except (
        requests.Timeout,
        requests.exceptions.ConnectionError,
    ):
        if retry:
            print(f"{worker_num} Other error, retrying: {url}")
            time.sleep(RETRY_DELAY)
            handle_request(url, worker_num, input_queue, retry=False)
        else:
            print(f"{worker_num} Other error: {url}")
        # timed_out.add(url)
    return


# Define an instance of the main crawl task
def crawl_task(input_queue: InputQueue, output_queue, worker_num: str):
    """Worker process to visit pages."""
    while True:
        url = output_queue.get()
        handle_request(url, worker_num, input_queue, retry=True)


# Define the bloom filtering task
def bloom_filter_task(input_queue, output_queue):
    bloom_filter = BloomFilter(5 * 10**9, 0.01)
    while True:
        url = input_queue.get()
        if url not in bloom_filter:
            bloom_filter.add(url)
            output_queue.put(url)


if __name__ == "__main__":
    multiprocessing.freeze_support()  # For Windows compatibility

    # Initialize Queues
    manager = multiprocessing.Manager()
    input_queue = InputQueue(manager, VALID_DOMAINS)
    output_queue = manager.Queue()  # Final queue

    for url in START_URLS:
        input_queue.safe_put(url)

    # Initialize Bloom filter process
    bloom_proc = multiprocessing.Process(
        target=bloom_filter_task, args=(input_queue, output_queue)
    )
    bloom_proc.start()

    # Initialize multiprocessing pool
    with multiprocessing.Pool(NUM_CRAWLERS) as pool:
        try:
            workers = [
                pool.apply_async(
                    crawl_task, (input_queue, output_queue, str(i).zfill(2))
                )
                for i in range(NUM_CRAWLERS)
            ]
            # Monitor and keep main process alive
            while any(w.ready() is False for w in workers):
                time.sleep(0.001)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected. Terminating crawl gracefully...")
            bloom_proc.terminate()
