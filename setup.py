import setuptools

setuptools.setup(
    name='LangChainYouTube',
    version='0.0.0',
    author='Mr. Lance E Sloan',
    author_email='lsloan-github.com@umich.edu',
    description='Collects captions from media in YouTube and produces '
                'LangChain Document objects.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license_files=['LICENSE.txt', ],
    url='https://github.com/umich-its-ai/langchain_youtube',
    project_urls={
        'Issues': 'https://github.com/umich-its-ai/langchain_youtube/issues',
        'Homepage': 'https://github.com/umich-its-ai/langchain_youtube', },
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Topic :: Scientific/Engineering :: Artificial Intelligence', ],
    keywords=[
        'YouTube', 'LangChain', 'caption', 'AI', 'Artificial Intelligence', ],
    python_requires='>=3.11.8',
    include_package_data=True,
    data_files=[('/', ['requirements.txt'])],
    install_requires=open('requirements.txt').read().split(),
)
