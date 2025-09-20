from bs4 import BeautifulSoup
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import requests
import re
import Utilities.format_conversion as format_conversion
import Utilities.logs as logs
import exceptions

SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
Configuration: dict[str, Any] = {}

def GetBaseURL(URL: str) -> str:
    if ("/" in URL):
        url = URL[:URL.rfind("/")]
        url2 = URL[URL.rfind("/") + 1:]

        if ("#" in url2):
            url2 = url2[:url2.find("#")]
        
        if ("?" in url2):
            url2 = url2[:url2.find("?")]
        
        url = f"{url}/{url2}"
    else:
        url = URL

        if ("#" in url):
            url = url[:url.find("#")]
        
        if ("?" in url):
            url = url[:url.find("?")]
    
    logs.WriteLog(logs.INFO, "[internet] Got base URL.")
    return url

def __get_requests_response__(URL: str) -> requests.Response:
    response = requests.get(URL, headers = SCRAPE_HEADERS)
    response.raise_for_status()

    return response

def Scrape_Base(URL: str) -> BeautifulSoup:
    logs.WriteLog(logs.INFO, "[internet] Running base scrapper.")

    if (Configuration["internet"]["follow_scrape_guidelines"]):
        baseURL = urlparse(URL)
        baseURL = f"{baseURL.scheme}://{baseURL.netloc}/"

        rp = RobotFileParser(baseURL + "robots.txt")
        rp.read()

        if (not rp.can_fetch("*", URL)):
            raise exceptions.ScrapeGuidelinesError()

    response = __get_requests_response__(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    return soup

def Scrape_Wikipedia(URL: str) -> dict[str, str]:
    logs.WriteLog(logs.INFO, "[internet] Running Wikipedia scrapper.")

    soup = Scrape_Base(URL)
    title = soup.find("h1", {"class": "mw-first-heading"}).get_text()
    paragraphs = soup.find("div", {"class": "mw-parser-output"}).find_all("p")
    content = []

    for p in paragraphs:
        if (p.get_text().strip()):
            content.append(format_conversion.HTML_To_Markdown(str(p), GetBaseURL(URL)).strip())

    return {"title": title, "content": "\n\n".join(content)}

def Scrape_Reddit_Post(URL: str, CommentsLimit: int | None = None) -> dict[str, str | dict[str, str]]:
    logs.WriteLog(logs.INFO, "[internet] Running Reddit post scrapper.")

    soup = Scrape_Base(URL)
    title = soup.find("h1", {"slot": "title"})
    content = soup.find("div", {"property": "schema:articleBody"})

    if (title is None):
        title = "No title"
    else:
        title = title.get_text().strip()

    if (content is None):
        content = "No text content"
    else:
        content = format_conversion.HTML_To_Markdown(str(content), GetBaseURL(URL)).strip()
    
    # TODO: Comments

    return {"title": title, "content": content}

def Scrape_Reddit_Subreddit(
    URL: str,
    IsName: bool = False,
    ScrapePosts: bool = False,
    PostsLimit: int | None = None,
    PostsCommentsLimit: int | None = None
) -> list[str | dict[str, str | dict[str, str]]]:
    logs.WriteLog(logs.INFO, "[internet] Running Reddit subreddit scrapper.")

    if (PostsLimit > 25):
        logs.WriteLog(logs.WARNING, "[internet] Reddit (subreddit) posts limit is 25. Higher values doesn't make a difference.")
    
    if (IsName):
        url = f"https://reddit.com/r/{URL}/hot.json"
    else:
        url = re.search(r"/r/([^/]+)", URL).group(1)
        url = f"https://reddit.com/r/{url}/hot.json"
    
    response = __get_requests_response__(url)
    data = response.json()
    posts = []

    for post in data["data"]["children"]:
        if (PostsLimit is not None and len(posts) >= PostsLimit):
            break

        postUrl = post["data"]["url"]
        posts.append(Scrape_Reddit_Post(postUrl, PostsCommentsLimit) if (ScrapePosts) else postUrl)
    
    return posts