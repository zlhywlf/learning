import asyncio
import logging

from twisted.internet.defer import Deferred

logger = logging.getLogger(__name__)


def _set_result_unless_cancelled(fut, result):
    logging.info("=" * 10 + ":::\t" + result)
    fut.callback(result)


async def sleep(msg:str,s: int) -> None:
    loop = asyncio.get_running_loop()
    future = Deferred()
    loop.call_later(s, _set_result_unless_cancelled, future, f"sleep{s}\t{msg}")
    await future
