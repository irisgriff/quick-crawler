from typing import List
import urllib.error
from urllib.parse import urlparse

import urllib
from src.filter import default_filter, load_robots_txt


class InputQueue:
    """Queue wrapper to handle initial input filtering."""

    def __init__(self, manager, valid_domains: List[str]):
        self.queue = manager.Queue()
        try:
            self.robots_parsers = {}
            for d in valid_domains:
                self.robots_parsers[d.split("://")[1]] = load_robots_txt(
                    d + "/robots.txt"
                )
        except urllib.error.URLError:
            raise ValueError(
                f"Invalid config.yaml: One or more URLs in 'valid_domains' is not formatted correctly"
            )

    def safe_put(self, url: str, filter_fun: callable = default_filter):
        """
        This function canonicalizes and puts valid URLs on queue.
        """
        # Canonicalize the url
        parsed_url = urlparse(url)._replace(fragment="", query="")
        url, domain = parsed_url.geturl(), parsed_url.netloc
        # Skip url if not allowed, or filtered
        if filter_fun(url, self.robots_parsers.get(domain, None), domain=domain):
            return
        # Otherwise, the url is allowed, and we may enqueue
        self.queue.put(url)

    def get(self):
        """Retrieve an item from the queue."""
        return self.queue.get()
