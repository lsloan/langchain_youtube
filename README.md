# langchain_youtube — README

A Python module to collect captions from media in YouTube and produce LangChain `Document` objects.

Unlike the YouTube indexer included with LangChain Community, which takes
video captions and returns them as a single `Document` object, this module
rearranges the captions into multiple `Document` objects, each one containing
a specific number of seconds.  The metadata of each `Document` object includes
the timestamp in the video where the captions begin and the YouTube URL with
the timestamp as a start time.
