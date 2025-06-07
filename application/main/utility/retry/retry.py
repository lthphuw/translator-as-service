from logging import Logger

from tenacity import retry as r
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential


def retry(service: str, logger: Logger, stop_after=3):
    return r(
        stop=stop_after_attempt(stop_after),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
        before_sleep=lambda r: logger.warning(
            f"Retrying {service} due to: {r.outcome.exception()}"  # type: ignore
        ),
    )
