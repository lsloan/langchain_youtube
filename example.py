from typing import List

from langchain_core.documents import Document

from LangChainYouTube import YouTubeCaptionLoader

# U2 - When Love Comes To Town - "en" captions
# mediaUrl = 'https://www.youtube.com/embed/7mCE73j59Zs'  # embed-style URL
mediaUrl = 'https://www.youtube.com/watch?v=7mCE73j59Zs'  # watch-style URL


# Without CGI Walton Goggins As The Ghoul Is So Weird - "en-US" captions
# mediaUrl = 'https://www.youtube.com/watch?v=qGulvsKFyvo'

def main(mediaUrl: str) -> List[Document]:
    captionLoader = YouTubeCaptionLoader(mediaUrl)

    captionDocuments = captionLoader.load()

    return captionDocuments


if '__main__' == __name__:  # pragma: no cover
    captionDocuments = main(mediaUrl)
    print('\n\n'.join(map(repr, captionDocuments)))
