from LangChainYouTube import YouTubeCaptionLoader

# U2 - When Love Comes To Town
mediaUrl = 'https://www.youtube.com/watch?v=7mCE73j59Zs'

captionLoader = YouTubeCaptionLoader(mediaUrl)

captionDocuments = captionLoader.load()

print(captionDocuments)
