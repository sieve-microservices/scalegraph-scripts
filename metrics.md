# Docker related metrics (Systemmetrics)

docker related metrics: https://docs.docker.com/v1.8/articles/runmetrics/

## docker_container_mem

doc: https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Resource_Management_Guide/sec-memory.html

- total_pgmafault
- cache: the amount of memory used by the processes of this control group that can be associated precisely with a block on a block device. When you read from and write to files on disk, this amount will increase. This will be the case if you use “conventional” I/O (open, read, write syscalls) as well as mapped files (with mmap). It also accounts for the memory used by tmpfs mounts, though the reasons are unclear.
- mapped_file: size of memory-mapped mapped files, including tmpfs (shmem), in bytes
- total_inactive_file: 
- pgpgout: Total number of kilobytes the system paged out to disk per second
- rss: the amount of memory that doesn’t correspond to anything on disk: stacks, heaps, and anonymous memory maps.
- total_mapped_file: 
- writeback
- unevictable: the amount of memory that cannot be reclaimed; generally, it will account for memory that has been “locked” with mlock. It is often used by crypto frameworks to make sure that secret keys and other sensitive material never gets swapped out to disk.
- pgpgin: Total number of kilobytes the system paged in from disk per second
- total_unevictable
- pgmajfault: indicate the number of times that a process of the cgroup triggered a “page fault” and a “major fault”, respectively. A page fault happens when a process accesses a part of its virtual memory space which is nonexistent or protected. The former can happen if the process is buggy and tries to access an invalid address (it will then be sent a SIGSEGV signal, typically killing it with the famous Segmentation fault message). The latter can happen when the process reads from a memory zone which has been swapped out, or which corresponds to a mapped file: in that case, the kernel will load the page from disk, and let the CPU complete the memory access. It can also happen when the process writes to a copy-on-write memory zone: likewise, the kernel will preempt the process, duplicate the memory page, and resume the write operation on the process` own copy of the page. “Major” faults happen when the kernel actually has to read the data from disk. When it just has to duplicate an existing page, or allocate an empty page, it’s a regular (or “minor”) fault.
- total_rss
- total_rss_huge
- total_writeback
- total_inactive_anon
- rss_huge
- hierarchical_memory_limit
- total_pgfault
- total_active_file
- active_anon: the amount of anonymous memory that has been identified has respectively active and inactive by the kernel. “Anonymous” memory is the memory that is not linked to disk pages. In other words, that’s the equivalent of the rss counter described above. In fact, the very definition of the rss counter is active_anon + inactive_anon - tmpfs (where tmpfs is the amount of memory used up by tmpfs filesystems mounted by this control group). Now, what’s the difference between “active” and “inactive”? Pages are initially “active”; and at regular intervals, the kernel sweeps over the memory, and tags some pages as “inactive”. Whenever they are accessed again, they are immediately retagged “active”. When the kernel is almost out of memory, and time comes to swap out to disk, the kernel will swap “inactive” pages.
- total_active_anon
- total_pgpgout
- total_cache
- inactive_anon: see active_anon
- active_file
- pgfault: pgmajfault
- inactive_file
- total_pgpgin
- max_usage
- usage
- failcnt
- limit

## docker_container_cpu

doc: https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Resource_Management_Guide/sec-cpu.html
doc: https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Resource_Management_Guide/sec-cpuacct.html

- throttling_periods: number of period intervals (as specified in cpu.cfs_period_us) that have elapsed.
- throttling_throttled_periods: Number of CPU throttling enforcements for a container
- throttling_throttled_time: Total time that a container’s CPU usage was throttled
- usage_in_kernelmode: CPU time consumed by tasks in system (kernel) mode.
- usage_in_usermode: CPU time consumed by tasks in user mode.
- usage_system: Percent of time that CPU is executing system calls on behalf of processes
- usage_total: Total cpu usage of the container
- usage_percent: (usage_total[t] - usage_total[t - 1]) / (usage_system[t] - usage_system[t - 1])

## docker_container_net

- interface statistic of eth0
- all numbers are summed up over time -> differencing required

- rx_dropped
- rx_bytes
- rx_errors
- tx_packets
- tx_dropped
- rx_packets
- tx_errors
- tx_bytes

## docker_container_blkio

doc: http://lxr.free-electrons.com/source/Documentation/cgroups/blkio-controller.txt?v=4.4


### io_serviced

Number of IOs (bio) issued to the disk by the group. These are further divided
by the type of operation - read or write, sync or async. First two fields
specify the major and minor number of the device, third field specifies the
operation type and the fourth field specifies the number of IOs.

### io_service_bytes

Number of bytes transferred to/from the disk by the group. These
are further divided by the type of operation - read or write, sync
or async. First two fields specify the major and minor number of the
device, third field specifies the operation type and the fourth field
specifies the number of bytes.

- io_service_bytes_recursive_async
- io_service_bytes_recursive_read
- io_service_bytes_recursive_sync
- io_service_bytes_recursive_total
- io_service_bytes_recursive_write
- io_serviced_recursive_async
- io_serviced_recursive_read
- io_serviced_recursive_sync
- io_serviced_recursive_total
- io_serviced_recursive_write

# Application specific metrics provied by telegraf

## haproxy

- qcur [..BS]: current queued requests. For the backend this reports the
-   number queued without a server assigned.
- qmax [..BS]: max value of qcur
- scur [LFBS]: current sessions
- smax [LFBS]: max sessions
- stot [LFBS]: cumulative number of connections
- bin [LFBS]: bytes in
- bout [LFBS]: bytes out
- dreq [LFB.]: requests denied because of security concerns.
  - For tcp this is because of a matched tcp-request content rule.
  - For http this is because of a matched http-request or tarpit rule.
- dresp [LFBS]: responses denied because of security concerns.
  - For http this is because of a matched http-request rule, or "option checkcache".
- ereq [LF..]: request errors. Some of the possible causes are:
   - early termination from the client, before the request has been sent.
   - read error from the client
   - client timeout
   - client closed connection
   - various bad requests from the client.
   - request was tarpitted.
- econ [..BS]: number of requests that encountered an error trying to
   -  connect to a backend server. The backend stat is the sum of the stat
   -  for all servers of that backend, plus any connection errors not
   -  associated with a particular server (such as the backend having no
   -  active servers).
- eresp [..BS]: response errors. srv_abrt will be counted here also.
   Some other errors are:
   - write error on the client socket (won't be counted for the server stat)
   - failure applying filters to the response.
- wretr [..BS]: number of times a connection to a server was retried.
- wredis [..BS]: number of times a request was redispatched to another server. The server value counts the number of times that server was switched away from.
- status [LFBS]: status (UP/DOWN/NOLB/MAINT/MAINT(via)...)
- active_servers [..BS]: number of active servers (backend), server is active (server)
- backup_servers [..BS]: number of backup servers (backend), server is backup (server)
- downtime [..BS]: total downtime (in seconds). The value for the backend is the downtime for the whole backend, not the sum of the server downtime.
- qlimit [...S]: configured maxqueue for the server, or nothing in the
- value is 0 (default, meaning no limit)
- throttle [...S]: current throttle percentage for the server, when slowstart is active, or no value if not in slowstart.
- lbtot [..BS]: total number of times a server was selected, either for new sessions, or when re-dispatching. The server counter is the number of times that server was selected.
- rate [.FBS]: number of sessions per second over last elapsed second
- rate_max [.FBS]: max number of new sessions per second
- check_duration [...S]: time in ms took to finish last health check
- hrsp_1xx [.FBS]: http responses with 1xx code
- hrsp_2xx [.FBS]: http responses with 2xx code
- hrsp_3xx [.FBS]: http responses with 3xx code
- hrsp_4xx [.FBS]: http responses with 4xx code
- hrsp_5xx [.FBS]: http responses with 5xx code
- req_rate [.F..]: HTTP requests per second over last elapsed second
- req_rate_max [.F..]: max number of HTTP requests per second observed
- req_tot [.F..]: total number of HTTP requests received
- cli_abrt [..BS]: number of data transfers aborted by the client
- srv_abrt [..BS]: number of data transfers aborted by the server
- (inc. in eresp)
- qtime [..BS]: the average queue time in ms over the 1024 last requests
- ctime [..BS]: the average connect time in ms over the 1024 last requests
- rtime [..BS]: the average response time in ms over the 1024 last requests
- (0 for TCP)
- ttime [..BS]: the average total session time in ms over the 1024 last requests

## redis

doc: http://redis.io/commands/INFO

- uptime_in_seconds: Number of seconds since Redis server start
- connected_clients: Number of client connections (excluding connections from slaves)
- used_memory: total number of bytes allocated by Redis using its allocator (either standard libc, jemalloc, or an alternative allocator such as tcmalloc)
- used_memory_rss: used_memory_rss: Number of bytes that Redis allocated as seen by the operating system (a.k.a resident set size). This is the number reported by tools such as top(1) and ps(1)
- used_memory_peak: used_memory_peak: Peak memory consumed by Redis (in bytes)
- used_memory_lua: Number of bytes used by the Lua engine
- rdb_changes_since_last_save: Number of changes since the last dump
- total_connections_received: Total number of connections accepted by the server
- total_commands_processed: Total number of commands processed by the server
- instantaneous_ops_per_sec:  Number of commands processed per second
- instantaneous_input_kbps
- instantaneous_output_kbps
- sync_full:
- sync_partial_ok
- sync_partial_err
- expired_keys: Total number of key expiration events
- evicted_keys: Number of evicted keys due to maxmemory limit
- keyspace_hits: Number of successful lookup of keys in the main dictionary
- keyspace_misses: Number of failed lookup of keys in the main dictionary
- pubsub_channels: Global number of pub/sub channels with client subscriptions
- pubsub_patterns: Global number of pub/sub pattern with client subscriptions
- latest_fork_usec: Duration of the latest fork operation in microseconds
- connected_slaves: Number of connected slaves
- master_repl_offset:
- master_last_io_seconds_ago: Number of seconds since the last interaction with master
- repl_backlog_active:
- repl_backlog_size
- repl_backlog_histlen
- mem_fragmentation_ratio: Ratio between used_memory_rss and used_memory
- used_cpu_sys: System CPU consumed by the Redis server
- used_cpu_user: User CPU consumed by the Redis server
- used_cpu_sys_children: System CPU consumed by the background processes
- used_cpu_user_children: User CPU consumed by the background processes

## mongodb

doc: https://docs.mongodb.com/v3.0/reference/command/serverStatus/

- active_reads
- active_writes
- commands_per_sec
- deletes_per_sec
- flushes_per_sec
- getmores_per_sec
- inserts_per_sec
- net_in_bytes
- net_out_bytes
- open_connections
- percent_cache_dirty
- percent_cache_used
- queries_per_sec
- queued_reads
- queued_writes
- resident_megabytes
- updates_per_sec
- vsize_megabytes
- ttl_deletes_per_sec
- ttl_passes_per_sec
- repl_lag
- jumbo_chunks

## postgresql

doc: https://www.postgresql.org/docs/9.2/static/monitoring-stats.html#PG-STAT-DATABASE-VIEW

- numbackends: Number of backends currently connected to this database. This is the only column in this view that returns a value reflecting current state; all other columns return the accumulated values since the last reset.
- xact_commit: Number of transactions in this database that have been committed
- xact_rollback: Number of transactions in this database that have been rolled back
- blks_read: Number of disk blocks read in this database
- blks_hit: Number of times disk blocks were found already in the buffer cache, so that a read was not necessary (this only includes hits in the PostgreSQL buffer cache, not the operating system's file system cache)
- tup_returned: Number of rows returned by queries in this database
- tup_fetched: Number of rows fetched by queries in this database
- tup_inserted: Number of rows inserted by queries in this database
- tup_updated: Number of rows updated by queries in this database
- tup_deleted: Number of rows deleted by queries in this database
- conflicts: Number of queries canceled due to conflicts with recovery in this database. (Conflicts occur only on standby servers; see pg_stat_database_conflicts for details.)
- temp_files: Number of temporary files created by queries in this database. All temporary files are counted, regardless of why the temporary file was created (e.g., sorting or hashing), and regardless of the log_temp_files setting.
- temp_bytes: Total amount of data written to temporary files by queries in this database. All temporary files are counted, regardless of why the temporary file was created, and regardless of the log_temp_files setting.
- deadlocks: Number of deadlocks detected in this database
- blk_read_time: Time spent reading data file blocks by backends in this database, in milliseconds
- blk_write_time: Time spent writing data file blocks by backends in this database, in milliseconds

# Statsd-metrics from source code

- *gauge*: Gauges are a constant data type. They are not subject to averaging, and they don’t change unless you change them. That is, once you set a gauge value, it will be a flat line on the graph until you change it again.
- *inc*: Counters are the most basic type. They are treated as a count of a type of event. They will continually increase unless you set delete_counters=true.
- *set*: Sets count the number of unique values passed to a key. For example, you could count the number of users accessing your system using users:<user_id>|s. No matter how many times the same user_id is sent, the count will only increase by 1.
- *timing*: Timers are meant to track how long something took. They are an invaluable tool for tracking application performance. The following aggregate measurements are made for timers:
   - statsd_<name>_lower: The lower bound is the lowest value statsd saw for that stat during that interval.
   - statsd_<name>_upper: The upper bound is the highest value statsd saw for that stat during that interval.
   - statsd_<name>_mean: The mean is the average of all values statsd saw for that stat during that interval.
   - statsd_<name>_stddev: The stddev is the sample standard deviation of all values statsd saw for that stat during that interval.
   - statsd_<name>_count: The count is the number of timings statsd saw for that stat during that interval. It is not averaged.
   - statsd_<name>_percentile_<P> The Pth percentile is a value x such that P% of all the values statsd saw for that stat during that time period are below x. The most common value that people use for P is the 90, this is a great number to try to optimize.


## Shared metric types
- *-open_connections.http.#{hostname} gauge
- *-open_connections.https.#{hostname}        gauge
- *-memory.rss      gauge
- *-memory.heaptotal        gauge
- *-memory.heapused gauge
- *-memory.gc-interval      gauge
- *-memory.cpu-time-bucket  gauge
- *-memory.gc-time  timing
- *-memory.gc-rss-freed     gauge
- *-memory.gc-heaptotal-freed       gauge
- *-memory.gc-heapused-freed        gauge
- *-event-loop-millsec  timing
- *-mongo-requests.#{collection}.#{type} timing

##  Service specific specific
- filestore-getFile	inc
- filestore-insertFile	inc
- filestore-copyFile	inc
- filestore-deleteFile	inc
- filestore-projectSize	inc
- web-user.logout	inc
- web-user.password-change	inc
- web-open_connections.socketio	gauge
- web-open_connections.http	gauge
- web-open_connections.https	gauge
- web-tpds.add-file	inc
- web-tpds.add-doc	inc
- web-tpds.move-entity	inc
- web-tpds.delete-entity	inc
- web-tpds.poll-dropbox	inc
- web-tpds.merge-update	inc
- web-tpds.delete-update	inc
- web-cloned-project	inc
- web-project-creation	inc
- web-email	inc
- web-startup	inc
- web-http-request	inc
- web-crawler.google	inc
- web-crawler.facebook	inc
- web-crawler.bing	inc
- web-doc-not-blocking	inc
- web-doc-blocking	inc
- web-doc-blocking	inc
- web-doc-not-blocking	inc
- web-http.open-sockets	gauge
- spelling-mongoCache-hit	inc
- spelling-mongoCache-miss	inc
- spelling-spelling-check	inc
- spelling-spelling-learn	inc
- spelling-aspellWorker-start-	inc
- spelling-aspellWorker-exit-	inc
- real-time-editor.join-project	inc
- real-time-editor.leave-project	inc
- real-time-editor.join-doc	inc
- real-time-editor.leave-doc	inc
- real-time-editor.update-client-position	inc
- real-time-editor.get-connected-users	inc
- real-time-editor.doc-update	inc
- real-time-editor.active-projects	set
- real-time-editor.active-users	set
- chat-editor.instant-message	inc
- doc-updater-doc-not-blocking	inc
- doc-updater-doc-blocking	inc
- doc-updater-doc-blocking	inc
- doc-updater-doc-not-blocking	inc


# Actual metrics from metadata.json

Some metric names are not known in advance as they
get created dynamically in the source code.
Therefor I included here the metrics, I have observed.

## chat
- chat-http-requests_room_project_id_messages_POST_201_count
- chat-http-requests_room_project_id_messages_POST_201_lower
- chat-http-requests_room_project_id_messages_POST_201_mean
- chat-http-requests_room_project_id_messages_POST_201_stddev
- chat-http-requests_room_project_id_messages_POST_201_upper
- chat-mongo-requests_sharelatex_messages_insert_count
- chat-mongo-requests_sharelatex_messages_insert_lower
- chat-mongo-requests_sharelatex_messages_insert_mean
- chat-mongo-requests_sharelatex_messages_insert_stddev
- chat-mongo-requests_sharelatex_messages_insert_upper
- chat-mongo-requests_sharelatex_rooms_insert_count
- chat-mongo-requests_sharelatex_rooms_insert_lower
- chat-mongo-requests_sharelatex_rooms_insert_mean
- chat-mongo-requests_sharelatex_rooms_insert_stddev
- chat-mongo-requests_sharelatex_rooms_insert_upper
- chat-mongo-requests_sharelatex_rooms_query_project_id_count
- chat-mongo-requests_sharelatex_rooms_query_project_id_lower
- chat-mongo-requests_sharelatex_rooms_query_project_id_mean
- chat-mongo-requests_sharelatex_rooms_query_project_id_stddev
- chat-mongo-requests_sharelatex_rooms_query_project_id_upper

## clsi
- clsi-compile-request_count
- clsi-compile-request_lower
- clsi-compile-request_mean
- clsi-compile-request_stddev
- clsi-compile-request_upper
- clsi-compiles
- clsi-compiles-succeeded
- clsi-http-requests_project_project_id_compile_POST_200_count
- clsi-http-requests_project_project_id_compile_POST_200_lower
- clsi-http-requests_project_project_id_compile_POST_200_mean
- clsi-http-requests_project_project_id_compile_POST_200_stddev
- clsi-http-requests_project_project_id_compile_POST_200_upper
- clsi-http-requests_project_project_id_output_*_GET_200_count
- clsi-http-requests_project_project_id_output_*_GET_200_lower
- clsi-http-requests_project_project_id_output_*_GET_200_mean
- clsi-http-requests_project_project_id_output_*_GET_200_stddev
- clsi-http-requests_project_project_id_output_*_GET_200_upper
- clsi-http-requests_project_project_id_output_*_GET_404_count
- clsi-http-requests_project_project_id_output_*_GET_404_lower
- clsi-http-requests_project_project_id_output_*_GET_404_mean
- clsi-http-requests_project_project_id_output_*_GET_404_stddev
- clsi-http-requests_project_project_id_output_*_GET_404_upper
- clsi-latex-runs
- clsi-latex-runs-0
- clsi-latex-runs-with-errors
- clsi-latex-runs-with-errors-0
- clsi-latexmk-errors
- clsi-load-avg
- clsi-memory_gc-interval
- clsi-memory_heaptotal
- clsi-memory_heapused
- clsi-memory_rss
- clsi-open_connections_http_filestore
- clsi-qpdf_count
- clsi-qpdf_lower
- clsi-qpdf_mean
- clsi-qpdf_stddev
- clsi-qpdf_upper
- clsi-run-compile_count
- clsi-run-compile_lower
- clsi-run-compile_mean
- clsi-run-compile_stddev
- clsi-run-compile_upper
- clsi-unlink-output-files_count
- clsi-unlink-output-files_lower
- clsi-unlink-output-files_mean
- clsi-unlink-output-files_stddev
- clsi-unlink-output-files_upper
- clsi-write-to-disk_count
- clsi-write-to-disk_lower
- clsi-write-to-disk_mean
- clsi-write-to-disk_stddev
- clsi-write-to-disk_upper

## contacts
- contacts-event-loop-millsec_count
- contacts-event-loop-millsec_lower
- contacts-event-loop-millsec_mean
- contacts-event-loop-millsec_stddev
- contacts-event-loop-millsec_upper
- contacts-http-requests_user_user_id_contacts_GET_200_count
- contacts-http-requests_user_user_id_contacts_GET_200_lower
- contacts-http-requests_user_user_id_contacts_GET_200_mean
- contacts-http-requests_user_user_id_contacts_GET_200_stddev
- contacts-http-requests_user_user_id_contacts_GET_200_upper
- contacts-http-requests_user_user_id_contacts_POST_204_count
- contacts-http-requests_user_user_id_contacts_POST_204_lower
- contacts-http-requests_user_user_id_contacts_POST_204_mean
- contacts-http-requests_user_user_id_contacts_POST_204_stddev
- contacts-http-requests_user_user_id_contacts_POST_204_upper
- contacts-mongo-requests_sharelatex_contacts_query_user_id_count
- contacts-mongo-requests_sharelatex_contacts_query_user_id_lower
- contacts-mongo-requests_sharelatex_contacts_query_user_id_mean
- contacts-mongo-requests_sharelatex_contacts_query_user_id_stddev
- contacts-mongo-requests_sharelatex_contacts_query_user_id_upper
- contacts-mongo-requests_sharelatex_contacts_update_count
- contacts-mongo-requests_sharelatex_contacts_update_lower
- contacts-mongo-requests_sharelatex_contacts_update_mean
- contacts-mongo-requests_sharelatex_contacts_update_stddev
- contacts-mongo-requests_sharelatex_contacts_update_upper

## doc-updater
- doc-updater-doc-blocking
- doc-updater-doc-not-blocking
- doc-updater-docManager_flushAndDeleteDoc_count
- doc-updater-docManager_flushAndDeleteDoc_lower
- doc-updater-docManager_flushAndDeleteDoc_mean
- doc-updater-docManager_flushAndDeleteDoc_stddev
- doc-updater-docManager_flushAndDeleteDoc_upper
- doc-updater-docManager_flushDocIfLoaded_count
- doc-updater-docManager_flushDocIfLoaded_lower
- doc-updater-docManager_flushDocIfLoaded_mean
- doc-updater-docManager_flushDocIfLoaded_stddev
- doc-updater-docManager_flushDocIfLoaded_upper
- doc-updater-docManager_getDocAndRecentOps_count
- doc-updater-docManager_getDocAndRecentOps_lower
- doc-updater-docManager_getDocAndRecentOps_mean
- doc-updater-docManager_getDocAndRecentOps_stddev
- doc-updater-docManager_getDocAndRecentOps_upper
- doc-updater-docManager_getDoc_count
- doc-updater-docManager_getDoc_lower
- doc-updater-docManager_getDoc_mean
- doc-updater-docManager_getDoc_stddev
- doc-updater-docManager_getDoc_upper
- doc-updater-http-requests_project_project_id_DELETE_204_count
- doc-updater-http-requests_project_project_id_DELETE_204_lower
- doc-updater-http-requests_project_project_id_DELETE_204_mean
- doc-updater-http-requests_project_project_id_DELETE_204_stddev
- doc-updater-http-requests_project_project_id_DELETE_204_upper
- doc-updater-http-requests_project_project_id_doc_doc_id_GET_200_count
- doc-updater-http-requests_project_project_id_doc_doc_id_GET_200_lower
- doc-updater-http-requests_project_project_id_doc_doc_id_GET_200_mean
- doc-updater-http-requests_project_project_id_doc_doc_id_GET_200_stddev
- doc-updater-http-requests_project_project_id_doc_doc_id_GET_200_upper
- doc-updater-http-requests_project_project_id_flush_POST_204_count
- doc-updater-http-requests_project_project_id_flush_POST_204_lower
- doc-updater-http-requests_project_project_id_flush_POST_204_mean
- doc-updater-http-requests_project_project_id_flush_POST_204_stddev
- doc-updater-http-requests_project_project_id_flush_POST_204_upper
- doc-updater-http_deleteProject_count
- doc-updater-http_deleteProject_lower
- doc-updater-http_deleteProject_mean
- doc-updater-http_deleteProject_stddev
- doc-updater-http_deleteProject_upper
- doc-updater-http_flushProject_count
- doc-updater-http_flushProject_lower
- doc-updater-http_flushProject_mean
- doc-updater-http_flushProject_stddev
- doc-updater-http_flushProject_upper
- doc-updater-http_getDoc_count
- doc-updater-http_getDoc_lower
- doc-updater-http_getDoc_mean
- doc-updater-http_getDoc_stddev
- doc-updater-http_getDoc_upper
- doc-updater-mongo-requests_sharelatex_docOps_query_doc_id_count
- doc-updater-mongo-requests_sharelatex_docOps_query_doc_id_lower
- doc-updater-mongo-requests_sharelatex_docOps_query_doc_id_mean
- doc-updater-mongo-requests_sharelatex_docOps_query_doc_id_stddev
- doc-updater-mongo-requests_sharelatex_docOps_query_doc_id_upper
- doc-updater-mongo-requests_sharelatex_docOps_update_count
- doc-updater-mongo-requests_sharelatex_docOps_update_lower
- doc-updater-mongo-requests_sharelatex_docOps_update_mean
- doc-updater-mongo-requests_sharelatex_docOps_update_stddev
- doc-updater-mongo-requests_sharelatex_docOps_update_upper
- doc-updater-persistenceManager_getDoc_count
- doc-updater-persistenceManager_getDoc_lower
- doc-updater-persistenceManager_getDoc_mean
- doc-updater-persistenceManager_getDoc_stddev
- doc-updater-persistenceManager_getDoc_upper
- doc-updater-persistenceManager_setDoc_count
- doc-updater-persistenceManager_setDoc_lower
- doc-updater-persistenceManager_setDoc_mean
- doc-updater-persistenceManager_setDoc_stddev
- doc-updater-persistenceManager_setDoc_upper
- doc-updater-projectManager_flushAndDeleteProjectWithLocks_count
- doc-updater-projectManager_flushAndDeleteProjectWithLocks_lower
- doc-updater-projectManager_flushAndDeleteProjectWithLocks_mean
- doc-updater-projectManager_flushAndDeleteProjectWithLocks_stddev
- doc-updater-projectManager_flushAndDeleteProjectWithLocks_upper
- doc-updater-projectManager_flushProjectWithLocks_count
- doc-updater-projectManager_flushProjectWithLocks_lower
- doc-updater-projectManager_flushProjectWithLocks_mean
- doc-updater-projectManager_flushProjectWithLocks_stddev
- doc-updater-projectManager_flushProjectWithLocks_upper
- doc-updater-redis_get-doc_count
- doc-updater-redis_get-doc_lower
- doc-updater-redis_get-doc_mean
- doc-updater-redis_get-doc_stddev
- doc-updater-redis_get-doc_upper
- doc-updater-redis_put-doc_count
- doc-updater-redis_put-doc_lower
- doc-updater-redis_put-doc_mean
- doc-updater-redis_put-doc_stddev
- doc-updater-redis_put-doc_upper
- doc-updater-updateManager_processOutstandingUpdates_count
- doc-updater-updateManager_processOutstandingUpdates_lower
- doc-updater-updateManager_processOutstandingUpdates_mean
- doc-updater-updateManager_processOutstandingUpdates_stddev
- doc-updater-updateManager_processOutstandingUpdates_upper
- doc-updater-worker_waiting_count
- doc-updater-worker_waiting_lower
- doc-updater-worker_waiting_mean
- doc-updater-worker_waiting_stddev
- doc-updater-worker_waiting_upper

## docstore
- docstore-event-loop-millsec_count
- docstore-event-loop-millsec_lower
- docstore-event-loop-millsec_mean
- docstore-event-loop-millsec_stddev
- docstore-event-loop-millsec_upper
- docstore-http-requests_project_project_id_doc_GET_200_count
- docstore-http-requests_project_project_id_doc_GET_200_lower
- docstore-http-requests_project_project_id_doc_GET_200_mean
- docstore-http-requests_project_project_id_doc_GET_200_stddev
- docstore-http-requests_project_project_id_doc_GET_200_upper
- docstore-http-requests_project_project_id_doc_doc_id_GET_200_count
- docstore-http-requests_project_project_id_doc_doc_id_GET_200_lower
- docstore-http-requests_project_project_id_doc_doc_id_GET_200_mean
- docstore-http-requests_project_project_id_doc_doc_id_GET_200_stddev
- docstore-http-requests_project_project_id_doc_doc_id_GET_200_upper
- docstore-http-requests_project_project_id_doc_doc_id_GET_404_count
- docstore-http-requests_project_project_id_doc_doc_id_GET_404_lower
- docstore-http-requests_project_project_id_doc_doc_id_GET_404_mean
- docstore-http-requests_project_project_id_doc_doc_id_GET_404_stddev
- docstore-http-requests_project_project_id_doc_doc_id_GET_404_upper
- docstore-http-requests_project_project_id_doc_doc_id_POST_200_count
- docstore-http-requests_project_project_id_doc_doc_id_POST_200_lower
- docstore-http-requests_project_project_id_doc_doc_id_POST_200_mean
- docstore-http-requests_project_project_id_doc_doc_id_POST_200_stddev
- docstore-http-requests_project_project_id_doc_doc_id_POST_200_upper
- docstore-mongo-requests_sharelatex_docs_query__id_count
- docstore-mongo-requests_sharelatex_docs_query__id_lower
- docstore-mongo-requests_sharelatex_docs_query__id_mean
- docstore-mongo-requests_sharelatex_docs_query__id_stddev
- docstore-mongo-requests_sharelatex_docs_query__id_upper
- docstore-mongo-requests_sharelatex_docs_query_inS3_project_id_count
- docstore-mongo-requests_sharelatex_docs_query_inS3_project_id_lower
- docstore-mongo-requests_sharelatex_docs_query_inS3_project_id_mean
- docstore-mongo-requests_sharelatex_docs_query_inS3_project_id_stddev
- docstore-mongo-requests_sharelatex_docs_query_inS3_project_id_upper
- docstore-mongo-requests_sharelatex_docs_query_project_id_count
- docstore-mongo-requests_sharelatex_docs_query_project_id_lower
- docstore-mongo-requests_sharelatex_docs_query_project_id_mean
- docstore-mongo-requests_sharelatex_docs_query_project_id_stddev
- docstore-mongo-requests_sharelatex_docs_query_project_id_upper
- docstore-mongo-requests_sharelatex_docs_update_count
- docstore-mongo-requests_sharelatex_docs_update_lower
- docstore-mongo-requests_sharelatex_docs_update_mean
- docstore-mongo-requests_sharelatex_docs_update_stddev
- docstore-mongo-requests_sharelatex_docs_update_upper

## filestore
- filestore-event-loop-millsec_count
- filestore-event-loop-millsec_lower
- filestore-event-loop-millsec_mean
- filestore-event-loop-millsec_stddev
- filestore-event-loop-millsec_upper
- filestore-getFile
- filestore-http-request
- filestore-http-requests_project_project_id_file_file_id_GET_200_count
- filestore-http-requests_project_project_id_file_file_id_GET_200_lower
- filestore-http-requests_project_project_id_file_file_id_GET_200_mean
- filestore-http-requests_project_project_id_file_file_id_GET_200_stddev
- filestore-http-requests_project_project_id_file_file_id_GET_200_upper
- filestore-http-requests_project_project_id_file_file_id_POST_200_count
- filestore-http-requests_project_project_id_file_file_id_POST_200_lower
- filestore-http-requests_project_project_id_file_file_id_POST_200_mean
- filestore-http-requests_project_project_id_file_file_id_POST_200_stddev
- filestore-http-requests_project_project_id_file_file_id_POST_200_upper
- filestore-insertFile
- filestore-memory_gc-interval
- filestore-memory_heaptotal
- filestore-memory_heapused
- filestore-memory_rss
- filestore-writingFile_count
- filestore-writingFile_lower
- filestore-writingFile_mean
- filestore-writingFile_stddev
- filestore-writingFile_upper

## haproxy
- haproxy-active_servers
- haproxy-backup_servers
- haproxy-bin
- haproxy-bout
- haproxy-cli_abort
- haproxy-ctime
- haproxy-downtime
- haproxy-dreq
- haproxy-dresp
- haproxy-econ
- haproxy-ereq
- haproxy-eresp
- haproxy-http_response.1xx
- haproxy-http_response.2xx
- haproxy-http_response.3xx
- haproxy-http_response.4xx
- haproxy-http_response.5xx
- haproxy-lbtot
- haproxy-qcur
- haproxy-qmax
- haproxy-qtime
- haproxy-rate
- haproxy-rate_max
- haproxy-req_rate
- haproxy-req_rate_max
- haproxy-req_tot
- haproxy-rtime
- haproxy-scur
- haproxy-smax
- haproxy-srv_abort
- haproxy-stot
- haproxy-ttime
- haproxy-wredis
- haproxy-wretr

## mongodb
- mongodb-active_reads
- mongodb-active_writes
- mongodb-commands_per_sec
- mongodb-deletes_per_sec
- mongodb-flushes_per_sec
- mongodb-getmores_per_sec
- mongodb-inserts_per_sec
- mongodb-jumbo_chunks
- mongodb-mapped_megabytes
- mongodb-net_in_bytes
- mongodb-net_out_bytes
- mongodb-non-mapped_megabytes
- mongodb-open_connections
- mongodb-page_faults_per_sec
- mongodb-queries_per_sec
- mongodb-queued_reads
- mongodb-queued_writes
- mongodb-resident_megabytes
- mongodb-ttl_deletes_per_sec
- mongodb-ttl_passes_per_sec
- mongodb-updates_per_sec
- mongodb-vsize_megabytes

## postgresql
- postgresql-blk_read_time
- postgresql-blk_write_time
- postgresql-blks_hit
- postgresql-blks_read
- postgresql-buffers_alloc
- postgresql-buffers_backend
- postgresql-buffers_backend_fsync
- postgresql-buffers_checkpoint
- postgresql-buffers_clean
- postgresql-checkpoint_sync_time
- postgresql-checkpoint_write_time
- postgresql-checkpoints_req
- postgresql-checkpoints_timed
- postgresql-conflicts
- postgresql-deadlocks
- postgresql-maxwritten_clean
- postgresql-numbackends
- postgresql-temp_bytes
- postgresql-temp_files
- postgresql-tup_deleted
- postgresql-tup_fetched
- postgresql-tup_inserted
- postgresql-tup_returned
- postgresql-tup_updated
- postgresql-xact_commit
- postgresql-xact_rollback

## real-time
- real-time-delete_mongo_project_count
- real-time-delete_mongo_project_lower
- real-time-delete_mongo_project_mean
- real-time-delete_mongo_project_stddev
- real-time-delete_mongo_project_upper
- real-time-editor_doc-update
- real-time-editor_get-connected-users
- real-time-editor_join-doc
- real-time-editor_join-project
- real-time-editor_leave-project
- real-time-event-loop-millsec_count
- real-time-event-loop-millsec_lower
- real-time-event-loop-millsec_mean
- real-time-event-loop-millsec_stddev
- real-time-event-loop-millsec_upper
- real-time-get-document_count
- real-time-get-document_lower
- real-time-get-document_mean
- real-time-get-document_stddev
- real-time-get-document_upper
- real-time-socket-io_connection
- real-time-socket-io_disconnect

## redis
- redis-avg_ttl
- redis-clients
- redis-connected_slaves
- redis-evicted_keys
- redis-expired_keys
- redis-expires
- redis-instantaneous_ops_per_sec
- redis-keys
- redis-keyspace_hitrate
- redis-keyspace_hits
- redis-keyspace_misses
- redis-latest_fork_usec
- redis-master_repl_offset
- redis-mem_fragmentation_ratio
- redis-pubsub_channels
- redis-pubsub_patterns
- redis-rdb_changes_since_last_save
- redis-repl_backlog_active
- redis-repl_backlog_histlen
- redis-repl_backlog_size
- redis-sync_full
- redis-sync_partial_err
- redis-sync_partial_ok
- redis-total_commands_processed
- redis-total_connections_received
- redis-uptime
- redis-used_cpu_sys
- redis-used_cpu_sys_children
- redis-used_cpu_user
- redis-used_cpu_user_children
- redis-used_memory
- redis-used_memory_lua
- redis-used_memory_peak
- redis-used_memory_rss

## spelling
- spelling-memory_gc-interval
- spelling-memory_heaptotal
- spelling-memory_heapused
- spelling-memory_rss

## tags
- tags-memory_gc-interval
- tags-memory_heaptotal
- tags-memory_heapused
- tags-memory_rss

## track-changes
- track-changes-append-pack-permanent
- track-changes-http-requests_project_project_id_doc_doc_id_flush_POST_204_count
- track-changes-http-requests_project_project_id_doc_doc_id_flush_POST_204_lower
- track-changes-http-requests_project_project_id_doc_doc_id_flush_POST_204_mean
- track-changes-http-requests_project_project_id_doc_doc_id_flush_POST_204_stddev
- track-changes-http-requests_project_project_id_doc_doc_id_flush_POST_204_upper
- track-changes-http-requests_project_project_id_updates_GET_200_count
- track-changes-http-requests_project_project_id_updates_GET_200_lower
- track-changes-http-requests_project_project_id_updates_GET_200_mean
- track-changes-http-requests_project_project_id_updates_GET_200_stddev
- track-changes-http-requests_project_project_id_updates_GET_200_upper
- track-changes-insert-pack-permanent
- track-changes-memory_gc-interval
- track-changes-memory_heaptotal
- track-changes-memory_heapused
- track-changes-memory_rss
- track-changes-mongo-requests_sharelatex_docHistory_insert_count
- track-changes-mongo-requests_sharelatex_docHistory_insert_lower
- track-changes-mongo-requests_sharelatex_docHistory_insert_mean
- track-changes-mongo-requests_sharelatex_docHistory_insert_stddev
- track-changes-mongo-requests_sharelatex_docHistory_insert_upper
- track-changes-mongo-requests_sharelatex_docHistory_update_doc_id_project_id_count
- track-changes-mongo-requests_sharelatex_docHistory_update_doc_id_project_id_lower
- track-changes-mongo-requests_sharelatex_docHistory_update_doc_id_project_id_mean
- track-changes-mongo-requests_sharelatex_docHistory_update_doc_id_project_id_stddev
- track-changes-mongo-requests_sharelatex_docHistory_update_doc_id_project_id_upper
- track-changes-mongo-requests_sharelatex_docHistory_update_expiresAt_project_id_temporary_count
- track-changes-mongo-requests_sharelatex_docHistory_update_expiresAt_project_id_temporary_lower
- track-changes-mongo-requests_sharelatex_docHistory_update_expiresAt_project_id_temporary_mean
- track-changes-mongo-requests_sharelatex_docHistory_update_expiresAt_project_id_temporary_stddev
- track-changes-mongo-requests_sharelatex_docHistory_update_expiresAt_project_id_temporary_upper
- track-changes-mongo-requests_sharelatex_projectHistoryMetaData_update_project_id_count
- track-changes-mongo-requests_sharelatex_projectHistoryMetaData_update_project_id_lower
- track-changes-mongo-requests_sharelatex_projectHistoryMetaData_update_project_id_mean
- track-changes-mongo-requests_sharelatex_projectHistoryMetaData_update_project_id_stddev
- track-changes-mongo-requests_sharelatex_projectHistoryMetaData_update_project_id_upper

## web
- web-editor_add-file
- web-editor_compile_count
- web-editor_compile_lower
- web-editor_compile_mean
- web-editor_compile_stddev
- web-editor_compile_upper
- web-editor_join-project
- web-email
- web-event-loop-millsec_count
- web-event-loop-millsec_lower
- web-event-loop-millsec_mean
- web-event-loop-millsec_stddev
- web-event-loop-millsec_upper
- web-file-upload_count
- web-file-upload_lower
- web-file-upload_mean
- web-file-upload_stddev
- web-file-upload_upper
- web-http-request
- web-http-requests_Project_Project_id_DELETE_200_count
- web-http-requests_Project_Project_id_DELETE_200_lower
- web-http-requests_Project_Project_id_DELETE_200_mean
- web-http-requests_Project_Project_id_DELETE_200_stddev
- web-http-requests_Project_Project_id_DELETE_200_upper
- web-http-requests_Project_Project_id_GET_200_count
- web-http-requests_Project_Project_id_GET_200_lower
- web-http-requests_Project_Project_id_GET_200_mean
- web-http-requests_Project_Project_id_GET_200_stddev
- web-http-requests_Project_Project_id_GET_200_upper
- web-http-requests_Project_Project_id_output_output_pdf_GET_200_count
- web-http-requests_Project_Project_id_output_output_pdf_GET_200_lower
- web-http-requests_Project_Project_id_output_output_pdf_GET_200_mean
- web-http-requests_Project_Project_id_output_output_pdf_GET_200_stddev
- web-http-requests_Project_Project_id_output_output_pdf_GET_200_upper
- web-http-requests_Project_Project_id_output_output_pdf_GET_404_count
- web-http-requests_Project_Project_id_output_output_pdf_GET_404_lower
- web-http-requests_Project_Project_id_output_output_pdf_GET_404_mean
- web-http-requests_Project_Project_id_output_output_pdf_GET_404_stddev
- web-http-requests_Project_Project_id_output_output_pdf_GET_404_upper
- web-http-requests_Project_Project_id_upload_POST_200_count
- web-http-requests_Project_Project_id_upload_POST_200_lower
- web-http-requests_Project_Project_id_upload_POST_200_mean
- web-http-requests_Project_Project_id_upload_POST_200_stddev
- web-http-requests_Project_Project_id_upload_POST_200_upper
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_200_count
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_200_lower
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_200_mean
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_200_stddev
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_200_upper
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_404_count
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_404_lower
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_404_mean
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_404_stddev
- web-http-requests_^\_project\_([^\_]*)\_output\_(_*)$__GET_404_upper
- web-http-requests__GET_302_count
- web-http-requests__GET_302_lower
- web-http-requests__GET_302_mean
- web-http-requests__GET_302_stddev
- web-http-requests__GET_302_upper
- web-http-requests_login_GET_200_count
- web-http-requests_login_GET_200_lower
- web-http-requests_login_GET_200_mean
- web-http-requests_login_GET_200_stddev
- web-http-requests_login_GET_200_upper
- web-http-requests_login_POST_200_count
- web-http-requests_login_POST_200_lower
- web-http-requests_login_POST_200_mean
- web-http-requests_login_POST_200_stddev
- web-http-requests_login_POST_200_upper
- web-http-requests_project_GET_200_count
- web-http-requests_project_GET_200_lower
- web-http-requests_project_GET_200_mean
- web-http-requests_project_GET_200_stddev
- web-http-requests_project_GET_200_upper
- web-http-requests_project_Project_id_compile_POST_200_count
- web-http-requests_project_Project_id_compile_POST_200_lower
- web-http-requests_project_Project_id_compile_POST_200_mean
- web-http-requests_project_Project_id_compile_POST_200_stddev
- web-http-requests_project_Project_id_compile_POST_200_upper
- web-http-requests_project_Project_id_compile_POST_500_count
- web-http-requests_project_Project_id_compile_POST_500_lower
- web-http-requests_project_Project_id_compile_POST_500_mean
- web-http-requests_project_Project_id_compile_POST_500_stddev
- web-http-requests_project_Project_id_compile_POST_500_upper
- web-http-requests_project_Project_id_doc_doc_id_GET_200_count
- web-http-requests_project_Project_id_doc_doc_id_GET_200_lower
- web-http-requests_project_Project_id_doc_doc_id_GET_200_mean
- web-http-requests_project_Project_id_doc_doc_id_GET_200_stddev
- web-http-requests_project_Project_id_doc_doc_id_GET_200_upper
- web-http-requests_project_Project_id_doc_doc_id_POST_200_count
- web-http-requests_project_Project_id_doc_doc_id_POST_200_lower
- web-http-requests_project_Project_id_doc_doc_id_POST_200_mean
- web-http-requests_project_Project_id_doc_doc_id_POST_200_stddev
- web-http-requests_project_Project_id_doc_doc_id_POST_200_upper
- web-http-requests_project_Project_id_doc_doc_id_diff_GET_500_count
- web-http-requests_project_Project_id_doc_doc_id_diff_GET_500_lower
- web-http-requests_project_Project_id_doc_doc_id_diff_GET_500_mean
- web-http-requests_project_Project_id_doc_doc_id_diff_GET_500_stddev
- web-http-requests_project_Project_id_doc_doc_id_diff_GET_500_upper
- web-http-requests_project_Project_id_join_POST_200_count
- web-http-requests_project_Project_id_join_POST_200_lower
- web-http-requests_project_Project_id_join_POST_200_mean
- web-http-requests_project_Project_id_join_POST_200_stddev
- web-http-requests_project_Project_id_join_POST_200_upper
- web-http-requests_project_Project_id_messages_POST_200_count
- web-http-requests_project_Project_id_messages_POST_200_lower
- web-http-requests_project_Project_id_messages_POST_200_mean
- web-http-requests_project_Project_id_messages_POST_200_stddev
- web-http-requests_project_Project_id_messages_POST_200_upper
- web-http-requests_project_Project_id_updates_GET_200_count
- web-http-requests_project_Project_id_updates_GET_200_lower
- web-http-requests_project_Project_id_updates_GET_200_mean
- web-http-requests_project_Project_id_updates_GET_200_stddev
- web-http-requests_project_Project_id_updates_GET_200_upper
- web-http-requests_project_Project_id_updates_GET_500_count
- web-http-requests_project_Project_id_updates_GET_500_lower
- web-http-requests_project_Project_id_updates_GET_500_mean
- web-http-requests_project_Project_id_updates_GET_500_stddev
- web-http-requests_project_Project_id_updates_GET_500_upper
- web-http-requests_project_Project_id_users_POST_200_count
- web-http-requests_project_Project_id_users_POST_200_lower
- web-http-requests_project_Project_id_users_POST_200_mean
- web-http-requests_project_Project_id_users_POST_200_stddev
- web-http-requests_project_Project_id_users_POST_200_upper
- web-http-requests_project_Project_id_users_POST_302_count
- web-http-requests_project_Project_id_users_POST_302_lower
- web-http-requests_project_Project_id_users_POST_302_mean
- web-http-requests_project_Project_id_users_POST_302_stddev
- web-http-requests_project_Project_id_users_POST_302_upper
- web-http-requests_project_new_POST_200_count
- web-http-requests_project_new_POST_200_lower
- web-http-requests_project_new_POST_200_mean
- web-http-requests_project_new_POST_200_stddev
- web-http-requests_project_new_POST_200_upper
- web-http-requests_project_project_id_details_GET_200_count
- web-http-requests_project_project_id_details_GET_200_lower
- web-http-requests_project_project_id_details_GET_200_mean
- web-http-requests_project_project_id_details_GET_200_stddev
- web-http-requests_project_project_id_details_GET_200_upper
- web-http-requests_register_GET_200_count
- web-http-requests_register_GET_200_lower
- web-http-requests_register_GET_200_mean
- web-http-requests_register_GET_200_stddev
- web-http-requests_register_GET_200_upper
- web-http-requests_restricted_GET_200_count
- web-http-requests_restricted_GET_200_lower
- web-http-requests_restricted_GET_200_mean
- web-http-requests_restricted_GET_200_stddev
- web-http-requests_restricted_GET_200_upper
- web-http-requests_user_contacts_GET_200_count
- web-http-requests_user_contacts_GET_200_lower
- web-http-requests_user_contacts_GET_200_mean
- web-http-requests_user_contacts_GET_200_stddev
- web-http-requests_user_contacts_GET_200_upper
- web-http-requests_user_settings_GET_200_count
- web-http-requests_user_settings_GET_200_lower
- web-http-requests_user_settings_GET_200_mean
- web-http-requests_user_settings_GET_200_stddev
- web-http-requests_user_settings_GET_200_upper
- web-http-requests_user_settings_POST_200_count
- web-http-requests_user_settings_POST_200_lower
- web-http-requests_user_settings_POST_200_mean
- web-http-requests_user_settings_POST_200_stddev
- web-http-requests_user_settings_POST_200_upper
- web-http-requests_user_user_id_personal_info_GET_200_count
- web-http-requests_user_user_id_personal_info_GET_200_lower
- web-http-requests_user_user_id_personal_info_GET_200_mean
- web-http-requests_user_user_id_personal_info_GET_200_stddev
- web-http-requests_user_user_id_personal_info_GET_200_upper
- web-load-editor_count
- web-load-editor_lower
- web-load-editor_mean
- web-load-editor_stddev
- web-load-editor_upper
- web-memory_gc-interval
- web-memory_heaptotal
- web-memory_heapused
- web-memory_rss
- web-mongo-requests_sharelatex_projects_query__id_count
- web-mongo-requests_sharelatex_projects_query__id_lower
- web-mongo-requests_sharelatex_projects_query__id_mean
- web-mongo-requests_sharelatex_projects_query__id_stddev
- web-mongo-requests_sharelatex_projects_query__id_upper
- web-mongo-requests_sharelatex_users_query__id_count
- web-mongo-requests_sharelatex_users_query__id_lower
- web-mongo-requests_sharelatex_users_query__id_mean
- web-mongo-requests_sharelatex_users_query__id_stddev
- web-mongo-requests_sharelatex_users_query__id_upper
- web-mongo-requests_sharelatex_users_query_email_count
- web-mongo-requests_sharelatex_users_query_email_lower
- web-mongo-requests_sharelatex_users_query_email_mean
- web-mongo-requests_sharelatex_users_query_email_stddev
- web-mongo-requests_sharelatex_users_query_email_upper
- web-mongo-requests_sharelatex_users_update_count
- web-mongo-requests_sharelatex_users_update_lower
- web-mongo-requests_sharelatex_users_update_mean
- web-mongo-requests_sharelatex_users_update_stddev
- web-mongo-requests_sharelatex_users_update_upper
- web-open_connections_http
- web-open_connections_https
- web-pdf-downloads
- web-project-creation
- web-project-list_count
- web-project-list_lower
- web-project-list_mean
- web-project-list_stddev
- web-project-list_upper
- web-tpds_add-doc
- web-tpds_add-file
- web-user_login_failed
- web-user_login_success
