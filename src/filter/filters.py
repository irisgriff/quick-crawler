import urllib.robotparser


def load_robots_txt(url):
    """Load robots.txt"""
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(url)
    rp.read()
    return rp


def default_filter(url: str, robots_parser, **kwargs) -> bool:
    """
    Check if the URL is a discussion page or contains discussions.
    This may not be a comprehensive list of filters.

    url: The url to check filter
    robots_parser: The robots.txt filter
    """
    # True means the link will be filtered
    if robots_parser is None:
        return True
    return not robots_parser.can_fetch("*", url)


def closed_domain_filter(url: str, robots_parser, domain: str, **kwargs) -> bool:
    """
    This filters out links to other domains.

    url: The url to check filter
    robots_parser: The robots.txt filter
    """
    # True means the link will be filtered
    if robots_parser is None:
        return True
    if not url.startswith(domain):
        return True
    if not robots_parser.can_fetch("*", url):
        return True
    return False


def wikipedia_filter(url: str, robots_parser, **kwargs) -> bool:
    """
    Check if the URL is a discussion page or contains discussions.
    This may not be a comprehensive list of filters.

    url: The url to check filter
    robots_parser: The robots.txt filter
    """
    # True means the link will be filtered
    if robots_parser is None:
        return True
    if not url.startswith("https://en.wikipedia.org"):
        return True
    if not robots_parser.can_fetch("*", url):
        return True
    # Additional filters
    return any(
        keyword in url
        for keyword in [
            "Talk:",
            "User:",
            "File:",
            "talk:",
            "Help",
            "Special:",
            "files_for_discussion",
            "Template:",
            "Portal:",
            "Category:",
            "index.php",
            "Wikipedia:",
        ]
    )
