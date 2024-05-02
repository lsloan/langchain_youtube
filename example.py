from LangChainYouTube import YouTubeCaptionLoader

# U2 - When Love Comes To Town
# mediaUrl = 'https://www.youtube.com/watch?v=7mCE73j59Zs'  # watch-style URL
# mediaUrl = 'https://www.youtube.com/embed/7mCE73j59Zs'  # embed-style URL

# Without CGI Walton Goggins As The Ghoul Is So Weird
# Example of video without `en` captions.  It has `en-US` captions, which fail.
mediaUrl = 'https://www.youtube.com/watch?v=qGulvsKFyvo'

captionLoader = YouTubeCaptionLoader(mediaUrl)

captionDocuments = captionLoader.load()

print(captionDocuments)
