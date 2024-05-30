from typing import List, Sequence

from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from pytube import YouTube as pytube
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptList, \
    Transcript


class YouTubeCaptionLoader(BaseLoader):
    """
    Load chunked caption assets from YouTube for a single media entry ID.

    Following the pattern of other LangChain loaders, all configuration of
    YouTubeCaptionLoader is done via constructor parameters.  After an
    instance of the class has been created, call its `load()` method to begin
    working and return results.

    This differs from langchain_community.document_loaders.YoutubeLoader
    in that it splits captions into chunks of a specified length and
    includes the timestamp for the beginning of each chunk in its metadata.
    """
    CHUNK_SECONDS_DEFAULT = 120
    URL_TEMPLATE_DEFAULT = ('https://www.youtube.com/watch?'
                            'v={mediaId}&t={startSeconds}s')
    LANGUAGES_DEFAULT = ('en-us', 'en', 'en-ca', 'en-gb', 'en-ie', 'en-au',
                         'en-nz', 'en-bz', 'en-jm', 'en-ph', 'en-tt',
                         'en-za', 'en-zw')
    """Various English dialects from ISO 639-1, ordered by similarity to 
      `en-us`.  For an unofficial listing of languages with dialects, see: 
      https://gist.github.com/jrnk/8eb57b065ea0b098d571#file-iso-639-1-language-json"""
    YOUTUBE_METADATA_KEYS_DEFAULT = ('title', 'author')

    def __init__(self,
                 mediaUrl: str,
                 urlTemplate: str = URL_TEMPLATE_DEFAULT,
                 chunkSeconds: int = CHUNK_SECONDS_DEFAULT,
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
            `YouTubeCaptionLoader.URL_TEMPLATE_DEFAULT`.*
        :param chunkSeconds: *Optional* Integer number of seconds of the length
            of each caption chunk loaded from YouTube.  *Defaults to the value
            of`YouTubeCaptionLoader.CHUNK_SECONDS_DEFAULT`.*
        :param languages: *Optional* Sequence of strings containing language
            codes for which to load captions.  *Defaults to the value of
            `YouTubeCaptionLoader.LANGUAGES_DEFAULT`, a list of various English
            dialects from ISO 639-1, ordered by similarity to `en-us`.  See:
            https://gist.github.com/jrnk/8eb57b065ea0b098d571#file-iso-639-1-language-json*
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

        # LangChain's method for handling YouTube URLs works well
        self.mediaId = YoutubeLoader.extract_video_id(mediaUrl)
        if not self.mediaId:
            raise ValueError('mediaId could not be extracted from mediaUrl')

        self.mediaUrl = mediaUrl
        self.urlTemplate = urlTemplate
        self.chunkSeconds = int(chunkSeconds)
        self.languages = languages
        self.youtubeMetadataKeys = youtubeMetadataKeys

    def _findPreferredLanguageTranscriptIsGenerated(
            self, transcriptList: TranscriptList,
            isGenerated: bool) -> Transcript | None:
        for language in self.languages:
            for transcript in transcriptList:
                if (transcript.is_generated == isGenerated and
                        transcript.language_code.lower() == language.lower()):
                    return transcript
        return None

    def _findPreferredLanguageTranscript(
            self, transcriptList: TranscriptList) -> Transcript | None:
        """
        Find the first transcript in the list that is not generated and has a
        language code matching one of the languages in `self.languages`.  If
        a non-generated transcript is not found, find the first generated one.
        This method resolves the problem that YouTubeTranscriptApi does not
        have a CASE-INSENSITIVE method to find a transcript by language code.
        :param transcriptList:
        :return:
        """
        transcript = self._findPreferredLanguageTranscriptIsGenerated(
            transcriptList, False)
        if transcript is not None:
            return transcript

        # no manually edited transcript found, fall back to auto-generated ones
        return self._findPreferredLanguageTranscriptIsGenerated(
            transcriptList, True)

    def load(self) -> List[Document]:
        def makeChunkDocument() -> Document:
            """Create Document from chunk of transcript pieces."""
            m, s = divmod(chunkStartSeconds, 60)
            h, m = divmod(m, 60)
            return Document(
                page_content=' '.join(
                    c['text'].strip(' ') for c in chunkPieces),
                metadata={
                    'source': self.urlTemplate.format(
                        mediaId=self.mediaId, startSeconds=chunkStartSeconds),
                    'start_seconds': chunkStartSeconds,
                    'start_timestamp': f'{h:02d}:{m:02d}:{s:02d}',
                    **staticMetadata})

        transcriptList = (
            YouTubeTranscriptApi.list_transcripts(self.mediaId))

        transcript = self._findPreferredLanguageTranscript(transcriptList)

        if transcript is None:
            return []

        videoDetails = pytube(self.mediaUrl).vid_info.get('videoDetails', {})
        staticMetadata = {**{k: v for k in self.youtubeMetadataKeys
                             if (v := videoDetails.get(k)) is not None},
                          'caption_language_code': transcript.language_code,
                          'media_id': self.mediaId}

        transcriptPieces = transcript.fetch()

        documents: List[Document] = []
        chunkPieces = []
        chunkStartSeconds = 0
        chunkTimeLimit = self.chunkSeconds
        for transcriptPiece in transcriptPieces:
            if (transcriptPiece['start'] +
                    transcriptPiece['duration'] > chunkTimeLimit):
                if chunkPieces:
                    documents.append(makeChunkDocument())
                    chunkPieces = []
                chunkStartSeconds = chunkTimeLimit
                chunkTimeLimit += self.chunkSeconds
            chunkPieces.append(transcriptPiece)

        # handle chunk pieces left over from last iteration
        if chunkPieces:
            documents.append(makeChunkDocument())

        return documents
