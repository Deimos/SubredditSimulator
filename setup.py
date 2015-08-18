from setuptools import find_packages, setup

setup(
    name="SubredditSimulator",
    version="",
    description="An automated bot-run subreddit using markov chains",
    author="Chad Birch",
    author_email="chad.birch@gmail.com",
    platforms=["any"],
    license="MIT",
    url="https://github.com/Deimos/SubredditSimulator",
    packages=find_packages(),
    install_requires=[i.strip() for i in open("requirements.txt").readlines()],
)
