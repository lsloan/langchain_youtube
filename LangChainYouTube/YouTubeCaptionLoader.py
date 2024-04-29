from typing import List, Sequence

import pysrt
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
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

    # class FilterType(Enum):
    #     """
    #     Types of supported filter strings.
    #
    #     - `MEDIAID` indicates a Kaltura media entry ID.
    #     - `CATEGORY` indicates a Kaltura category text "full path", e.g.,
    #       `root>site>courses>course_category_name`.
    #
    #     For convenience, the constructor parameter is case-insensitive.
    #     E.g., `FilterType('CATEGORY')` and `FilterType('category')` are
    #     equivalent.
    #     """
    #     CATEGORY = auto()
    #     MEDIAID = auto()
    #
    #     @classmethod
    #     def _missing_(cls, key):
    #         value = cls.__members__.get(key.upper())
    #         if value is None:
    #             raise ValueError(f'Invalid key "{key}" for {cls.__name__}')
    #         return cls(value)

    def __init__(self,
                 mediaId: str,
                 urlTemplate: str,
                 chunkMinutes: int = CHUNKMINUTESDEFAULT,
                 languages: Sequence[str] = ('en',)):
        """
        :param mediaId: String containing the ID of the media in YouTube to be
            processed.
        :param urlTemplate: String template to construct URLs for the `source`
            metadata property of LangChain `Document` objects.  It must contain
            the fields `mediaId` and `startSeconds` ONLY to be filled in by
            `str.format()`.  E.g.,
            `https://example.edu/v/{mediaId}?t={startSeconds}`.
        :param chunkMinutes: *Optional* Integer number of minutes of the length
            of each caption chunk loaded from Kaltura.  *Defaults to value of
            `KalturaCaptionLoader.CHUNKMINUTESDEFAULT`.*
        """

        if not mediaId:
            raise ValueError('mediaId must be specified')

        if not urlTemplate:
            raise ValueError('urlFormat must be specified, with fields for'
                             '"{mediaId}" and "{startSeconds}".')

        self.mediaId = mediaId
        self.urlTemplate = urlTemplate
        self.chunkMinutes = int(chunkMinutes)
        self.languages = languages
        self.srtFormatter = SRTFormatter()

    # def setMediaEntry(self, mediaEntryId: str) -> Self:
    #     self.mediaFilter = KalturaMediaEntryFilter()
    #     self.mediaFilter.idEqual = mediaEntryId
    #     return self

    # def setMediaCategory(self, categoryText: str) -> Self:
    #     self.mediaFilter = KalturaMediaEntryFilter()
    #     self.mediaFilter.categoriesMatchAnd = categoryText
    #     return self

    def load(self) -> List[Document]:
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
                # TODO: What other metadata should be included?
                metadata={  # Start time is sliced to remove milliseconds.
                    'source': self.urlTemplate.format(
                        mediaId=self.mediaId,
                        startSeconds=str(captionsSection[0].start.ordinal)[
                                     0:-3]),  # 'filename': mediaEntry.name,
                    'media_id': self.mediaId,  # 'caption_id': captionAsset.id,
                    'language_code': transcript.language_code,
                    'caption_format': 'SRT', }))
            index += 1

        return captionDocuments
