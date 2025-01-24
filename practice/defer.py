from twisted.internet.asyncioreactor import AsyncioSelectorReactor
from twisted.internet.main import installReactor
from twisted.internet.defer import Deferred,DeferredList
import asyncio
import platform
import asyncio.futures
import time

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
reactor = AsyncioSelectorReactor()
installReactor(reactor)


def request(msg: str) -> Deferred:
    d = Deferred()
    reactor.callLater(1, d.callback, msg)
    d.addCallback(print)
    return d


def _set_result_unless_cancelled(fut, result):
    print("=" * 30)
    fut.callback(result)


async def task(msg: str,s:int) -> str:
    loop = asyncio.get_running_loop()
    future = Deferred()
    loop.call_later(s, _set_result_unless_cancelled, future, f"app{s}")
    res = await future
    print(res)
    return msg + f" async{s}"


def request_async(msg: str) -> Deferred:
    request(msg)
    s = time.time()
    d = Deferred.fromCoroutine(task(msg,2))
    d.addBoth(print)
    d2 = Deferred.fromCoroutine(task(msg,3))
    d2.addBoth(print)
    return DeferredList([d,d2]).addCallback(lambda _:print(time.time()-s)).addBoth(lambda _: reactor.stop())


reactor.callLater(1, request_async, "hello world")
reactor.run()
