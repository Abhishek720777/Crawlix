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
            return

        # Skip if a report already exists to prevent duplicates
        existing_report = session.query(IntelligenceReport).filter(IntelligenceReport.job_id == job_id).first()
        if existing_report:
            logger.info(f"[Intelligence Engine] Report already exists for job {job_id}, skipping.")
            return

        records = session.query(ScrapedRecord).filter(ScrapedRecord.job_id == job_id).all()
        if not records:
            logger.warning(f"[Intelligence Engine] No records found for job {job_id}, skipping intelligence generation.")
            return

        avg_latency = round(sum(r.response_time_ms for r in records) / len(records), 2)
        total_records = len(records)

        metrics = {
            "total_records_analyzed": total_records,
            "average_response_time_ms": avg_latency,
            "success_rate_percentage": round((sum(1 for r in records if r.http_status == 200) / total_records) * 100, 1),
            "status_distribution": {},
            "worker_node_distribution": {},
        }

        # Status distribution
        for r in records:
            st = str(r.http_status)
            metrics["status_distribution"][st] = metrics["status_distribution"].get(st, 0) + 1
            metrics["worker_node_distribution"][r.worker_node] = metrics["worker_node_distribution"].get(r.worker_node, 0) + 1

        # Domain/Preset specific analysis
        if job.crawler_type == "ecommerce":
            prices = []
            in_stock_count = 0
            for r in records:
                if r.structured_data:
                    p = r.structured_data.get("detected_price")
                    if p:
                        prices.append(float(p))
                    if r.structured_data.get("in_stock", True):
                        in_stock_count += 1

            if prices:
                metrics["pricing_intelligence"] = {
                    "min_price": min(prices),
                    "max_price": max(prices),
                    "average_price": round(sum(prices) / len(prices), 2),
                    "total_priced_items": len(prices),
                    "in_stock_ratio": round(in_stock_count / total_records, 2)
                }
            summary = f"E-Commerce intelligence completed across {total_records} items. Avg Price: ${metrics.get('pricing_intelligence', {}).get('average_price', 'N/A')}. Stock Availability: {round((in_stock_count/total_records)*100, 1)}%."

        elif job.crawler_type == "news":
            sentiment_scores = []
            sentiment_labels = {"positive": 0, "neutral": 0, "negative": 0}
            all_entities = []

            for r in records:
                if r.structured_data:
                    score = r.structured_data.get("sentiment_score")
                    lbl = r.structured_data.get("sentiment_label", "neutral")
                    if score is not None:
                        sentiment_scores.append(score)
                    sentiment_labels[lbl] = sentiment_labels.get(lbl, 0) + 1
                    all_entities.extend(r.structured_data.get("key_entities", []))

            avg_sentiment = round(sum(sentiment_scores) / len(sentiment_scores), 3) if sentiment_scores else 0.0
            metrics["news_intelligence"] = {
                "overall_sentiment_score": avg_sentiment,
                "sentiment_breakdown": sentiment_labels,
                "top_mentioned_entities": all_entities[:10]
            }
            summary = f"News analysis completed over {total_records} articles. Overall Sentiment Polarity: {avg_sentiment} ({'Bullish/Positive' if avg_sentiment > 0.05 else 'Bearish/Negative' if avg_sentiment < -0.05 else 'Neutral'})."

        else:
            summary = f"General crawl intelligence synthesized. Analyzed {total_records} URLs across {len(metrics['worker_node_distribution'])} distributed worker nodes."

        report = IntelligenceReport(
            job_id=job.id,
            report_type=f"{job.crawler_type}_intelligence",
            metrics=metrics,
            summary_text=summary
        )
        session.add(report)
        session.commit()
        logger.info(f"[Intelligence Engine] Report generated for job {job_id}")

    except Exception as e:
        session.rollback()
        logger.exception(f"Error generating intelligence for job {job_id}: {e}")
    finally:
        session.close()
