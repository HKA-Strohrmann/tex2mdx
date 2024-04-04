from asyncio.queues import Queue
import aiohttp
from pydantic import BaseModel

from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func

from arxiv.db import get_db
from arxiv.db.models import Metadata
from arxiv.identifier import Identifier

class ConvertData (BaseModel):
    paper_id: str
    version: int
    single_file: bool


async def worker (url: str, queue: Queue):
    async with aiohttp.ClientSession() as session:
        while True:
            convert_data: ConvertData = await queue.get()

            if convert_data is None:
                queue.task_done()
                break

            async with session.post(url, json=convert_data.json()) as response:
                await response.text

            queue.task_done()

class ConvertDataIterator:

    def __init__ (self):
        with get_db() as session:
            self.current_meta_id = session.scalar(
                func.max(Metadata.metadata_id)
            )
        
    def __iter__ (self) -> 'ConvertDataIterator':
        return self
    
    def __next__ (self) -> ConvertData:
        with get_db() as session:
            while self.current_meta_id >= 0:
                try:
                    item = session.scalar (
                        select(Metadata.paper_id, Metadata.version, Metadata.source_flags, Metadata.source_format, Metadata.is_withdrawn)
                        .filter(Metadata.metadata_id == self.current_meta_id)
                    )
                    if item is None:
                        self.current_meta_id -= 1
                        continue
                    paper_id, version, source_flags, source_format, is_withdrawn = item
                    if is_withdrawn or not 'tex' in source_format:
                        self.current_meta_id -= 1
                        continue
                    return ConvertData(
                        paper_id=paper_id,
                        version=version,
                        single_file=('1' in source_flags)
                    )
                except:
                    self.current_meta_id -= 1
                    continue

async def scheduler():
    worker_urls = [
        
    ]
