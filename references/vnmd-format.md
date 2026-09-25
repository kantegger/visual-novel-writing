# VNMD-0.1：本包的可选路径辅助格式

不是游戏引擎、不是 Agent Skills 标准的一部分，也不是 Ren'Py/ink 转换器。普通稿件可以不用它。只在需要确定性路径抽取且项目允许时采用；已有 `::` 风格稿也必须先核对本说明，不能假定兼容。

## 输入

一个 UTF-8 文本剧本和一个 JSON 状态文件。Python 3.10+，只有标准库依赖。正文不需要英语；ID 使用英文字母、数字、下划线，不能数字开头。

`::scene` 之前的说明不进入玩家路径。每个场景必须显式 `::goto` 或 `::ending`；不能靠文件排列自动落入下个场景。作者附录应放在另一个文件，不能接在最后一个场景末尾指望解析器自动识别。

```text
::scene START
## 雨停以前
正文。
::choice ASK
::option speak | 问她是否愿意留下。
::set asked = true
具体台词和回应。
::option wait | 先把她的伞拿过来。
另一段具体动作。
::endchoice
::if asked
与实际发生的对话对应的正文。
::else
没有问过时的正文。
::endif
::goto LAST

::scene LAST
结尾正文。
::ending FINISH
```

状态文件：

```json
{
  "format": "vnmd-0.1",
  "entry": "START",
  "defaults": {"asked": false},
  "invariants": []
}
```

## 支持的指令

| 指令 | 行为 |
|---|---|
| `::scene ID` | 场景入口；ID 全稿唯一 |
| `::choice ID` / `::endchoice` | 互斥选择；选择 ID 全稿唯一 |
| `::option ID [if expr] \| 标签` | 当前选择中的选项；选项 ID 在本选择内唯一 |
| `::if expr` / `::elif expr` / `::else` / `::endif` | 可嵌套条件 |
| `::set variable = expr` | 仅当前执行分支赋值 |
| `::goto ID` | 立即离开当前嵌套块和场景，跳到目标 |
| `::ending ID` | 立即终止本路径；后面的文本不读取 |
| `[CUE: 单行说明]` | 可执行阅读中移除整行 |
| `<!-- 单行作者注 -->` | 可执行阅读中移除整行 |

不支持：正文内代码围栏、多行 cue/HTML 注释、变量插值、宏、函数、数组/对象值、引擎命令、自动存读档、算术表达式。遇到不支持的指令或代码围栏报错，不静默删掉未知结构。

## 表达式与状态

允许有限标量：字符串、布尔、有限数字、null；变量名；`and/or/not`；`== != < <= > >=`；括号；数字前的正负号。没有 `eval`、函数调用、属性读取、索引或任意 Python 执行。选项行的 `|` 是分隔符，条件字符串内不能含该字符。条件必须真的为布尔，不把非空字符串当真。

状态从 `defaults` 新建，每次运行相互独立。不从上一结局继承任何隐式值。变量先声明后使用；未声明变量即使位于未选分支也在静态检查中报错。

可用 `domains` 指定枚举域，例如 `"cup": ["intact", "broken"]`。未指定域时，赋值类型必须与初始值一致。相等比较与域检查对类型敏感，`true`、`1`、`1.0` 不互作相等值；有序数字比较仍允许整数与浮点数比较。需要从 null 转字符串时，在域中显式列出所有允许值；没有域的 null 变量只能保持 null。

`invariants` 每项为 `{"id":"unique_name","expr":"boolean expression"}`。初始状态和每次赋值后检查；中间状态也必须满足，因此相互依赖的赋值顺序需要设计。它们只检验作者显式编码的规则，无法识别正文写“杯子又完好”是否违背变量。

## 三个命令

以下在 skill 根目录运行；其他工作目录请使用脚本完整路径。Windows 环境的解释器名称可能是 `py`，用其替换 `python`。

```bash
python scripts/vnmd.py lint examples/umbrella.vnm.md --state examples/umbrella.state.json

python scripts/vnmd.py trace examples/umbrella.vnm.md --state examples/umbrella.state.json --choices examples/umbrella.path.json --out umbrella-reading.md --record umbrella-trace.json

python scripts/vnmd.py sample examples/umbrella.vnm.md --state examples/umbrella.state.json --runs 200 --seed 17 --out umbrella-sample.json
```

`lint` 检查语法、标记配对、ID、变量、目标存在、常量域，以及忽略条件的保守可达关系。可能落空的场景和结构不可达场景是警告，不构成“条件可达已证明”。

`trace` 必须为有多个可用选项的节点提供决定；只有一个可用选项时可自动进入。不会暗选第一个分支。路径文件值可以是一个选项 ID，也可以是重复经过此节点时依次使用的 ID 列表。不可用、缺失、未使用的路径决定都报错。输出剥离未选分支、状态与 cue，供人工按路径试读；不是 UI 渲染。

`sample` 从当前可用选项中按固定随机种子抽样，报告成功/失败、实际访问的场景/选项/结局和漏项，最多附前 20 个失败重现与各结局一个代表路径。覆盖所有结局不等于覆盖所有状态组合；也不代表文笔、人物、事实和情绪正确。

三种命令默认写 stdout。`--out` 指定生成文件，存在时拒绝覆盖；显式 `--force` 才替换生成结果。即使有 `--force` 也不覆盖作为输入的剧本、状态或路径文件。`trace --record` 可另存执行记录；两种输出不能同一路径。所有执行有 `--max-steps`（默认 10000）阻止无尽循环。

## 验证边界

这些检查不能自动发现：散文中的读心、时间倒退、感情重置、未经建立的能力、晦涩或乏味。只有显式变量与断言能被执行。程序不调用外部模型或网络，不编译游戏，不验证音画、语音、存读档和设备适配。

脚本的单元测试不等于 skill 的写作质量测试。验证报告应附实际输入、命令、随机种子、覆盖范围和未测试范围。
