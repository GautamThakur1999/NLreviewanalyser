"""
T-P2-02 - Reddit connector + normaliser.

PRAW; subreddit + query search; full comment-tree expansion; threading preserved.
Filter [deleted]/[removed] bodies at normalisation.

Guards: EC-C-20, EC-C-18, EC-C-19, EC-C-21, EC-C-05
"""

import logging
from datetime import datetime, timezone
from typing import Any, Iterator
from pathlib import Path

import praw
from praw.models import Submission, Comment

from engine.collection.base import BaseConnector
from engine.store.verbatim import Verbatim, make_verbatim

logger = logging.getLogger(__name__)


class RedditConnector(BaseConnector):
    """
    Collects threads from Reddit using PRAW.
    """
    
    def __init__(
        self,
        brand: str,
        data_dir: Path,
        client_id: str,
        client_secret: str,
        user_agent: str,
        subreddits: list[str],
        queries: list[str],
        max_posts_per_query: int = 100,
    ):
        super().__init__(source="reddit", brand=brand, data_dir=data_dir, max_pages=1)
        self.subreddits = subreddits
        self.queries = queries
        self.max_posts_per_query = max_posts_per_query
        
        # PRAW respects rate limits automatically
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        yielded = 0
        
        for sub_name in self.subreddits:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                # Check access (EC-C-05) - if banned/private this will raise an exception during iteration
                for query in self.queries:
                    logger.info(f"RedditConnector [{self.brand}]: Searching r/{sub_name} for '{query}'")
                    
                    try:
                        posts = subreddit.search(query, sort="new", limit=self.max_posts_per_query)
                        
                        for post in posts:
                            if limit and yielded >= limit:
                                return
                            
                            # Check `since`
                            post_dt = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                            if since and post_dt < since:
                                continue
                                
                            # Yield the submission
                            yield self._serialize_submission(post, sub_name, query)
                            yielded += 1
                            
                            # Expand comment tree
                            post.comments.replace_more(limit=None)
                            comments = post.comments.list()
                            
                            for comment in comments:
                                if limit and yielded >= limit:
                                    return
                                    
                                comment_dt = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)
                                if since and comment_dt < since:
                                    continue
                                    
                                yield self._serialize_comment(comment, sub_name, post.id)
                                yielded += 1
                                
                    except Exception as e:
                        logger.error(f"Failed to search r/{sub_name} for query '{query}': {e}")
                        continue
                        
            except Exception as e:
                # Private/banned subreddit (EC-C-05)
                logger.error(f"Cannot access subreddit r/{sub_name}. Declaring gap: {e}")
                continue

    def _serialize_submission(self, post: Submission, subreddit: str, query: str) -> dict[str, Any]:
        """Convert a Submission to a JSON-serializable dict representing the raw payload."""
        return {
            "_type": "submission",
            "_source": self.source,
            "_brand": self.brand,
            "id": post.id,
            "subreddit": subreddit,
            "title": post.title,
            "selftext": post.selftext,
            "author": post.author.name if post.author else None,
            "created_utc": post.created_utc,
            "score": post.score,
            "url": post.url,
            "permalink": post.permalink,
            "query": query,
        }

    def _serialize_comment(self, comment: Comment, subreddit: str, submission_id: str) -> dict[str, Any]:
        """Convert a Comment to a JSON-serializable dict representing the raw payload."""
        parent_id = comment.parent_id
        # parent_id is prefixed with 't1_' (comment) or 't3_' (submission)
        if parent_id.startswith("t1_") or parent_id.startswith("t3_"):
            parent_id = parent_id[3:]
            
        return {
            "_type": "comment",
            "_source": self.source,
            "_brand": self.brand,
            "id": comment.id,
            "submission_id": submission_id,
            "parent_id": parent_id,
            "subreddit": subreddit,
            "body": comment.body,
            "author": comment.author.name if comment.author else None,
            "created_utc": comment.created_utc,
            "score": comment.score,
            "permalink": comment.permalink,
            "depth": comment.depth,
        }


def normalise_reddit_payload(raw: dict[str, Any], run_id: str, raw_payload_ref: str) -> Verbatim | None:
    """
    Convert a raw Reddit payload to the Verbatim schema.
    Returns None if the payload is [deleted] or [removed].
    """
    from engine.store.verbatim import make_verbatim
    
    # 1. Identify deleted/removed bodies (EC-C-18)
    _type = raw.get("_type")
    
    if _type == "submission":
        text_raw = raw.get("title", "")
        selftext = raw.get("selftext", "")
        if selftext and selftext not in ["[deleted]", "[removed]"]:
            text_raw = f"{text_raw}\n\n{selftext}"
            
    elif _type == "comment":
        text_raw = raw.get("body", "")
        if text_raw in ["[deleted]", "[removed]"]:
            return None
    else:
        raise ValueError(f"Unknown Reddit payload type: {_type}")
        
    source = raw.get("_source", "reddit")
    brand = raw.get("_brand", "unknown")
    source_id = raw.get("id")
    if not source_id:
        raise ValueError("Missing id in Reddit payload")
        
    dt = datetime.fromtimestamp(raw.get("created_utc", 0), tz=timezone.utc)
    
    # Threading info
    thread_id = raw.get("submission_id") if _type == "comment" else source_id
    parent_id = raw.get("parent_id") if _type == "comment" else None
    
    # Author (null author handled properly by verbatim schema which hashes to something deterministic)
    author = raw.get("author") or "unknown_author"
    
    return make_verbatim(
        source=source,
        source_id=source_id,
        brand=brand,
        run_id=run_id,
        raw_payload_ref=raw_payload_ref,
        text_raw=text_raw,
        rating=None,  # Reddit has no star rating
        review_date=dt,
        helpful_votes=raw.get("score", 0),
        thumbs_up=raw.get("score", 0),
        meta={
            "subreddit": raw.get("subreddit"),
            "author": author,
            "permalink": raw.get("permalink"),
        },
    )
