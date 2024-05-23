# langchain_youtube — README

A Python module to collect captions from media in YouTube and produce LangChain `Document` objects.

Unlike the YouTube indexer included with LangChain Community, which takes
video captions and returns them as a single `Document` object, this module
rearranges the captions into multiple `Document` objects, each one containing
a specific number of seconds.  The metadata of each `Document` object includes
the timestamp in the video where the captions begin and the YouTube URL with
the timestamp as a start time.

## Installation

Download the wheel file (`.whl`) from the latest release on the [Releases](https://github.com/umich-its-ai/langchain_kaltura/releases) page.

```shell
pip install LangChainKaltura-0.0.1-py3-none-any.whl
```

## Usage

Instantiate `YouTubeCaptionLoader` with a YouTube media URL, then invoke its `load()` method…

```python
from LangChainYouTube import YouTubeCaptionLoader

# The Victors - University of Michigan 2021 Commencement
# youtu.be-style URL (watch- and embed-style URLs also supported)
mediaUrl = 'https://youtu.be/TKCMw0utiak'

captionLoader = YouTubeCaptionLoader(mediaUrl)
captionDocuments = captionLoader.load()

print('\n\n'.join(map(repr, captionDocuments)))
```

See the repo for `example.py`, a more detailed example.

## Features

* Does not require a YouTube API token.
* Captions from media are reorganized into chunks.  The chunk duration is configurable (`chunkSeconds` keyword argument), with a default of two minutes.
* The default caption languages are various English dialects, but a list of other languages may be specified (`languages` keyword argument).
* It returns a list of LangChain `Document` object(s), each containing a caption chunk and metadata.
* Caption chunks' metadata contains source URLs to the media, which includes timestamps to the specific chunk of the video.
