# porter

Porter 是一个数据清洗辅助工具，能够将 MySQL、MongoDB 和文本文件（CSV/TSV/JSON）等数据源数据全量扫描推入到 Redis 队列，支持断点续传、自定义等待延迟和 Batch Size。

## 安装

```bash
$ git clone https://github.com/zhiweio/porter.git && cd porter
$ python3 setup.py install --user
```

## 使用

### 配置参数说明

**读取方式**

```yaml
reader: [mysql|mongo|json|file|csv]
```

**redis 配置**

```yaml
redis:
  host: 主机地址
  port: 端口
  db: 库
  password:
  key: 任务名称
  queue_key_prefix: 数据队列名前称缀，留空则默认为`porter.queue.`
  cache_key_prefix: 缓存名前称缀，留空则默认 `porter.cache.`
```

**MySQL 配置**

```yaml
mysql:
  host: 主机地址
  port: 端口
  db: 数据库
  table: 表名
  user: 用户名
  password: 密码
  pk: 表的主键，留空默认 `id`
  column: 需要上传的字段名，留空默认选取全部字段
  append_db_info: 可选，是否同时上传库名表名信息，true OR false，默认 false
  appendices: 可选，指定附加字段数据上传，详细配置见模板文件
```

**MongoDB 配置**

```yaml
mongo:
  host: 主机地址
  port: 端口
  db: 库
  collection: 集合
  user: 用户名
  password: 密码
  column: 需要上传的字段名，留空默认选取全部字段
  appendices: 同上
```

**文本文件配置**
```yaml
file:
  path: 文件路径
  delimiter: 文件分隔符
  header: true: 使用 header 拼接为 json 格式数据; false: 不处理上传整条数据
  appendices: 同上
```

**JSON 文件配置**
```yaml
json:
  path: 文件路径
  appendices: 同上
```

### 使用示例

**MySQL**

```yaml
---
reader: mysql

redis:
  host: "127.0.0.1"
  port: 6379
  db: 56
  password: 123456
  key: task_read_from_mysql
  queue_key_prefix: porter.queue.
  cache_key_prefix: porter.cache.

mysql:
  host: "127.0.0.1"
  port: 3306
  db: db_economic
  table: t_macroindex
  user: test
  password: 123456
  pk: id
  column:

# 指定附加字段一同上传 redis
# appendices 内容格式为 ^\w+:\w+$，会被解析为 key-value，可以为多个
# append_db_info=true 表示同时上传数据库名和表名

```

**MongoDB**

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

**JSON**

```yaml
---
reader: json
...

json:
  path: /pathto/data/test.json
#  appendices:
#    - field_name:"hello world"
```

**CSV**

```yaml
---
reader: file
...

file:
  path: /pathto/data/test.csv
  delimiter: ","
  header: True
#  appendices:
#    - field_name:"hello world"
```

**普通文件**

> 上传原始数据，不做 json 拼接处理

```yaml
---
reader: file
...

file:
  path: /pathto/data/test.csv
  delimiter:
  header: false
#  appendices:
#    - "hello world"
```

### 命令功能详解

```bash
Usage: porter [OPTIONS] [sync|monitor|clear|new]

  A command line tool for extracting data and load into Redis.



Options:
  -V, --version                   Show the version and exit.
  -f, --config-file PATH          Task config file
  -l, --limit INTEGER             Limit of each reading from data source
                                  [default: 1000]

  --limit-scale INTEGER           The maximum lengeth of redis queue is (limit
                                  * scale)  [default: 3]

  --blocking / -B, --no-blocking  Enable blocking mode  [default: True]
  -t, --time-sleep INTEGER        Time to wait when up to the maximum limit of
                                  queue  [default: 10]

  -C, --clean-type [status|queue|all]
                                  Type of redis cache
  -T, --task-type [mysql|mongo|json|file|csv]
                                  Type of task template
  -o, --output-task-file PATH     Save task template into file
  -v, --verbose                   Print debug information
  --debug-file PATH               File to be used as a stream for DEBUG
                                  logging

  -h, --help                      Show this message and exit.
```

1. sync 同步数据
2. monitor 监控任务状态
3. clear 清空任务状态
4. new 创建新的任务模板

每次读取 100 条数据并上传，超过最大限制数量则停止读取
```bash
$ porter sync -f task_template.yaml -l 100
```

读取全部数据并上传
```bash
$ porter sync -f task_template.yaml --no-blocking
```

打印详细日志
```bash
$ porter sync -f task_template.yaml -l 100 -v --debug-file /tmp/porter.log
```

查看任务进度
```bash
$ porter monitor -f task_template.yaml
{
    "db": "db_economic",
    "table": "t_macroindex",
    "count": 61,
    "page": 6,
    "record": {xxx}
}
```

清空缓存数据
- all 所有
- status 任务状态
- queue 队列数据

```bash
$ porter clear -f task_template.yaml --clean-type all
```

创建一个任务配置模板

[mysql|mongo|json|file|csv]

```bash
$ porter new -T mysql

---
reader: mysql

redis:
  host: "127.0.0.1"
  port: 6379
  db:
  password:
  key:
  queue_key_prefix: porter.queue.
  cache_key_prefix: porter.cache.

mysql:
  host: "127.0.0.1"
  port: 3306
  db:
  table:
  user:
  password:
  pk:
  column:

# 指定附加字段一同上传 redis
# appendices 内容格式为 ^\w+:\w+$，会被解析为 key-value，可以为多个
# append_db_info=true 表示同时上传数据库名和表名
```

创建任务模板并写入到指定文件

```bash
$ porter new -T mysql -o /tmp/mysql.yaml
```

## 注意事项

每个数据同步任务都必须是唯一指定的 `cache_key_prefix` + `key`，但是可以多个任务往同一个队列里推数据，即多个任务可以用相同的 `queue_key_prefix` + `key`
