"""Entry point for scheduled Lambda functions.

This module is the handler entry point for EventBridge-triggered Lambda
functions. It intentionally avoids importing the API app so scheduled jobs
only load the dependencies they need.
"""

from core.enrichment_service import get_enrichment_config, run_enrichment


def _get_batch_limit(event):
    if not isinstance(event, dict):
        return None

    value = event.get("batch_limit", event.get("enrichment_batch_limit"))
    if value is None:
        return None

    return int(value)


def lambda_run_enrichment_handler(event, context):
    """Lambda handler to enrich pending language-learning words.

    For manual test invocations, pass {"batch_limit": 5} to process up to
    five words without changing the scheduled job's configured default.
    """
    batch_limit = _get_batch_limit(event)
    if batch_limit is None:
        return run_enrichment()

    return run_enrichment(config=get_enrichment_config(batch_limit=batch_limit))
