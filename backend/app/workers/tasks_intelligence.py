import re
import datetime
from celery.utils.log import get_task_logger
from app.workers.celery_app import celery_app
from app.core.database import SyncSessionLocal
from app.models.models import CrawlJob, ScrapedRecord, IntelligenceReport

logger = get_task_logger(__name__)

@celery_app.task(name="app.workers.tasks_intelligence.generate_job_intelligence")
def generate_job_intelligence(job_id: str):
    """Aggregates all scraped records in a job and produces actionable market/data intelligence"""
    logger.info(f"[Intelligence Engine] Generating insights for job {job_id}")
    session = SyncSessionLocal()
    try:
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            logger.warning(f"[Intelligence Engine] Job {job_id} not found, skipping.")
            return

        # Skip if a report already exists to prevent duplicates
        existing_report = session.query(IntelligenceReport).filter(IntelligenceReport.job_id == job_id).first()
        if existing_report:
            logger.info(f"[Intelligence Engine] Report already exists for job {job_id}, skipping.")
            return

        records = session.query(ScrapedRecord).filter(ScrapedRecord.job_id == job_id).all()
        if not records:
            logger.warning(f"[Intelligence Engine] No records found for job {job_id}, skipping.")
            return

        avg_latency = round(sum(r.response_time_ms or 0 for r in records) / len(records), 2)
        total_records = len(records)

        # Build status and node distribution
        status_dist = {}
        node_dist = {}
        for r in records:
            st = str(r.http_status)
            status_dist[st] = status_dist.get(st, 0) + 1
            node_key = r.worker_node or "unknown"
            node_dist[node_key] = node_dist.get(node_key, 0) + 1

        metrics = {
            "total_records_analyzed": total_records,
            "average_response_time_ms": avg_latency,
            "success_rate_percentage": round(
                (sum(1 for r in records if r.http_status == 200) / total_records) * 100, 1
            ),
            "status_distribution": status_dist,
            "worker_node_distribution": node_dist,
        }

        # ─── E-Commerce ───────────────────────────────────────────────
        if job.crawler_type == "ecommerce":
            prices = []
            in_stock_count = 0

            for r in records:
                sd = r.structured_data or {}
                # crawler_engine stores the raw price string in "price"
                raw_price = sd.get("price") or sd.get("detected_price")
                if raw_price:
                    # Strip currency symbols and commas then parse
                    cleaned = re.sub(r"[^\d.]", "", str(raw_price).replace(",", "."))
                    try:
                        prices.append(float(cleaned))
                    except ValueError:
                        pass

                avail = sd.get("availability", "").lower()
                if "out" not in avail:           # "in stock" or empty → treat as in stock
                    in_stock_count += 1

            if prices:
                metrics["pricing_intelligence"] = {
                    "min_price": round(min(prices), 2),
                    "max_price": round(max(prices), 2),
                    "average_price": round(sum(prices) / len(prices), 2),
                    "total_priced_items": len(prices),
                    "in_stock_ratio": round(in_stock_count / total_records, 2),
                }
                avg_p = metrics["pricing_intelligence"]["average_price"]
                stock_pct = round((in_stock_count / total_records) * 100, 1)
                summary = (
                    f"E-Commerce intelligence completed across {total_records} items. "
                    f"Avg Price: ${avg_p}. Stock Availability: {stock_pct}%."
                )
            else:
                summary = (
                    f"E-Commerce crawl completed across {total_records} pages. "
                    f"No parseable price data was found — try adding CSS selectors for the price element."
                )

        # ─── News / Sentiment ─────────────────────────────────────────
        elif job.crawler_type == "news":
            sentiment_scores = []
            sentiment_labels = {"positive": 0, "neutral": 0, "negative": 0}
            all_entities = []

            for r in records:
                sd = r.structured_data or {}
                # crawler_engine stores polarity as "sentiment_polarity"
                score = sd.get("sentiment_polarity") or sd.get("sentiment_score")
                if score is not None:
                    try:
                        score = float(score)
                        sentiment_scores.append(score)
                        if score > 0.05:
                            sentiment_labels["positive"] += 1
                        elif score < -0.05:
                            sentiment_labels["negative"] += 1
                        else:
                            sentiment_labels["neutral"] += 1
                    except (ValueError, TypeError):
                        pass
                all_entities.extend(sd.get("key_entities", []))

            avg_sentiment = (
                round(sum(sentiment_scores) / len(sentiment_scores), 3)
                if sentiment_scores else 0.0
            )
            metrics["news_intelligence"] = {
                "overall_sentiment_score": avg_sentiment,
                "sentiment_breakdown": sentiment_labels,
                "top_mentioned_entities": list(dict.fromkeys(all_entities))[:10],
            }
            tone = "Bullish/Positive" if avg_sentiment > 0.05 else "Bearish/Negative" if avg_sentiment < -0.05 else "Neutral"
            summary = (
                f"News analysis completed over {total_records} articles. "
                f"Overall Sentiment Polarity: {avg_sentiment} ({tone})."
            )

        # ─── Schema.org / JSON-LD ─────────────────────────────────────
        elif job.crawler_type == "schema":
            schema_types = {}
            for r in records:
                sd = r.structured_data or {}
                for schema in sd.get("schemas", []):
                    t = schema.get("@type", "Unknown")
                    schema_types[t] = schema_types.get(t, 0) + 1
            metrics["schema_types"] = schema_types
            summary = (
                f"Schema.org / JSON-LD extraction completed across {total_records} pages. "
                f"Found {len(schema_types)} distinct schema types: {', '.join(list(schema_types.keys())[:5]) or 'none detected'}."
            )

        # ─── Generic ──────────────────────────────────────────────────
        else:
            avg_words = round(
                sum(r.structured_data.get("word_count", 0) for r in records if r.structured_data) / total_records, 0
            ) if total_records > 0 else 0
            metrics["generic_stats"] = {"average_word_count_per_page": avg_words}
            summary = (
                f"General crawl intelligence synthesized. Analyzed {total_records} URLs "
                f"across {len(node_dist)} distributed worker node(s). "
                f"Average page word count: {int(avg_words)}."
            )

        report = IntelligenceReport(
            job_id=job.id,
            report_type=f"{job.crawler_type}_intelligence",
            metrics=metrics,
            summary_text=summary
        )
        session.add(report)
        session.commit()
        logger.info(f"[Intelligence Engine] Report generated successfully for job {job_id}")

    except Exception as e:
        try:
            session.rollback()
        except Exception:
            pass
        logger.exception(f"[Intelligence Engine] Error generating intelligence for job {job_id}: {e}")
    finally:
        try:
            session.close()
        except Exception:
            pass
