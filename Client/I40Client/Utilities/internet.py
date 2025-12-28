from bs4 import BeautifulSoup
from typing import Any, Literal
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from ddgs.ddgs import DDGS
from . import format_conversion
import requests
import re

__DDGS__: DDGS = DDGS()
SCRAPE_HEADERS: dict[str, Any] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
FollowScrapeGuidelines: bool = True

class ScrapeGuidelinesError(BaseException):
    def __init__(self) -> None:
        super().__init__("Scrapping not allowed here. Please disable the scrapping guidelines or scrape another website if you see this error often.")

def __get_requests_response__(URL: str) -> requests.Response:
    response = requests.get(URL, headers = SCRAPE_HEADERS)
    response.raise_for_status()

    return response

def SearchText(
    Keywords: str,
    Region: str = "us-en",
    UseSafeSearch: bool = True,
    MaxResults: int = 5,
    Backend: Literal[
        "bing", "brave", "duckduckgo", "google", "grokipedia",
        "mojeek", "yandex", "yahoo", "wikipedia", "auto"
    ] = "duckduckgo"
) -> list[str]:
    results = __DDGS__.text(
        query = Keywords,
        region = Region,
        safesearch = "moderate" if (UseSafeSearch) else "off",
        max_results = MaxResults,
        backend = Backend
    )
    return [r["href"] for r in results]

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
    
    return url

def GetURLInfo(URL: str) -> dict[str, str]:
    if ("://" in URL):
        protocol = URL[:URL.find("://")]
        website = URL[URL.find("://") + 3:]
    else:
        protocol = "http"
        website = URL
    
    if ("/" in website):
        website = website[:website.find("/")]
    
    if (website.count(".") == 1):
        subdomain = None
    elif (website.count(".") >= 2):
        subdomain = ".".join(website.split(".")[:-2])
        website = ".".join(website.split(".")[-2:])
    
    return {
        "protocol": protocol,
        "website": website,
        "subdomain": subdomain
    }

def Scrape_Base(URL: str) -> BeautifulSoup:
    if (FollowScrapeGuidelines):
        baseURL = urlparse(URL)
        baseURL = f"{baseURL.scheme}://{baseURL.netloc}/"

        rp = RobotFileParser(baseURL + "robots.txt")
        rp.read()

        if (not rp.can_fetch("*", URL)):
            raise ScrapeGuidelinesError()

    response = __get_requests_response__(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    return soup

def Scrape_Wikipedia(URL: str) -> dict[str, str]:
    parserURL = GetURLInfo(GetBaseURL(URL))
    parserURL = f"{parserURL['protocol']}://" + (f"{parserURL['subdomain']}." if (parserURL["subdomain"] is not None) else "") + parserURL["website"]

    soup = Scrape_Base(URL)
    title = soup.find("h1", {"class": "mw-first-heading"}).get_text().strip()
    paragraphs = soup.find("div", {"class": "mw-parser-output"}).find_all("p")
    content = []

    for p in paragraphs:
        if (p.get_text().strip()):
            content.append(format_conversion.HTML_To_Markdown(str(p), parserURL).strip())

    return {"title": title, "content_text": "\n\n".join(content)}  # TODO: Scrape images too

def Scrape_Reddit_Post(URL: str, CommentsLimit: int | None = None) -> dict[str, str | dict[str, str]]:
    soup = Scrape_Base(URL)
    title = soup.find("h1", {"slot": "title"})
    contentTxt = soup.find("div", {"property": "schema:articleBody"})

    if (title is None):
        title = "No title"
    else:
        title = title.get_text().strip()

    if (contentTxt is None):
        contentTxt = "No text content"
    else:
        contentTxt = format_conversion.HTML_To_Markdown(str(contentTxt), URL).strip()
    
    # TODO: Scrape images too
    
    # TODO: Comments

    return {"title": title, "content_text": contentTxt}

def Scrape_Reddit_Subreddit(
    URL: str,
    IsName: bool = False,
    ScrapePosts: bool = False,
    PostsLimit: int | None = None,
    PostsCommentsLimit: int | None = None
) -> list[str | dict[str, str | dict[str, str]]]:
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

def Scrape_Wikidot(URL: str) -> dict[str, str]:
    parserURL = GetURLInfo(GetBaseURL(URL))
    parserURL = f"{parserURL['protocol']}://" + (f"{parserURL['subdomain']}." if (parserURL["subdomain"] is not None) else "") + parserURL["website"]

    soup = Scrape_Base(URL)
    title = soup.find("div", {"id": "page-title"}).get_text().strip()
    paragraphs = soup.find("div", {"id": "page-content"}).find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "span"])
    content = []

    for p in paragraphs:
        if (p.get_text().strip()):
            content.append(format_conversion.HTML_To_Markdown(str(p), parserURL).strip())

    return {"title": title, "content_text": "\n\n".join(content)}  # TODO: Scrape images too

def Scrape_Fandom(URL: str) -> dict[str, str]:
    parserURL = GetURLInfo(GetBaseURL(URL))
    parserURL = f"{parserURL['protocol']}://" + (f"{parserURL['subdomain']}." if (parserURL["subdomain"] is not None) else "") + parserURL["website"]

    soup = Scrape_Base(URL)
    title = soup.find("h1", {"class": "page-header__title"}).get_text().strip()
    paragraphs = soup.find("div", {"class": "mw-content-ltr"}).find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "span"])
    content = []

    for p in paragraphs:
        if (p.get_text().strip()):
            content.append(format_conversion.HTML_To_Markdown(str(p), parserURL).strip())
    
    return {"title": title, "content_text": "\n\n".join(content)}  # TODO: Scrape images too

def Scrape_Auto(URL: str) -> dict[str, Any]:
    urlInfo = GetURLInfo(GetBaseURL(URL))

    if (urlInfo["website"] == "reddit.com"):
        if ("/comments/" in URL):
            # Scrape Reddit post
            return Scrape_Reddit_Post(URL, None) | {"type": "reddit post"}
        else:
            # Scrape Reddit subreddit
            s = Scrape_Reddit_Subreddit(URL, False, True, None, None)

            # TODO
    elif (urlInfo["website"] == "wikipedia.com"):
        return Scrape_Wikipedia(URL) | {"type": "wikipedia"}
    elif (urlInfo["website"] == "wikidot.com"):
        return Scrape_Wikidot(URL) | {"type": "wikidot"}
    elif (urlInfo["website"] == "fandom.com"):
        return Scrape_Fandom(URL) | {"type": "fandom"}
    else:
        websiteContent = str(Scrape_Base(URL).find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "span"]))
        websiteContent = format_conversion.HTML_To_Markdown(
            websiteContent,
            f"{urlInfo['protocol']}://{urlInfo['subdomain'] + '.' if (urlInfo['subdomain'] is not None) else ''}{urlInfo['website']}"
        )
        return {"title": "No title detected", "content_text": websiteContent, "type": "unknown"}