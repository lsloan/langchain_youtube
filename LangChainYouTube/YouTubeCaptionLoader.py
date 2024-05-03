from typing import List, Sequence

import pysrt
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from pytube import YouTube as pytube
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from youtube_transcript_api.formatters import SRTFormatter


class YouTubeCaptionLoader(BaseLoader):
    """
    Load chunked caption assets from YouTube for a single media entry ID.

    Following the pattern of other LangChain loaders, all configuration of
    YouTubeCaptionLoader is done via constructor parameters.  After an
    instance of the class has been created, call its `load()` method to begin
    working and return results.
    """
    CHUNK_MINUTES_DEFAULT = 2
    URL_TEMPLATE_DEFAULT = ('https://www.youtube.com/watch?'
                            'v={mediaId}&t={startSeconds}s')
    LANGUAGES_DEFAULT = ('en',)
    YOUTUBE_METADATA_KEYS_DEFAULT = ('title', 'author')

    def __init__(self,
                 mediaUrl: str,
                 urlTemplate: str = URL_TEMPLATE_DEFAULT,
                 chunkMinutes: int = CHUNK_MINUTES_DEFAULT,
                 languages: Sequence[str] = LANGUAGES_DEFAULT,
                 youtubeMetadataKeys: Sequence[str] =
                 YOUTUBE_METADATA_KEYS_DEFAULT):
        """
        :param mediaUrl: String containing the URL of the media in YouTube to
            be processed.
        :param urlTemplate: *Optional* String template to construct URLs for
            the `source` metadata property of LangChain `Document` objects.
            It must contain the fields `mediaId` and `startSeconds` ONLY to be
            filled in by `str.format()`.  *Defaults to the value of
            `YouTubeCaptionLoader.URLTEMPLATEDEFAULT`.*
        :param chunkMinutes: *Optional* Integer number of minutes of the length
            of each caption chunk loaded from YouTube.  *Defaults to the value
            of`YouTubeCaptionLoader.CHUNKMINUTESDEFAULT`.*
        :param languages: *Optional* Sequence of strings containing language
            codes for which to load captions.  *Defaults to the value of
            `YouTubeCaptionLoader.LANGUAGESDEFAULT`.*
        :param youtubeMetadataKeys: *Optional* Sequence of strings containing
            metadata keys to be extracted from the YouTube video.  *Defaults
            to the value of
            `YouTubeCaptionLoader.YOUTUBE_METADATA_KEYS_DEFAULT`.*
        """

        if not mediaUrl:
            raise ValueError('mediaUrl must be specified')

        if not urlTemplate:
            raise ValueError('urlTemplate must be specified, with fields for'
                             '"{mediaId}" and "{startSeconds}".')

        self.mediaId = YoutubeLoader.extract_video_id(mediaUrl)
        if not self.mediaId:
            raise ValueError('mediaId could not be extracted from mediaUrl')

        self.mediaUrl = mediaUrl
        self.urlTemplate = urlTemplate
        self.chunkMinutes = int(chunkMinutes)
        self.languages = languages
        self.youtubeMetadataKeys = youtubeMetadataKeys

    def load(self) -> List[Document]:
        videoDetails = pytube(self.mediaUrl).vid_info.get('videoDetails', {})
        videoMetadata = {key: value for key in self.youtubeMetadataKeys
                         if (value := videoDetails.get(key)) is not None}

        transcriptList = (YouTubeTranscriptApi.list_transcripts(
            self.mediaId))

        try:
            transcript = (transcriptList
                          .find_manually_created_transcript(self.languages))
        except NoTranscriptFound:
            # Find first transcript in list that is not generated and has a
            # language code that starts with one of the configured languages.
            # I.e., `en` may yield one of `en-US`, `en-GB`, etc., if available.
            transcriptLanguage = None
            for l in self.languages:
                for t in transcriptList:
                    if not t.is_generated and t.language_code.startswith(l):
                        transcriptLanguage = t.language_code
                        break
                if transcriptLanguage:
                    break

            if not transcriptLanguage:
                return []
            transcript = (transcriptList.find_transcript([transcriptLanguage]))

        transcriptSrt = SRTFormatter().format_transcript(transcript.fetch())

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
                    'timestamp': str(captionsSection[0].start)[0:-4],  # no ms
                    'language_code': transcript.language_code,
                    'caption_format': 'SRT',
                    **videoMetadata}))
            index += 1

        return captionDocuments
