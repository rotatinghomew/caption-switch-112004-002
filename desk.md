# 调度台收件协议

本地演练使用 `python3 desk.py --port 8087 --state /tmp/caption-desk.sqlite3`。台端来件库可独立重启；只负责收件和返回实际来件，不判断共享缓存安全、节目质量或试验结果。

`PUT /desk/{station}/operations/{operation}` 以 UTF-8 JSON 提交控制交接。字段与 `handoffs.json` 的 `request_fields` 一致，`station` 是 `dispatcher` 或 `backup`；这里的 `scope` 为在案入口范围名称。相同台、相同号和相同正文返回同样的登记结果；相同号而正文不同返回 409。不同台的登记相互独立。同一操作的两个台端请求允许正文里的链路不同。

`202` 只代表台端登记。`GET` 同路径返回实际登记请求和该台回执；`GET` 后缀 `/receipts` 只返回回执数组。未登记为 404。演练时可在第一次 `PUT` 加 `X-Desk-Simulation: drop-acceptance`，使该台登记后断开连接，查询仍能查到；发生断线不是业务上的未收。

演练控制员通过 `POST` 到 `/desk/{station}/operations/{operation}/receipts` 单独录入各台回报，字段为 `at`、`effective_at`、`kind`、`route_gen`。`kind` 只取 `accepted`、`applied`、`rejected`；只对 `applied` 填实际 `effective_at`，其他为 `null`。旧回执可以晚到，处置方读取回执，不替台端录入自己的成功。`handoffs.json` 是运营交接中取得的历史记录，不会自动进台端来件库。
