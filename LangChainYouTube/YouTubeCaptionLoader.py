from typing import List, Sequence

import pysrt
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from pytube import YouTube as pytube
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter


class YouTubeCaptionLoader(BaseLoader):
    """
    Load chunked caption assets from YouTube for a single media entry ID.

    Following the pattern of other LangChain loaders, all configuration of
    YouTubeCaptionLoader is done via constructor parameters.  After an
    instance of the class has been created, call its `load()` method to begin
    working and return results.
    """
    EXPIRYSECONDSDEFAULT = 86400  # 24 hours
    CHUNKMINUTESDEFAULT = 2
    URLTEMPLATEDEFAULT = ('https://www.youtube.com/watch?'
                          'v={mediaId}&t={startSeconds}s')
    LANGUAGESDEFAULT: Sequence[str] = ('en',)

    def __init__(self,
                 mediaUrl: str,
                 urlTemplate: str = URLTEMPLATEDEFAULT,
                 chunkMinutes: int = CHUNKMINUTESDEFAULT,
                 languages: Sequence[str] = LANGUAGESDEFAULT):
        """
        :param mediaUrl: String containing the URL of the media in YouTube to
            be processed.
        :param urlTemplate: *Optional* String template to construct URLs for
            the `source` metadata property of LangChain `Document` objects.
            It must contain the fields `mediaId` and `startSeconds` ONLY to be
            filled in by `str.format()`.  *Defaults to the value of
            `YouTubeCaptionLoader.URLTEMPLATEDEFAULT`,
            `https://www.youtube.com/watch?v={mediaId}&t={startSeconds}s`.*
        :param chunkMinutes: *Optional* Integer number of minutes of the length
            of each caption chunk loaded from YouTube.  *Defaults to the value
            of`YouTubeCaptionLoader.CHUNKMINUTESDEFAULT`, which is `2`.*
        :param languages: *Optional* Sequence of strings containing language
            codes for which to load captions.  *Defaults to the value of
            `YouTubeCaptionLoader.LANGUAGESDEFAULT`, `('en',)`.*
        """

        if not mediaUrl:
            raise ValueError('mediaUrl must be specified')

        if not urlTemplate:
            raise ValueError('urlTemplate must be specified, with fields for'
                             '"{mediaId}" and "{startSeconds}".')

        self.mediaUrl = mediaUrl
        self.mediaId = YoutubeLoader.extract_video_id(mediaUrl)
        self.urlTemplate = urlTemplate
        self.chunkMinutes = int(chunkMinutes)
        self.languages = languages
        self.srtFormatter = SRTFormatter()

    def load(self) -> List[Document]:
        videoData = pytube(self.mediaUrl)
        videoInfo = {key: value for key in ('title', 'author')
                     if (value := videoData.__getattribute__(key)) is not None}

        transcript = (YouTubeTranscriptApi.list_transcripts(
            self.mediaId).find_manually_created_transcript(self.languages))

        transcriptSrt = self.srtFormatter.format_transcript(transcript.fetch())

        captionDocuments: List[Document] = []
        captions = pysrt.from_string(transcriptSrt)

        index = 0
        while (captionsSection := captions.slice(
                starts_after={'minutes': (start := self.chunkMinutes * index)},
                ends_before={'minutes': start + self.chunkMinutes})):
            captionDocuments.append(Document(
                page_content=captionsSection.text,
                metadata={
                    # Start time is rounded to the nearest second
                    'source': self.urlTemplate.format(
                        mediaId=self.mediaId,
                        startSeconds=captionsSection[0].start.ordinal // 1000
                    ),
                    'media_id': self.mediaId,
                    'language_code': transcript.language_code,
                    'caption_format': 'SRT',
                    **videoInfo}))
            index += 1

        return captionDocuments
