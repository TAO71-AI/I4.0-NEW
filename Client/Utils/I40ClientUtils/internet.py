from bs4 import BeautifulSoup
from typing import Any, Literal
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from ddgs.ddgs import DDGS
from . import format_conversion
import base64
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

def DownloadContent(URL: str, ReturnAsBase64: bool = False, ReturnAsString: bool = False) -> bytes | str:
    response = requests.get(URL)
    response.raise_for_status()

    content = response.content

    if (ReturnAsBase64):
        content = base64.b64encode(content)
    
    if (ReturnAsString):
        content = content.decode("utf-8")
    
    return content

def SearchText(
    Keywords: str,
    Region: str = "auto",
    UseSafeSearch: bool = True,
    MaxResults: int = 5,
    Backend: Literal[
        "bing", "brave", "duckduckgo", "google", "grokipedia",
        "mojeek", "yandex", "yahoo", "wikipedia", "auto"
    ] = "auto"
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

def Scrape_Wikipedia(URL: str) -> dict[str, str | list[dict[str, str]]]:
    soup = Scrape_Base(URL)
    title = soup.find("h1", {"class": "mw-first-heading"}).get_text().strip()
    paragraphs = soup.find("div", {"class": "mw-parser-output"}).find_all("p")
    content = []

    for p in paragraphs:
        if (p.get_text().strip()):
            content.append(format_conversion.HTML_To_Markdown(str(p)).strip())

    return {"title": title, "content_text": "\n\n".join(content), "content_media": []}  # TODO: Scrape images too

def Scrape_Reddit_Post(URL: str) -> dict[str, str | list[dict[str, str]]]:
    soup = Scrape_Base(URL)
    title = soup.find("h1", {"slot": "title"})
    contentTxt = soup.find("div", {"property": "schema:articleBody"})
    media = []

    if (title is None):
        title = "No title"
    else:
        title = title.get_text().strip()

    if (contentTxt is None):
        contentTxt = "No text content"
    else:
        contentTxt = format_conversion.HTML_To_Markdown(str(contentTxt)).strip()
    
    gallery = soup.find("gallery-carousel")

    if (gallery is None):
        mediaData = soup.find("img", {"id": "post-image"})
        mediaType = "image"

        if (mediaData is None):
            mediaData = soup.find("shreddit-player")
            mediaType = None if (mediaData is None) else "video" if (mediaData.get("post-type") == "video") else "gif"

        if (mediaData is not None):
            if (mediaType == "image"):
                mediaURL = mediaData.get("src")
            elif(mediaType == "gif"):
                mediaURL = mediaData.get("src")
                mediaType = "video"  # Reddit converts GIF to MP4
            elif (mediaType == "video"):
                # When handling with videos, only low-quality previews can be get
                # It's also buggy sometimes
                mediaURL = mediaData.get("preview")
            
            if (mediaURL is None):
                mediaURL = mediaData.get("data-lazy-src")
            
            if (mediaURL is not None):
                media.append({
                    "type": mediaType,
                    mediaType: DownloadContent(URL = mediaURL, ReturnAsBase64 = True, ReturnAsString = True)
                })
    else:
        gallery = gallery.find_all("li")

        for item in gallery:
            mediaContainer = item.find("figure", {"class": "items-center"})
            mediaData = mediaContainer.find("img")  # All gallery items must be items
            mediaURL = mediaData.get("src")

            if (mediaURL is None):
                mediaURL = mediaData.get("data-lazy-src")

                if (mediaURL is None):
                    continue
            
            media.append({
                "type": "image",
                "image": DownloadContent(URL = mediaURL, ReturnAsBase64 = True, ReturnAsString = True)
            })

    return {"title": title, "content_text": contentTxt, "content_media": media}

def Scrape_Reddit_Subreddit(
    URL: str,
    IsName: bool = False,
    ScrapePosts: bool = False,
    PostsLimit: int | None = None
) -> list[str | dict[str, str | list[dict[str, str]]]]:
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
        posts.append(Scrape_Reddit_Post(postUrl) if (ScrapePosts) else postUrl)
    
    return posts

def Scrape_Wikidot(URL: str) -> dict[str, str | list[dict[str, str]]]:
    soup = Scrape_Base(URL)
    title = soup.find("div", {"id": "page-title"}).get_text().strip()
    paragraphs = soup.find("div", {"id": "page-content"}).find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"])
    content = []

    for p in paragraphs:
        if (p.get_text().strip()):
            content.append(format_conversion.HTML_To_Markdown(str(p)).strip())

    return {"title": title, "content_text": "\n\n".join(content), "content_media": []}  # TODO: Scrape images too

def Scrape_Fandom(URL: str) -> dict[str, str | list[dict[str, str]]]:
    soup = Scrape_Base(URL)
    title = soup.find("h1", {"class": "page-header__title"}).get_text().strip()
    paragraphs = soup.find("div", {"class": "mw-content-ltr"}).find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"])
    content = []

    for p in paragraphs:
        if (p.get_text().strip()):
            content.append(format_conversion.HTML_To_Markdown(str(p)).strip())
    
    return {"title": title, "content_text": "\n\n".join(content), "content_media": []}  # TODO: Scrape images too

def Scrape_Grokipedia(URL: str) -> dict[str, str | list[dict[str, str]]]:
    soup = Scrape_Base(URL)
    article = soup.find("article")
    article.find("div", {"id": "references"}).decompose()

    title = article.find("h1").get_text().strip()
    paragraphs = article.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "span"], {"class": "block"})
    content = []

    for p in paragraphs:
        if (p.get_text().strip()):
            content.append(format_conversion.HTML_To_Markdown(str(p)).strip())
    
    return {"title": title, "content_text": "\n\n".join(content), "content_media": []}  # TODO: Scrape images too

def Scrape_Auto(URL: str, RedditSubredditPosts: int | None = None) -> dict[str, str | list[dict[str, str]]]:
    urlInfo = GetURLInfo(GetBaseURL(URL))

    if (urlInfo["website"] == "reddit.com"):
        if ("/comments/" in URL):
            # Scrape Reddit post
            return Scrape_Reddit_Post(URL) | {"type": "reddit post"}
        else:
            # Scrape Reddit subreddit
            return {"posts": Scrape_Reddit_Subreddit(URL, False, True, RedditSubredditPosts), "type": "reddit subreddit"}
    elif (urlInfo["website"] == "wikipedia.org"):
        return Scrape_Wikipedia(URL) | {"type": "wikipedia"}
    elif (urlInfo["website"] == "wikidot.com"):
        return Scrape_Wikidot(URL) | {"type": "wikidot"}
    elif (urlInfo["website"] == "fandom.com"):
        return Scrape_Fandom(URL) | {"type": "fandom"}
    elif (urlInfo["website"] == "grokipedia.com"):
        return Scrape_Grokipedia(URL) | {"type": "grokipedia"}
    else:
        websiteContent = str(Scrape_Base(URL).find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "span"]))
        websiteContent = format_conversion.HTML_To_Markdown(websiteContent)
        return {"title": "No title detected", "content_text": websiteContent, "content_media": [], "type": "unknown"}