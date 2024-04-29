import sys

from LangChainYouTube import YouTubeCaptionLoader

mediaId = '7mCE73j59Zs'  # U2 - When Love Comes To Town
urlTemplate = 'https://www.youtube.com/watch?v={mediaId}&t={startSeconds}s'

captionLoader = YouTubeCaptionLoader(
    mediaId=mediaId,
    urlTemplate=urlTemplate)

print(captionLoader.load())
