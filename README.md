# 字幕切换试验的可归因窗口与回滚

一场节目内的异步字幕分发记录。时间为节目开始后的秒数；所有观察窗口左闭右开。每次配对安排均先于节目播出。 数据均为合成。

CSV 使用 UTF-8、首行字段名，`-` 表示来源未填；JSON 使用原生布尔、字符串及数字。没有另行给定时，`seq` 只用于还原各条来件的先后，不是业务日期。

## 来源说明

- `program.csv`：planned 是安排组；base 为原字幕，dual 为默认双语。block 是相邻两段配对编号，chain 是计划传输链。
- `routes.csv`：入口在给定区间实际使用的源链与缓存组；同缓存组的入口可相互影响。ready_at 是备用链最早可切入秒数。
- `sessions.csv`：entered 和 watched 分别为进入时刻与已见播放秒数。reported 为回报是否完整，exposed 表示实际观测到字幕，delay_ms、gap_s 为空时表示无对应观测。reported_at 是获得记录的时刻。
- `controls.csv`：request 是值班决定、receipt 是执行端回应；同 control 标识对应同一操作。manual_off 由工作人员解除，不能由新试验安排解除。

## 数据清单

- `policy.json`：配置对象。
- `program.csv`：`block`, `window`, `chain`, `start`, `end`, `planned`。
- `routes.csv`：`door`, `chain`, `cache`, `start`, `end`, `ready_at`。
- `sessions.csv`：`id`, `door`, `entered`, `watched`, `reported`, `exposed`, `delay_ms`, `gap_s`, `reported_at`。
- `observability.csv`：`feed`, `start`, `end`, `state`, `known_at`。
- `controls.csv`：`at`, `control`, `kind`, `chain`, `action`, `origin`, `status`。

## 本地检查

使用 Python 3.11 标准库，无需安装第三方依赖。构建检查和来源契约测试：

```sh
python3 -m compileall -q tests
python3 -m unittest discover -s tests -v
```
