"""
T-P1-08 - Collection spike runner.

Glues together verify, raw writer, play store connector, normaliser,
and parquet writer.
"""

import logging
from pathlib import Path

from engine.config.settings import Settings
from engine.store.manifest import Manifest, make_run_id
from engine.store.raw import RawArchiveWriter
from engine.store.parquet import write_verbatims_to_parquet
from engine.store.verbatim import assert_unique_ids
from engine.collection.play_store import PlayStoreConnector, normalise_play_store_review
from engine.collection.app_store import AppStoreConnector, normalise_app_store_review
from engine.collection.reddit import RedditConnector, normalise_reddit_payload
from engine.collection.forum import ForumConnector, normalise_forum_payload
from engine.collection.youtube import YouTubeConnector, normalise_youtube_payload
from engine.collection.product_review import ProductReviewConnector, normalise_product_review_payload
from engine.collection.x_instagram import XConnector, normalise_x_payload, InstagramConnector
from engine.collection.guard import check_min_count
from engine.clean.pipeline import apply_cleaning_chain

logger = logging.getLogger(__name__)


def run_collection(
    settings: Settings, data_dir: Path, target_source: str | None = None, acknowledge_low: bool = False
) -> None:
    """Run collection for configured sources."""
    runs_dir = data_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    manifest_path = runs_dir / run_id / "manifest.json"
    manifest = Manifest(run_id, manifest_path)
    
    logger.info(f"Starting collection run {run_id}")

    def _write_parquet(v_list: list[Verbatim], run_id: str, is_quarantine: bool = False):
        if not v_list:
            return
        # A small helper to write to quarantine vs clean partition
        # Currently write_verbatims_to_parquet writes to data/parquet/source=.../brand=...
        # Let's adjust the path for quarantine by overriding brand or using a different folder.
        # But wait, T-P2-13 says "written to quarantine.parquet instead of {run_id}.parquet".
        # Let's pass a suffix or folder to write_verbatims_to_parquet.
        # It's simpler to just write it manually or let the caller handle it.
        pass

    try:
        manifest.record_stage_start("collection")
        completed_sources = manifest.state.get("completed_sources", [])
        
        for source_cfg in settings.sources:
            if target_source and source_cfg.source != target_source:
                continue
                
            source_key = f"{source_cfg.source}_{source_cfg.brand}"
            if source_key in completed_sources:
                logger.info(f"Skipping already completed source {source_key}")
                continue

                
            if source_cfg.source == "play_store":
                pkg = source_cfg.params.get("play_package")
                if not pkg:
                    logger.error(f"Missing play_package for {source_cfg.brand}, skipping.")
                    continue
                    
                connector = PlayStoreConnector(
                    brand=source_cfg.brand,
                    play_package=pkg,
                    data_dir=data_dir,
                    max_pages_per_band=20,  # Cap for safety during spike
                )
                normaliser = normalise_play_store_review

            elif source_cfg.source == "app_store":
                app_id = source_cfg.params.get("app_id")
                if not app_id:
                    logger.error(f"Missing app_id for {source_cfg.brand}, skipping.")
                    continue
                connector = AppStoreConnector(
                    brand=source_cfg.brand,
                    data_dir=data_dir,
                    app_id=app_id,
                    locale=source_cfg.params.get("locale", "in"),
                )
                normaliser = normalise_app_store_review

            elif source_cfg.source == "reddit":
                connector = RedditConnector(
                    brand=source_cfg.brand,
                    data_dir=data_dir,
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    user_agent=settings.reddit_user_agent,
                    subreddits=source_cfg.params.get("subreddits", []),
                    queries=source_cfg.params.get("queries", []),
                )
                normaliser = normalise_reddit_payload
                
            elif source_cfg.source == "forum":
                connector = ForumConnector(
                    brand=source_cfg.brand,
                    data_dir=data_dir,
                    base_url=source_cfg.params.get("base_url", ""),
                    selectors=source_cfg.params.get("selectors", {}),
                )
                normaliser = normalise_forum_payload
                
            elif source_cfg.source == "youtube":
                connector = YouTubeConnector(
                    brand=source_cfg.brand,
                    data_dir=data_dir,
                    api_key=settings.gemini_api_key, # Or a separate YT API key if added to settings
                    video_ids=source_cfg.params.get("video_ids", []),
                )
                normaliser = normalise_youtube_payload
                
            elif source_cfg.source == "product_review":
                connector = ProductReviewConnector(
                    brand=source_cfg.brand,
                    data_dir=data_dir,
                    base_url=source_cfg.params.get("base_url", ""),
                    selectors=source_cfg.params.get("selectors", {}),
                    category=source_cfg.params.get("category", "unknown"),
                )
                normaliser = normalise_product_review_payload
                
            elif source_cfg.source == "x":
                connector = XConnector(
                    brand=source_cfg.brand,
                    data_dir=data_dir,
                    bearer_token=source_cfg.params.get("bearer_token"),
                )
                normaliser = normalise_x_payload
                
            elif source_cfg.source == "instagram":
                connector = InstagramConnector(
                    brand=source_cfg.brand,
                    data_dir=data_dir,
                )
                normaliser = lambda r, rid, ref: None # Yields nothing anyway
                
            else:
                logger.warning(f"Source {source_cfg.source} not implemented yet.")
                continue
                
            verbatims = []
            
            # 1. Load watermark for incremental collection
            since_ts = connector.load_watermark()
            logger.info(f"Collecting {source_cfg.source}/{source_cfg.brand} since {since_ts}")
            
            first_ts = None
            last_ts = None
            
            with RawArchiveWriter(run_id, source_cfg.source, source_cfg.brand, data_dir) as raw_writer:
                # Use target_max from config
                for raw_payload in connector.collect(since=since_ts, limit=source_cfg.target_max):
                    ref = raw_writer.write_payload(raw_payload)
                    v = normaliser(raw_payload, run_id, ref)
                    if v is not None:
                        verbatims.append(v)
                        dt = v.review_date if v.review_date else v.collected_at
                        if dt:
                            if first_ts is None or dt < first_ts:
                                first_ts = dt
                            if last_ts is None or dt > last_ts:
                                last_ts = dt
                    
            logger.info(f"Collected {len(verbatims)} raw records for {source_cfg.source}/{source_cfg.brand}")
            
            # Record collection window
            if first_ts and last_ts:
                windows = manifest.state.get("collection_windows", {})
                windows[source_key] = {
                    "start": first_ts.isoformat(),
                    "end": last_ts.isoformat()
                }
                manifest.state["collection_windows"] = windows
                
            # Update watermark if we collected new data
            if last_ts:
                connector.save_watermark(last_ts)
            
            # Minimum count guard (except for intentionally empty gaps or best-efforts)
            if source_cfg.source not in ("x", "instagram"):
                check_min_count(
                    source_cfg.source, source_cfg.brand, len(verbatims), source_cfg.min_expected, acknowledge_low
                )
                
            # Quota shortfall reporting (T-P2-17)
            if source_cfg.target_min is not None and len(verbatims) < source_cfg.target_min:
                shortfall = source_cfg.target_min - len(verbatims)
                logger.warning(
                    f"Shortfall in {source_key}: collected {len(verbatims)}, target_min {source_cfg.target_min}. "
                    f"Under-represented source!"
                )
                shortfalls = manifest.state.get("quota_shortfalls", {})
                shortfalls[source_key] = {
                    "collected": len(verbatims),
                    "target_min": source_cfg.target_min,
                    "shortfall": shortfall,
                    "bias_consequence": "Potential under-representation of reasoning/sentiment from this source."
                }
                manifest.state["quota_shortfalls"] = shortfalls
            
            # Clean the verbatims
            clean_verbatims, quarantined, collapsed_count = apply_cleaning_chain(verbatims, data_dir)
            
            logger.info(
                f"Cleaning stats: in={len(verbatims)} clean={len(clean_verbatims)} "
                f"quarantined={len(quarantined)} collapsed={collapsed_count}"
            )
            
            # Check uniqueness on the clean output
            if clean_verbatims:
                assert_unique_ids(clean_verbatims)
                # Write to parquet
                write_verbatims_to_parquet(clean_verbatims, data_dir, run_id)
                
            if quarantined:
                # Write quarantine to quarantine_{run_id}.parquet
                write_verbatims_to_parquet(quarantined, data_dir, f"quarantine_{run_id}")
                
            # Mark source as complete and flush manifest
            completed_sources.append(source_key)
            manifest.state["completed_sources"] = completed_sources
            manifest.save()
            
        manifest.complete("success")
        logger.info(f"Collection run {run_id} completed successfully.")
        
    except Exception as e:
        logger.error(f"Collection run {run_id} failed: {e}")
        manifest.complete("failed")
        raise
