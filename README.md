[中文](./README_zh.md)

# Porter

Porter is a data cleaning tool designed to assist with full data extraction from MySQL, MongoDB, and text files (CSV/TSV/JSON) and push them into Redis queues. It supports features like resumable uploads, customizable wait delays, and configurable batch sizes.

## Installation

```bash
$ git clone https://github.com/zhiweio/porter.git && cd porter
$ python3 setup.py install --user
```

## Usage

### Configuration Parameters

**Reader Types**

Specify the data source type:

```yaml
reader: [mysql|mongo|json|file|csv]
```

**Redis Configuration**

Configure Redis connection and data queue settings:

```yaml
redis:
  host: Redis server address
  port: Redis port
  db: Redis database number
  password: Redis password (optional)
  key: Task name
  queue_key_prefix: Prefix for data queue names (defaults to `porter.queue.` if left empty)
  cache_key_prefix: Prefix for cache names (defaults to `porter.cache.` if left empty)
```

**MySQL Configuration**

```yaml
mysql:
  host: MySQL server address
  port: MySQL port
  db: Database name
  table: Table name
  user: MySQL username
  password: MySQL password
  pk: Primary key (defaults to `id` if left empty)
  column: Columns to upload (uploads all columns if left empty)
  append_db_info: Optional, upload database and table names (true or false, defaults to false)
  appendices: Optional, additional fields to upload (refer to the template file for details)
```

**MongoDB Configuration**

```yaml
mongo:
  host: MongoDB server address
  port: MongoDB port
  db: Database name
  collection: Collection name
  user: MongoDB username
  password: MongoDB password
  column: Columns to upload (uploads all columns if left empty)
  appendices: Same as above
```

**Text File Configuration**

```yaml
file:
  path: File path
  delimiter: File delimiter
  header: true if the first row is a header (uploads data as JSON); false if not (uploads raw data)
  appendices: Same as above
```

**JSON File Configuration**

```yaml
json:
  path: File path
  appendices: Same as above
```

### Usage Examples

**MySQL Configuration Example**

```yaml
---
reader: mysql

redis:
  host: "127.0.0.1"
  port: 6379
  db: 56
  password: "123456"
  key: task_read_from_mysql
  queue_key_prefix: porter.queue.
  cache_key_prefix: porter.cache.

mysql:
  host: "127.0.0.1"
  port: 3306
  db: db_economic
  table: t_macroindex
  user: test
  password: "123456"
  pk: id
  column: 

# Additional fields can be uploaded to Redis.
# The format of appendices should be ^\w+:\w+$, interpreted as key-value pairs.
# Set append_db_info to true to also upload database and table names.
```

**MongoDB Configuration Example**

```yaml
---
reader: mongo
...

mongo:
  host: "127.0.0.1"
  port: 7055
  db: iEnterprise
  collection: TLDetailData
  user: root
  password: "123456"
  column: 
```

**JSON File Example**

```yaml
---
reader: json
...

json:
  path: /path/to/data/test.json
#  appendices:
#    - field_name:"hello world"
```

**CSV File Example**

```yaml
---
reader: file
...

file:
  path: /path/to/data/test.csv
  delimiter: ","
  header: true
#  appendices:
#    - field_name:"hello world"
```

**Plain Text File Example**

Upload raw data without JSON formatting:

```yaml
---
reader: file
...

file:
  path: /path/to/data/test.csv
  delimiter: 
  header: false
#  appendices:
#    - "hello world"
```

### Command Usage

```bash
Usage: porter [OPTIONS] [sync|monitor|clear|new]

  A command-line tool for extracting data and loading it into Redis.

Options:
  -V, --version                   Show the version and exit.
  -f, --config-file PATH          Path to the task config file.
  -l, --limit INTEGER             Limit the number of records read from the data source per batch [default: 1000].
  --limit-scale INTEGER           Maximum Redis queue size is (limit * scale) [default: 3].
  --blocking / -B, --no-blocking  Enable blocking mode [default: True].
  -t, --time-sleep INTEGER        Time (in seconds) to wait when the queue reaches the maximum limit [default: 10].
  -C, --clean-type [status|queue|all]
                                  Type of Redis cache to clear.
  -T, --task-type [mysql|mongo|json|file|csv]
                                  Type of task template.
  -o, --output-task-file PATH     Save task template to a file.
  -v, --verbose                   Enable verbose mode (print debug information).
  --debug-file PATH               Path to a file for DEBUG logging.
  -h, --help                      Show help information and exit.
```

1. **sync**: Synchronize data.
2. **monitor**: Monitor the task status.
3. **clear**: Clear the task status.
4. **new**: Create a new task template.

### Example Commands

Sync 100 records at a time and stop when the maximum queue limit is reached:

```bash
$ porter sync -f task_template.yaml -l 100
```

Sync all data without blocking:

```bash
$ porter sync -f task_template.yaml --no-blocking
```

Sync data with verbose logging:

```bash
$ porter sync -f task_template.yaml -l 100 -v --debug-file /tmp/porter.log
```

Monitor the task progress:

```bash
$ porter monitor -f task_template.yaml
{
    "db": "db_economic",
    "table": "t_macroindex",
    "count": 61,
    "page": 6,
    "record": { ... }
}
```

Clear cache data (options: `all`, `status`, or `queue`):

```bash
$ porter clear -f task_template.yaml --clean-type all
```

Create a task configuration template (options: `mysql`, `mongo`, `json`, `file`, `csv`):

```bash
$ porter new -T mysql
```

Create a task template and save it to a file:

```bash
$ porter new -T mysql -o /tmp/mysql.yaml
```

## Notes

Each data sync task must have a unique combination of `cache_key_prefix` + `key`. However, multiple tasks can push data to the same queue, meaning they can share the same `queue_key_prefix` + `key`.
