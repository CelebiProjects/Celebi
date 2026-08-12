# Celebi 命令命名问题审查报告

## 范围

本文档覆盖三个 CLI 入口和 Chern Shell 的全部命令：

| 入口 | 二进制 | 入口文件 | 命令数 |
|------|--------|---------|--------|
| `celebi` | `celebi` | `CelebiChrono/main.py` | 14 |
| `celebi-cli` | `celebi-cli` | `CelebiChrono/celebi_cli/cli.py` | 68 |
| `celebi-git` | `celebi-git` | `CelebiChrono/main.py` (git_cli) | 7 |
| Chern Shell | (交互式) | `interface/chern_shell/` | ~95 |

---

## 🔴 严重（名字无法传达功能，用户不可能猜到含义）

### 1. `use` / `use-data` / `use-eos` — "use" 是英语中最泛化的动词

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `celebi use PATH` | CLI | 把目录设为当前项目 |
| `use-data IMPRESSION_UUID` | CLI + Shell | 从 Yuki 导入一个 impression 作为 rawdata task |
| `use-eos on\|off` | Shell | 开关 EOS 功能 |

**问题**: "use" 毫无信息量。三个命令的实际行为分别是"切换项目"、"导入数据"、"开关功能"，跟 "use" 的语义几乎没有重叠。

**建议**:
- `celebi use` → `set-project` 或 `switch`
- `use-data` → `adopt-impression` 或 `import-impression`
- `use-eos` → `set-eos` 或 `toggle-eos`

---

### 2. `bkkurl` / `viewbkk` — 不可读的缩写

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `bkkurl` | Shell | 获取 bookkeeping URL |
| `viewbkk` | Shell | 在浏览器中打开 bookkeeping URL |

**问题**: "bkk" 不是任何常见缩写。CLI 中同样的功能叫 `bookkeep-url`，两边不一致。用户看到 `bkkurl` 不可能猜到含义。

**建议**: 统一用 `bookkeeping-url` / `view-bookkeeping`，或至少用 `bk-url` / `bk-open`。

---

### 3. `homekeep` — 英语中不存在的词

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `homekeep` | Shell | 清理 runner workflow |

**问题**: "homekeep" 是生造词，描述也只有一句 "Clean the runner workflow"。从名字完全看不出功能。

**建议**: `clean-runner` 或 `reset-workflow`。

---

### 4. `workon` — 非标准 CLI 动词

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `celebi workon PROJECT` | CLI | 切换到指定项目 |

**问题**: 标准 CLI 工具用 `switch`、`select`、`checkout`。"workon" 看起来像非母语者直译。

**建议**: `switch` 或 `select`。

---

### 5. `danger` / `danger-call` — 不描述操作，且制造不必要的恐慌

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `celebi-cli danger OPERATION` | CLI | 执行危险操作 |
| `danger-call` | Shell | 直接执行任意命令 |

**问题**: "danger" 不是动词，不描述做什么。用户不知道"危险操作"的具体含义。命名应该描述操作本身，风险提示应该放在确认环节。

**建议**: `exec-raw` 或 `run-direct`。如需警告，在确认 prompt 中处理。

---

### 6. `add-source` — 不描述实际行为，且与 `send` 的关系被名字隐藏

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `add-source PATH` | CLI + Shell | 计算外部目录 MD5 → 写入 celebi.yaml → 创建 impression |

**问题**: 名字暗示"添加一个来源"，但实际是纯元数据操作（算 hash + 打快照）。不复制文件，不上传数据，不建立 DAG 边。更严重的是，`send` = `add-source` 的全部逻辑 + 上传到 DITE，两个命令有 80% 代码重叠，但从名字上完全看不出关系。

**底层调用链**:
```
add-source → dir_md5() + set_input_md5() + impress()    # 本地记录
send       → [以上全部] + send_data() → deposit_with_data()  # 记录 + 上传 DITE
```

**建议**: 方案 A — 合并成一个命令：
```
register-data PATH           # = 现在的 add-source
register-data --upload PATH  # = 现在的 send
```
方案 B — 保留两个但让名字体现关系：
```
record-source PATH   # = add-source
push-source PATH     # = send
```

---

## 🟡 中等（不够清晰或容易混淆）

### 7. `impress` vs `impression` — 动词/名词混淆，极易打错

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `impress` | Shell | **创建** impression（动词） |
| `impression` | Shell | **查看**当前 impression（名词） |

**问题**: 两个相邻命令，一个是动词一个是名词，在 Shell 中极易打错。打错后行为完全不同（创建 vs 查看）。

**建议**: `create-impression` / `show-impression`，或 `snapshot` / `show-snapshot`。

---

### 8. `navigate` — 名不副实

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `navigate` | CLI + Shell | **打印**当前项目路径 |

**问题**: "navigate" 暗示移动/切换，实际只是 print 路径（相当于 `pwd`）。

**建议**: `pwd` 或 `current-path` 或 `where`。

---

### 9. `prologue` — 完全不描述功能

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `celebi prologue` | CLI | "A prologue from the author" |

**问题**: 帮助文本也没有说明实际功能。是显示作者信息？版本声明？许可证？

**建议**: 明确功能后重命名。如果是关于信息 → `about` 或 `version`。

---

### 10. `preshell` / `postshell` — 暴露了 workaround 本质

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `celebi-cli preshell` | CLI | "Pre-shell workaround" |
| `celebi-cli postshell COMMAND` | CLI | "Post-shell workaround" |

**问题**: 命名直接暴露了它们是 workaround，不是正式功能。用户会质疑为什么要用 workaround。

**建议**: 描述实际操作，或合并到 `workaround` 命令中。

---

### 11. `helpme` — 不够专业

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `helpme` | Shell | 获取当前对象的帮助信息 |

**问题**: 因为 `cmd.Cmd` 保留了 `help`，所以被迫用 `helpme`。但 "helpme" 看起来像求救信号。

**建议**: `info` 或 `describe` 或 `object-help`。

---

### 12. `book-reana` / `booking-server` / `register-booking-server` — "book" 动词奇怪

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `book-reana` | CLI + Shell | 将项目部署到 REANA |
| `booking-server` | CLI + Shell | 查看已注册的 booking server |
| `register-booking-server` | CLI + Shell | 注册 REANA server 和 token |

**问题**: "book" 作为动词在计算领域通常表示"预订资源"，但这里实际是"部署/同步项目到 REANA"。'booking-server' 读起来像名词短语而非命令。

**建议**: `deploy-reana` / `reana-server` / `register-reana-server`。

---

### 13. `chern-command-line` — 太长且不像命令

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `celebi chern-command-line` | CLI | 启动 Chern 命令行 |

**问题**: 三个词用连字符串起来，太长。而且 `celebi` 不带参数已经进入 shell。

**建议**: 如果确实需要显式入口 → `shell`。或者去掉这个命令。

---

### 14. `import` vs `import-file` — 完全相同的两个命令

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `import` | Shell | 复制外部文件到当前对象 |
| `import-file` | Shell | **完全一样** |

**问题**: 两个命令做完全相同的事（都调用 `shell.import_file()`），纯别名没有任何区分价值。

**底层行为**: `csys.copy()` / `csys.copy_tree()` — 就是文件复制。

**建议**: 只保留 `import-file`（比 `import` 更明确，避免和 Python 的 `import` 语义混淆）。

---

### 15. `short-ls` — 混用缩写

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `short-ls` | CLI + Shell | 简短列表 |

**问题**: 其他命令都是长格式（`create-task`、`add-algorithm`），唯独这个混入了 `ls` 的 Unix 缩写。

**建议**: `list-short`，或用 flag 形式（`ls --short`）。

---

## 🟠 一致性问题（CLI 和 Shell 不同名）

同一操作在不同入口使用了不同的命令名：

| 操作 | `celebi-cli` | Shell | 问题 |
|------|-------------|-------|------|
| 移动文件 | `mvfile` | `mv-file` | 一个有连字符，一个没有 |
| 删除文件 | `rmfile` | `rm-file` | 同上 |
| 切换项目 | `cdproject` | `cd-project` | 同上 |
| 列出项目 | 无（用 `celebi projects`） | `ls-projects` | 三个入口三种叫法 |
| 清理 | `purge` | `purge-impressions` | 名字不同 |
| 书签 URL | `bookkeep-url` | `bkkurl` | 差异巨大 |
| 画 DAG | `draw-dag` | `draw-dag-graphviz` | Shell 暴露了实现细节 |
| 内存限制 | `set-mem` | `set-memory-limit` | 缩写 vs 全称 |

**建议**: 统一用连字符格式。CLI 命令和 Shell 命令应尽量一致。

---

### 16. `config` 在两个入口含义不同

| 命令 | 入口 | 实际行为 |
|------|------|---------|
| `celebi config` | CLI | 配置软件（全局设置） |
| `celebi-cli config` | CLI | 配置设置（项目级？） |
| `config` | Shell | 编辑配置 |

**问题**: 同名命令在不同入口含义不同。

**建议**: `global-config` vs `project-config`，或统一行为。

---

## 🔵 轻微问题

### 17. `collect` / `collect-outputs` / `collect-logs` — 应该用子命令或 flag

三个独立命令不如整合：
```
collect --outputs    # = collect-outputs
collect --logs       # = collect-logs
collect --all        # = collect all
```

### 18. `imgcat` — 奇怪的合成词

把 "image" 缩成 "img" 再拼上 "cat"。更像是 `img2txt` 的节奏。

**建议**: `show-image` 或 `display-image`。

### 19. `add-multi-inputs` / `create-multi-tasks` / `create-multi-data` / `remove-multi-inputs`

"multi" 作为命令名一部分读起来笨拙。

**建议**: 用 `--batch` flag 或 `bulk-*` 前缀。

### 20. `config-cache-invalidation-mode` — 5 个单词

CLI 中最长的命令名。

**建议**: `cache-mode` 或做成 `config cache-mode` 子命令。

### 21. `draw-dag-graphviz` — 实现细节暴露在命令名中

用户不需要知道底层用 Graphviz。

**建议**: 统一为 `draw-dag`（和 CLI 一致）。

### 22. `system-shell` — 绕口

Shell 中输入 `system-shell` 进入 bash。

**建议**: `bash` 或 `!`（类似 IPython）。

### 23. `bookkeep` — 拼写问题

"Bookkeep" 是非常罕见的动词形式。

**建议**: `sync-impressions` 或 `reconcile-impressions`。

### 24. `set-environment` vs `setenv` / `set-descriptor` vs `setdescriptor`

存在无意义的别名对。在没有版本兼容需求的情况下，多余的别名只增加认知负担。

### 25. `add-apd-token` / `create-lhcb-ap-list` — 实验特定术语

包含 LHCb 实验的特定术语（APD、LHCb AP），对于非 LHCb 用户完全不可理解。

**建议**: 如果 Celebi 面向通用 HEP，考虑更通用的命名。

---

## 四个容易混淆的命令：`import` / `add-input` / `add-source` / `send`

这是整个系统中命名问题最集中的四个命令。底层行为完全不同，但名字让人无法区分：

| | import | add-input | add-source | send |
|---|---|---|---|---|
| **本质** | 文件复制 | DAG 依赖图操作 | 本地元数据记录 | 本地记录 + 远程上传 |
| **复制文件** | ✅ | ❌ | ❌ | ❌ |
| **建立 DAG 边** | ❌ | ✅ | ❌ | ❌ |
| **计算 MD5** | ❌ | ❌ | ✅ | ✅ |
| **写入 celebi.yaml** | ❌ | ❌ | ✅ | ✅ |
| **创建 impression** | ❌ | ❌ | ✅ | ✅ |
| **上传到 DITE** | ❌ | ❌ | ❌ | ✅ |
| **可用范围** | task/algorithm | task/algorithm | VTask only | VTask only |

**推荐的最终方案**:

| 现在的名字 | 推荐名字 | 理由 |
|-----------|---------|------|
| `import` / `import-file` | `import-file` | 合并双别名，语义明确（复制文件进来） |
| `add-input` | `link` 或 `depend-on` | 本质是建立 DAG 依赖 |
| `add-source` | `register-data` | 本质是登记数据源 hash + 创建快照 |
| `send` | `register-data --upload` 或 `push-data` | 是 register-data 的超集（加上传） |

---

## 总结

| 严重程度 | 数量 | 典型问题 |
|---------|------|---------|
| 🔴 严重 | 6 | 名字完全无法传达功能 |
| 🟡 中等 | 9 | 模糊、容易混淆 |
| 🟠 一致性 | 8 对 | CLI 和 Shell 命名不一致 |
| 🔵 轻微 | 9 | 可以更好但不致命 |

**优先修复 Top 5**:
1. `use` / `use-data` / `use-eos` → 拆分并重命名
2. `bkkurl` / `viewbkk` → 用完整单词
3. `homekeep` → 描述实际功能
4. `add-source` / `send` → 体现关系（合并或对齐命名）
5. `danger` / `danger-call` → 描述实际操作
