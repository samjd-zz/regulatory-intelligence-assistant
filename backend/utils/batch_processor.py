"""
Batch Processing Utilities

Provides efficient batch processing capabilities for document ingestion,
search operations, and RAG queries with progress tracking and error handling.

Features:
- Batch document upload and indexing
- Bulk search operations
- Parallel processing with thread/process pools
- Progress tracking and reporting
- Error handling and retry logic
- Rate limiting and throttling
- Result aggregation and reporting

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import asyncio
import time
from typing import List, Dict, Any, Callable, Optional, TypeVar, Generic, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from enum import Enum
import logging
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


# === Batch Job Status ===

class BatchJobStatus(str, Enum):
    """Status of a batch job"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Some items succeeded, some failed


@dataclass
class BatchJobProgress:
    """Progress tracking for batch jobs"""
    job_id: str
    status: BatchJobStatus
    total_items: int
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    current_item: Optional[str] = None
    error_messages: List[str] = field(default_factory=list)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100

    @property
    def elapsed_time_seconds(self) -> float:
        """Calculate elapsed time"""
        if not self.started_at:
            return 0.0
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'successful_items': self.successful_items,
            'failed_items': self.failed_items,
            'progress_percentage': round(self.progress_percentage, 2),
            'success_rate': round(self.success_rate, 2),
            'elapsed_time_seconds': round(self.elapsed_time_seconds, 2),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'current_item': self.current_item,
            'error_count': len(self.error_messages),
            'recent_errors': self.error_messages[-5:]  # Last 5 errors
        }


@dataclass
class BatchResult(Generic[R]):
    """Result of a batch operation"""
    job_id: str
    successful_results: List[R] = field(default_factory=list)
    failed_items: List[Dict[str, Any]] = field(default_factory=list)
    total_items: int = 0
    execution_time_seconds: float = 0.0

    @property
    def success_count(self) -> int:
        return len(self.successful_results)

    @property
    def failure_count(self) -> int:
        return len(self.failed_items)

    @property
    def success_rate(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self.success_count / self.total_items) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'total_items': self.total_items,
            'successful_items': self.success_count,
            'failed_items': self.failure_count,
            'success_rate': round(self.success_rate, 2),
            'execution_time_seconds': round(self.execution_time_seconds, 2),
            'results': self.successful_results,
            'failures': self.failed_items
        }


# === Batch Processor ===

class BatchProcessor(Generic[T, R]):
    """
    Generic batch processor for parallel processing of items

    Supports:
    - Thread-based parallelism for I/O-bound tasks
    - Process-based parallelism for CPU-bound tasks
    - Progress tracking
    - Error handling and retry logic
    - Rate limiting
    """

    def __init__(
        self,
        max_workers: int = 5,
        use_processes: bool = False,
        rate_limit_per_second: Optional[float] = None,
        retry_attempts: int = 1,
        retry_delay_seconds: float = 1.0
    ):
        """
        Initialize batch processor

        Args:
            max_workers: Maximum parallel workers
            use_processes: Use ProcessPoolExecutor instead of ThreadPoolExecutor
            rate_limit_per_second: Maximum items to process per second
            retry_attempts: Number of retry attempts for failed items
            retry_delay_seconds: Delay between retries
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.rate_limit_per_second = rate_limit_per_second
        self.retry_attempts = retry_attempts
        self.retry_delay_seconds = retry_delay_seconds

        # Progress tracking
        self.progress_store: Dict[str, BatchJobProgress] = {}

        # Rate limiting
        self._last_request_time = 0.0
        self._min_interval = 1.0 / rate_limit_per_second if rate_limit_per_second else 0.0

    def _generate_job_id(self, items: List[T]) -> str:
        """Generate unique job ID"""
        data = f"{len(items)}:{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def _apply_rate_limit(self):
        """Apply rate limiting"""
        if self._min_interval > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()

    def _process_item_with_retry(
        self,
        item: T,
        process_func: Callable[[T], R],
        job_id: str
    ) -> tuple[bool, Optional[R], Optional[str]]:
        """
        Process a single item with retry logic

        Returns:
            Tuple of (success, result, error_message)
        """
        for attempt in range(self.retry_attempts):
            try:
                # Apply rate limiting
                self._apply_rate_limit()

                # Process item
                result = process_func(item)
                return True, result, None

            except Exception as e:
                error_msg = f"Attempt {attempt + 1}/{self.retry_attempts} failed: {str(e)}"
                logger.warning(error_msg)

                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay_seconds * (attempt + 1))
                else:
                    return False, None, str(e)

        return False, None, "Max retries exceeded"

    def process_batch(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        job_id: Optional[str] = None
    ) -> BatchResult[R]:
        """
        Process a batch of items in parallel

        Args:
            items: List of items to process
            process_func: Function to process each item
            job_id: Optional job ID (auto-generated if not provided)

        Returns:
            BatchResult with successful and failed items
        """
        if not items:
            return BatchResult(job_id="empty", total_items=0)

        # Generate job ID
        if not job_id:
            job_id = self._generate_job_id(items)

        # Initialize progress tracking
        progress = BatchJobProgress(
            job_id=job_id,
            status=BatchJobStatus.RUNNING,
            total_items=len(items),
            started_at=datetime.now()
        )
        self.progress_store[job_id] = progress

        start_time = time.time()
        successful_results = []
        failed_items = []

        try:
            # Choose executor
            ExecutorClass = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

            with ExecutorClass(max_workers=self.max_workers) as executor:
                # Submit all items
                future_to_item = {
                    executor.submit(self._process_item_with_retry, item, process_func, job_id): item
                    for item in items
                }

                # Process results as they complete
                for future in as_completed(future_to_item):
                    item = future_to_item[future]

                    try:
                        success, result, error_msg = future.result()

                        if success:
                            successful_results.append(result)
                            progress.successful_items += 1
                        else:
                            failed_items.append({
                                'item': str(item),
                                'error': error_msg
                            })
                            progress.failed_items += 1
                            progress.error_messages.append(error_msg)

                        progress.processed_items += 1

                        # Update estimated completion time
                        if progress.processed_items > 0:
                            avg_time = progress.elapsed_time_seconds / progress.processed_items
                            remaining = progress.total_items - progress.processed_items
                            est_remaining_seconds = avg_time * remaining
                            progress.estimated_completion = datetime.now()

                    except Exception as e:
                        logger.error(f"Unexpected error processing item: {e}")
                        failed_items.append({
                            'item': str(item),
                            'error': f"Unexpected error: {str(e)}"
                        })
                        progress.failed_items += 1
                        progress.processed_items += 1

            # Update final status
            if progress.failed_items == 0:
                progress.status = BatchJobStatus.COMPLETED
            elif progress.successful_items == 0:
                progress.status = BatchJobStatus.FAILED
            else:
                progress.status = BatchJobStatus.PARTIAL

            progress.completed_at = datetime.now()

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            progress.status = BatchJobStatus.FAILED
            progress.completed_at = datetime.now()
            raise

        execution_time = time.time() - start_time

        return BatchResult(
            job_id=job_id,
            successful_results=successful_results,
            failed_items=failed_items,
            total_items=len(items),
            execution_time_seconds=execution_time
        )

    def get_progress(self, job_id: str) -> Optional[BatchJobProgress]:
        """Get progress for a batch job"""
        return self.progress_store.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running batch job

        Note: Cancellation is best-effort and may not stop immediately
        """
        if job_id in self.progress_store:
            progress = self.progress_store[job_id]
            if progress.status == BatchJobStatus.RUNNING:
                progress.status = BatchJobStatus.CANCELLED
                progress.completed_at = datetime.now()
                return True
        return False


# === Async Batch Processor ===

class AsyncBatchProcessor(Generic[T, R]):
    """
    Async batch processor for async operations

    Uses asyncio for concurrent processing of async functions
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        rate_limit_per_second: Optional[float] = None
    ):
        """
        Initialize async batch processor

        Args:
            max_concurrent: Maximum concurrent tasks
            rate_limit_per_second: Maximum items to process per second
        """
        self.max_concurrent = max_concurrent
        self.rate_limit_per_second = rate_limit_per_second
        self.progress_store: Dict[str, BatchJobProgress] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch(
        self,
        items: List[T],
        process_func: Callable[[T], Coroutine[Any, Any, R]],
        job_id: Optional[str] = None
    ) -> BatchResult[R]:
        """
        Process a batch of items asynchronously

        Args:
            items: List of items to process
            process_func: Async function to process each item
            job_id: Optional job ID

        Returns:
            BatchResult with successful and failed items
        """
        if not items:
            return BatchResult(job_id="empty", total_items=0)

        # Generate job ID
        if not job_id:
            data = f"{len(items)}:{time.time()}"
            job_id = hashlib.md5(data.encode()).hexdigest()[:16]

        # Initialize progress
        progress = BatchJobProgress(
            job_id=job_id,
            status=BatchJobStatus.RUNNING,
            total_items=len(items),
            started_at=datetime.now()
        )
        self.progress_store[job_id] = progress

        start_time = time.time()
        successful_results = []
        failed_items = []

        async def process_with_semaphore(item: T):
            """Process item with concurrency control"""
            async with self._semaphore:
                try:
                    result = await process_func(item)
                    return True, result, None
                except Exception as e:
                    return False, None, str(e)

        # Process all items concurrently
        tasks = [process_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks)

        # Aggregate results
        for item, (success, result, error) in zip(items, results):
            if success:
                successful_results.append(result)
                progress.successful_items += 1
            else:
                failed_items.append({
                    'item': str(item),
                    'error': error
                })
                progress.failed_items += 1
                progress.error_messages.append(error)

            progress.processed_items += 1

        # Update status
        if progress.failed_items == 0:
            progress.status = BatchJobStatus.COMPLETED
        elif progress.successful_items == 0:
            progress.status = BatchJobStatus.FAILED
        else:
            progress.status = BatchJobStatus.PARTIAL

        progress.completed_at = datetime.now()

        execution_time = time.time() - start_time

        return BatchResult(
            job_id=job_id,
            successful_results=successful_results,
            failed_items=failed_items,
            total_items=len(items),
            execution_time_seconds=execution_time
        )


# === Chunked Batch Processor ===

class ChunkedBatchProcessor:
    """
    Process large batches in chunks to avoid memory issues

    Useful for very large datasets that don't fit in memory
    """

    def __init__(self, chunk_size: int = 100):
        """
        Initialize chunked processor

        Args:
            chunk_size: Number of items per chunk
        """
        self.chunk_size = chunk_size

    def process_in_chunks(
        self,
        items: List[T],
        process_chunk_func: Callable[[List[T]], List[R]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[R]:
        """
        Process items in chunks

        Args:
            items: All items to process
            process_chunk_func: Function to process a chunk
            progress_callback: Optional callback(processed, total)

        Returns:
            List of all results
        """
        all_results = []
        total_items = len(items)
        processed = 0

        # Process in chunks
        for i in range(0, total_items, self.chunk_size):
            chunk = items[i:i + self.chunk_size]

            try:
                chunk_results = process_chunk_func(chunk)
                all_results.extend(chunk_results)

                processed += len(chunk)

                if progress_callback:
                    progress_callback(processed, total_items)

            except Exception as e:
                logger.error(f"Chunk processing failed at offset {i}: {e}")
                raise

        return all_results


# === Example Usage ===

if __name__ == "__main__":
    # Example 1: Batch processing with threads
    def process_number(n: int) -> int:
        """Example processing function"""
        time.sleep(0.1)  # Simulate work
        return n * 2

    processor = BatchProcessor[int, int](max_workers=5)
    items = list(range(20))

    result = processor.process_batch(items, process_number)
    print(f"Processed {result.success_count}/{result.total_items} items")
    print(f"Success rate: {result.success_rate:.1f}%")
    print(f"Execution time: {result.execution_time_seconds:.2f}s")

    # Example 2: Async batch processing
    async def async_process_example():
        async def process_item_async(item: str) -> str:
            await asyncio.sleep(0.1)
            return item.upper()

        async_processor = AsyncBatchProcessor[str, str](max_concurrent=10)
        items = [f"item{i}" for i in range(20)]

        result = await async_processor.process_batch(items, process_item_async)
        print(f"Async processed {result.success_count}/{result.total_items} items")

    # asyncio.run(async_process_example())

    # Example 3: Chunked processing
    def process_chunk(chunk: List[int]) -> List[int]:
        """Process a chunk of items"""
        return [x * 2 for x in chunk]

    chunked_processor = ChunkedBatchProcessor(chunk_size=5)
    large_items = list(range(100))

    results = chunked_processor.process_in_chunks(
        large_items,
        process_chunk,
        progress_callback=lambda p, t: print(f"Progress: {p}/{t}")
    )
    print(f"Chunked processing completed: {len(results)} results")
