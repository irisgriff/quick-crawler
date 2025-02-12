from src.crawler.input_queue import InputQueue
from lxml import html


def visit_page(
    content: str,
    url: str,
    input_queue: InputQueue,
    main_body_xpath,
    link_handler: callable,
):
    """
    Extracts natural language text from a page and enqueues the contained links.
    """

    # Define the xpath for the main content section
    tree = html.fromstring(content)
    content_section = tree.xpath(main_body_xpath)

    if not content_section:
        raise ValueError(f"Unable to parse {url} using xpath: {main_body_xpath}")

    # Extract text from <p> elements only
    paragraphs = content_section[0].xpath(".//p")
    text_content = " ".join(
        [p.text_content().strip() for p in paragraphs if p.text_content().strip()]
    )

    # Extract valid links
    for a_tag in tree.xpath(main_body_xpath + "//a[@href]"):
        link = a_tag.get("href").split("#")[0]
        link_handler(url, link, input_queue)
    return " ".join(text_content.split())
