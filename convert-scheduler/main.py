from typing import Optional
import random
import logging
import argparse
import asyncio
from asyncio.queues import Queue
import aiohttp
from pydantic import BaseModel

from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func

from arxiv.db.models import Metadata
from arxiv.db import get_db, SessionLocal

from config import settings

logger = logging.getLogger("convert_scheduler_log")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(settings.LOG_PATH)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

class ConvertData (BaseModel):
    paper_id: str
    version: int
    single_file: bool

class ConvertDataIterator:

    def __init__ (self, starting_meta_id: Optional[int] = None):
        if starting_meta_id is None:
            with get_db() as session:
                self.current_meta_id = session.scalar(
                    select(func.max(Metadata.metadata_id))
                )
        else:
            self.current_meta_id = starting_meta_id
        print (self.current_meta_id)
        
    def __iter__ (self) -> 'ConvertDataIterator':
        return self
    
    def __next__ (self) -> ConvertData:
        with get_db() as session:
            while self.current_meta_id >= 0:
                try:
                    item = session.execute (
                        select(Metadata.paper_id, Metadata.version, Metadata.source_flags, Metadata.source_format, Metadata.is_withdrawn)
                        .filter(Metadata.metadata_id == self.current_meta_id)
                    ).first()
                    if item is None:
                        continue
                    paper_id, version, source_flags, source_format, is_withdrawn = item._t
                    if is_withdrawn or not 'tex' in source_format:
                        continue
                    return ConvertData(
                        paper_id=paper_id,
                        version=version,
                        single_file=('1' in source_flags)
                    )
                except:
                    continue
                finally:
                    self.current_meta_id -= 1
        raise StopIteration

async def scheduler(args):

    async def worker (url: str, queue: Queue, args):
        print (f"STARTING WORKER {url}")
        async with aiohttp.ClientSession() as session:
            while True:
                convert_data: ConvertData = await queue.get()

                if convert_data is None:
                    queue.task_done()
                    break
                
                print (f'SENDING {convert_data} to {url}')
                logger.info(f'SENDING {convert_data} to {url}')
                if not args.dry_run:
                    async with session.post(url, json=convert_data.json()) as response:
                        await response.text
                else:
                    await asyncio.sleep(random.randint(1, 5))
                queue.task_done()

    iterator = ConvertDataIterator(args.start_meta_id)
    worker_urls = list(map(
        lambda x: 'https://' + x + settings.CONVERT_PATH,
        [
            'web5.arxiv.org',
            'web6.arxiv.org',
            'web7.arxiv.org',
            'web8.arxiv.org',
            'web9.arxiv.org',
            'web10.arxiv.org',
            'arxiv-sync.serverfarm.cornell.edu'
        ]
    ))

    max_q_size = len(worker_urls)
    queue = Queue(maxsize=max_q_size)

    workers = [asyncio.create_task(worker(url, queue, args)) for url in worker_urls]

    while True:
        if queue.qsize() < max_q_size:
            try:
                conv_data = next(iterator)
                await queue.put(conv_data)
            except StopIteration:
                break
        else:
            await asyncio.sleep(1)

    await queue.join()

    for _ in range(max_q_size):
        await queue.put(None)

    for w in workers:
        await w

async def main(args):
    await scheduler(args)

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description='Convert entire arXiv corpus to HTML by scheduling conversions on CIT machines',
    )
    parser.add_argument('-n', '--dry-run', 
                        action='store_true',
                        help='Log requests sent without sending them')
    parser.add_argument('-s', '--start-meta-id',
                        type=int, default=None,
                        help="An optional metadata id to start at (counting down from)")
    args = parser.parse_args()

    asyncio.run(main(args))