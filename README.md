# Visual Novel Writing · 视觉小说写作

[English](#english) · [简体中文](#简体中文) · [日本語](#日本語)


<a id="english"></a>
## English

**An Agent Skill for writing visual novels and narrative games**. Use it for story development, scene drafting, continuation, revision, route and choice design, continuity checks, and technique analysis. It supports both linear and branching stories. Current version: **0.33.0**.

The skill instructions are currently written in Chinese. They direct the agent to follow the language requested for the manuscript and the language of the project materials.

### Why this skill

VN writing is more than producing good dialogue. A scene may need to advance an immediate action, reveal a relationship, manage what the player knows, and establish readable causes for a choice or later route. A scene can be logically consistent and still fail to hold a player's attention.

This skill helps an agent identify the requested deliverable, write the actual prose, check causality and continuity, and then read the path a player would encounter. It uses examples to form testable techniques rather than fixed templates. It does not prescribe a genre, voice, route count, or ending structure; the project's canon and the user's instructions take precedence.

### What it can help with

| Task | Expected deliverable |
|---|---|
| Develop a premise or outline | A character-driven concept, structural outline, and any requested scene sample |
| Draft or continue a scene | Usable prose that connects to the existing context, not just a summary |
| Revise a passage or manuscript | Prioritized diagnosis, root causes, revised prose, and any needed continuity updates |
| Design choices, routes, or convergence | Clear player intent, state and knowledge differences, convergence conditions, and readable consequences |
| Check continuity and player paths | Character knowledge, relationship changes, what each path reveals, and whether the paths hold together |
| Plan presentation cues | How dialogue, action, visual/audio cues, and scene function relate; script cues are not treated as verified in-game behavior |
| Extract techniques from examples | Candidate technique cards with sources, observations, inferences, conditions, counterexamples, and transfer exercises |

### How it works

1. **Read the project materials.** Preserve established facts, character voice, canon, and format; ask only for information the current task actually needs.
2. **Define what the scene changes.** Identify the characters' immediate goals, obstacles, knowledge, and the action or relationship change at the end.
3. **Write or revise the actual text.** Deliver a scene when asked for a scene; give a located diagnosis before changing a manuscript when asked for feedback.
4. **Check causality and interaction.** Make sure actions are motivated, choices communicate what the player is doing, and route state and shared text do not contradict one another.
5. **Read the player-facing path.** Separate logic checks from reading experience: inspect clarity, pace, character distinction, exposition, and the reason to keep reading.
6. **Deliver the artifact and summarize changes.** Provide usable text or files and note material changes and what remains unverified.

This is a task-oriented workflow, not a mandatory questionnaire. Keep small requests small, and load only the references or templates that apply.

### Installation and use

From a Codex project directory:

```bash
mkdir -p .agents/skills
git clone https://github.com/kantegger/visual-novel-writing.git .agents/skills/visual-novel-writing
```

For use across projects, install under the user-level skills directory:

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/kantegger/visual-novel-writing.git "$HOME/.agents/skills/visual-novel-writing"
```

In a Codex environment that discovers this path, invoke it with `$visual-novel-writing`. If the host does not discover it automatically, ask the agent to read `SKILL.md` from the installed folder and follow the relevant references. Other Agent Skills hosts may use different discovery paths and invocation rules; follow their documentation.

Example prompt:

```text
$visual-novel-writing

Read the outline, character notes, and Chapter 2 in this project.
Draft only the opening of Chapter 3; do not restructure the whole story.
Preserve established voices and confirmed plot facts.
Write a scene that can go directly into the manuscript. Check what each character
currently knows and whether the scene's causes are clear; remove repeated explanation.
Save the result as chapter-03-opening.md and summarize the main changes.
```

You do not need to fill in every template first. Provide the existing materials, the scope of this task, and the expected deliverable.

### What's included

```text
visual-novel-writing/
├── SKILL.md                    Main entry point: task routing, writing loop, quality boundaries
├── agents/openai.yaml          Codex interface metadata
├── references/                 Structure, scenes, interaction, continuity, revision, and examples
│   ├── corpus-techniques.md     32 candidate technique cards with conditions and counterexamples
│   ├── source-index.md          Work index for the technique cards
│   ├── source-study.md          Method for evaluating source material and extracting techniques
│   └── ...
├── assets/templates/            Optional project, scene, choice, and continuity templates
├── examples/                    Original branching example, state, path, and reading version
├── scripts/vnmd.py              Optional VNMD text and path utility
├── tests/                       Unit tests for the VNMD utility
└── evals/                       Writing-evaluation prompts and trigger boundaries
```

References are loaded as needed: `structure.md` for concepts and outlines; `scene-craft.md` for scenes and character action; `interaction.md` for choices, state, and convergence; `continuity.md` for knowledge and consistency; `direction.md` for presentation cues; `quality.md` and `revision.md` for reading checks and revision; and `corpus-techniques.md` for bounded examples, not style rules.

### Optional VNMD utility

You can write in ordinary Markdown without running any scripts. If a project needs explicit nodes, conditions, and choices, try this package's **VNMD-0.1** format and `scripts/vnmd.py` to lint structure, trace a choice path, or sample states.

VNMD is a lightweight convention defined by this project, not an industry standard or game engine format. It cannot judge whether a scene is compelling or guarantee compatibility with an engine. The utility uses only the Python 3.10+ standard library and does not access the network or external models. From the repository root:

```bash
python -m unittest discover -s tests -v
python scripts/vnmd.py lint examples/umbrella.vnm.md --state examples/umbrella.state.json
python scripts/vnmd.py trace examples/umbrella.vnm.md --state examples/umbrella.state.json --choices examples/umbrella.path.json
python scripts/vnmd.py sample examples/umbrella.vnm.md --state examples/umbrella.state.json --runs 200 --seed 17
```

Passing a tooling check does not establish story quality.

### Source examples, evaluation, and limitations

The technique cards analyze local passages from visual novels and other narrative games. They distinguish what the text shows from what an editor thinks it may do, and include conditions, failure cases, and original transfer exercises. A single passage is not treated as a universal rule.

This repository does not contain or host complete game scripts, images, or audio. The cards retain only necessary short textual references, paraphrases, and commentary. See [`references/source-index.md`](references/source-index.md) for work titles and card IDs. The works and related intellectual property belong to their respective rights holders. Locations refer to particular text versions; a translation or extraction alone cannot establish the original-language writing, in-game presentation, or player experience.

The repository includes 16 writing prompts and 6 trigger boundaries as reusable evaluation inputs, not performance results. This version has not had an independent model comparison, blind evaluation, real-reader study, or in-engine playtest. It therefore does not guarantee compelling output or claim proven improvement across projects. Evaluate it against the actual project, complete player paths, and reader feedback.

### Contributions and license

Issues and pull requests are welcome when they describe a concrete writing failure or reference problem. Include reproducible task context, the expected and actual result, and—when adding a technique—its source, text version, evidence limits, transfer conditions, and counterexample. Do not submit complete game scripts, game assets, unauthorized manuscripts, or identifiable private project material.

Original skill instructions, templates, examples, technique analysis, and utility code in this repository are available under the [MIT License](LICENSE). The license does not relicense third-party text referenced in technique cards or grant rights to any game, character, script, image, audio, or trademark.

---

<a id="简体中文"></a>
## 简体中文

**一个帮助写作 agent 完成 VN 实际文本工作的 skill**。适用于构思、场景写作、续写、修订、路线与选项设计、连续性检查，以及从作品案例提炼技法。线性作品和多路线作品都可以使用。

技能主体以中文编写，但会按照项目资料和用户要求保留或切换剧本文字语言。

### 为什么做这个 skill

写 VN 不只是写一段好看的对白。一个场景可能同时要推进眼前行动、呈现人物关系、管理玩家已知信息，并为选择、条件文本或后续路线留下可读的因果。逻辑上说得通，不等于玩家会觉得有趣、可信或值得继续读。

这个 skill 引导 agent 先明确本次交付，再进入实际正文；检查因果与连续性后，沿玩家真正会读到的路径阅读；用场景和反馈检验规则，而不是把案例变成固定模板。它不会替作者选定题材、文风、路线数量或结局结构，项目设定和用户明确要求始终优先。

### 适用任务

| 任务 | 预期交付 |
|---|---|
| 从零构思或搭建大纲 | 有人物驱动的方案、结构骨架，以及用户需要的关键场景样稿 |
| 写一场、下一章或续写 | 接得上已有上下文的实际场景正文，而不只是梗概 |
| 修订一段或全稿 | 有优先级的诊断、根因说明、实际修改稿，以及必要的前后文同步 |
| 设计选项、路线或合流 | 选项表达的玩家意图、状态与知识差异、合流条件和可读后果 |
| 检查连续性和玩家路径 | 人物掌握的信息、关系变化、玩家读到的内容，以及各条路径如何成立 |
| 整理演出意图 | 台词、动作、视听提示与场景功能之间的关系；不把文本 cue 当成实机效果 |
| 从作品案例提炼写法 | 带来源、观察、推断、适用条件、反例和迁移练习的候选技法卡 |

### 工作方式

1. **读取已有项目资料**。沿用设定、人物声音、正史和格式约定；只询问当前任务真正缺少的信息。
2. **明确场景要改变什么**。识别人物当下目标、阻力、掌握的信息，以及场景结束时的行动或关系变化。
3. **写或改实际文本**。用户要场景就交场景；用户要建议就先给可定位的诊断，不擅自覆盖原稿。
4. **检查因果和交互**。确认行动有依据，选项表达的参与方式清楚，路线状态与合流信息没有互相矛盾。
5. **按玩家路径读一遍**。把逻辑检查和阅读体验分开：既检查文本是否成立，也检查节奏、人物辨识度、解释量和继续阅读的动力。
6. **交付并说明变化**。给出可直接使用的正文或文件，并简述重要改动及尚未验证的部分。

这是任务导向的流程，不是每次都要逐项填写的问卷。小任务保持小范围；只有涉及的部分才读取参考资料或模板。

### 安装与调用

在 Codex 项目目录运行：

```bash
mkdir -p .agents/skills
git clone https://github.com/kantegger/visual-novel-writing.git .agents/skills/visual-novel-writing
```

跨项目使用时，可安装到用户级目录：

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/kantegger/visual-novel-writing.git "$HOME/.agents/skills/visual-novel-writing"
```

在支持该发现路径的 Codex 环境中，用 `$visual-novel-writing` 调用。若宿主没有自动发现，可明确要求 agent 读取该目录的 `SKILL.md` 并按相关参考执行。其他 Agent Skills 宿主的安装位置和触发方式以宿主文档为准。

提示词示例：

```text
$visual-novel-writing

读取当前项目的故事大纲、人物设定和第二章正文。
本次只写第三章开场，不重做全书结构。
保留既定人物语气和已经确认的剧情事实。
写出可直接进入稿件的场景正文；检查人物目前掌握的信息和本场因果，
最后删去重复解释。把结果保存为 chapter-03-opening.md，并简述关键改动。
```

不必先把所有模板填完。提供现有材料、本次边界和预期交付即可。

### 包含内容

```text
visual-novel-writing/
├── SKILL.md                    主入口：任务识别、写作循环与质量边界
├── agents/openai.yaml          Codex 界面展示元数据
├── references/                 场景、结构、交互、连续性、修订与案例
│   ├── corpus-techniques.md     32 张带适用条件和反例的候选技法卡
│   ├── source-index.md          技法卡的作品来源索引
│   ├── source-study.md          资料判断与技法提炼方法
│   └── ...
├── assets/templates/            可选的项目、场景、选项与连续性模板
├── examples/                    原创分支示例、状态、路径与阅读稿
├── scripts/vnmd.py              可选的 VNMD 文本检查与路径工具
├── tests/                       VNMD 工具单元测试
└── evals/                       写作行为评测输入与触发边界
```

参考资料按需读取：`structure.md` 处理构思与章节骨架；`scene-craft.md` 处理场景和人物行动；`interaction.md` 处理选项、状态和合流；`continuity.md` 处理知识与跨场景一致性；`direction.md` 处理视听意图；`quality.md` 与 `revision.md` 处理阅读检查和修订；`corpus-techniques.md` 提供有边界的局部案例，不是风格规范。

### 可选的 VNMD 工具

一般 Markdown 写作不需要脚本。若项目需要显式标记节点、条件和选项，可尝试本包的 **VNMD-0.1** 格式及 `scripts/vnmd.py`，用于检查结构、追踪选择路径或抽样状态。

VNMD 是本项目的轻量文本约定，不是行业标准或游戏引擎格式。它不替作者判断场景是否好看，也不保证兼容某个引擎。脚本使用 Python 3.10+ 标准库，不访问网络或外部模型。从仓库根目录运行：

```bash
python -m unittest discover -s tests -v
python scripts/vnmd.py lint examples/umbrella.vnm.md --state examples/umbrella.state.json
python scripts/vnmd.py trace examples/umbrella.vnm.md --state examples/umbrella.state.json --choices examples/umbrella.path.json
python scripts/vnmd.py sample examples/umbrella.vnm.md --state examples/umbrella.state.json --runs 200 --seed 17
```

工具检查通过不代表剧本质量通过。

### 语料案例、评测与边界

技法卡从视觉小说及其他叙事游戏的局部文本中提炼，区分“文本实际呈现了什么”和“编辑者认为它可能产生什么效果”，并列出适用条件、失效方式和新写迁移练习。单个片段不会自动变成普遍规则。

本仓库不包含或托管完整游戏脚本、图片或音频。技法卡只保留必要的短文本指涉、转述和评论。作品名称和卡片编号见 [`references/source-index.md`](references/source-index.md)；相关作品及知识产权归各自权利人所有。引用位置属于特定文本版本，翻译稿或提取稿不能单独证明原语言写作、实机演出或玩家实际感受。

仓库包含 16 个写作任务和 6 个触发边界，作为可复用的评测输入，不是成绩报告。本版本没有独立模型对照、盲评、真实读者测试或游戏引擎实机验证，因此不保证输出一定精彩，也不声称已经证明 skill 能提升所有作品的质量。最终判断仍应回到具体项目、完整路径阅读和读者反馈。

### 贡献与许可证

欢迎针对明确的写作失败或参考资料问题提交 issue 或 pull request。请提供可复现的任务上下文、预期交付与实际问题；新增案例应给出作品来源、文本版本、证据限制、迁移条件和反例。请勿提交完整游戏脚本、游戏素材、未授权稿件或可识别的私人项目内容。

本仓库原创的 skill 指令、模板、示例、技法分析和工具代码采用 [MIT License](LICENSE)。MIT 许可不重新授权技法卡中引用的第三方短文本，也不授予任何游戏、角色、脚本、图片、音频或商标的权利。

---

<a id="日本語"></a>
## 日本語

**ビジュアルノベルとナラティブゲームの執筆を支援する Agent Skill**です。企画、シーン執筆、続きの執筆、改稿、ルートや選択肢の設計、整合性チェック、作品例からの技法抽出に使えます。一本道の作品と分岐型の作品の両方に対応します。現在のバージョン：**0.33.0**。

Skill の指示本文は現在中国語です。原稿の言語は、プロジェクト資料とユーザーの指定に従います。

### この Skill について

VN の執筆は、魅力的な台詞を書くことだけではありません。ひとつのシーンで、目の前の行動を進め、人物関係を示し、プレイヤーが知っている情報を管理し、選択や後のルートにつながる因果を読み取れる形にする必要があります。論理的に正しいシーンが、必ずしも続きを読みたくなるシーンとは限りません。

この Skill は、まず今回の成果物を特定し、実際の本文を書き、因果と連続性を確認し、その後プレイヤーが読む順序に沿って読み直すよう agent を導きます。事例を固定テンプレートにせず、検証可能な技法として扱います。ジャンル、文体、ルート数、結末を一律に指定せず、プロジェクトの設定とユーザーの指示を優先します。

### 対応できる作業

| 作業 | 想定する成果物 |
|---|---|
| 企画やプロットの作成 | 人物を軸にした案、構成案、必要に応じたシーン見本 |
| シーンや章の執筆・続きの執筆 | 既存の文脈につながる実際の本文。あらすじだけで終わらせない |
| 一部または全体の改稿 | 優先順位付きの診断、原因、改稿本文、必要な前後関係の更新 |
| 選択肢、ルート、合流の設計 | プレイヤーの意図、状態・知識の差、合流条件と読める結果 |
| 整合性とプレイヤー経路の確認 | 人物の知識、関係の変化、各経路で提示される情報と成立条件 |
| 演出意図の整理 | 台詞、動作、視聴覚 cue とシーン機能の関係。スクリプト上の cue を実機の挙動とみなさない |
| 作品例からの技法抽出 | 出典、観察、推論、適用条件、反例、応用練習を備えた技法カード |

### 作業の進め方

1. **既存のプロジェクト資料を読む**。設定、人物の声、正史、書式を尊重し、今回の作業に本当に必要な情報だけを尋ねます。
2. **シーンで何が変わるかを決める**。人物の当面の目的、障害、知識、シーンの終わりに起きる行動や関係の変化を整理します。
3. **実際の本文を書く・直す**。シーンを求められたらシーンを書き、講評を求められたら原稿を勝手に上書きせず、該当箇所と原因を示します。
4. **因果とインタラクションを確認する**。行動に根拠があるか、選択肢がプレイヤーの行為を伝えているか、ルート状態や共通部分に矛盾がないかを確認します。
5. **プレイヤーの読む順序で読み直す**。論理チェックと読書体験を分け、テンポ、人物の見分けやすさ、説明量、続きを読みたくなる力を見ます。
6. **成果物を渡し、変更点を説明する**。使える本文やファイルを提示し、主な変更と未検証の点を簡潔にまとめます。

これは作業に合わせて使う手順で、毎回すべてに回答する質問票ではありません。小さな依頼は小さく扱い、必要な参考資料やテンプレートだけを読みます。

### インストールと使い方

Codex のプロジェクトディレクトリで実行します。

```bash
mkdir -p .agents/skills
git clone https://github.com/kantegger/visual-novel-writing.git .agents/skills/visual-novel-writing
```

複数のプロジェクトで使う場合は、ユーザー共通の Skill ディレクトリにインストールします。

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/kantegger/visual-novel-writing.git "$HOME/.agents/skills/visual-novel-writing"
```

このパスを認識する Codex 環境では `$visual-novel-writing` で呼び出します。ホストが自動検出しない場合は、インストール先の `SKILL.md` を読み、関連資料に従うよう agent に依頼してください。他の Agent Skills 対応ホストでは、各ホストのインストール先と呼び出し方法を確認してください。

プロンプト例：

```text
$visual-novel-writing

このプロジェクトのプロット、キャラクター設定、第2章を読んでください。
全体構成は変更せず、第3章の冒頭だけを書いてください。
既に決まっている人物の口調と物語上の事実を維持してください。
原稿にそのまま使えるシーンを書き、人物が何を知っているかと因果関係を確認してください。
重複した説明を削り、chapter-03-opening.md に保存して、主な変更を短く説明してください。
```

先にすべてのテンプレートを埋める必要はありません。既存資料、今回の範囲、期待する成果物を伝えてください。

### 内容一覧

```text
visual-novel-writing/
├── SKILL.md                    メイン入口：依頼の振り分け、執筆手順、品質上の境界
├── agents/openai.yaml          Codex の表示用メタデータ
├── references/                 構成、シーン、選択、整合性、改稿、事例
│   ├── corpus-techniques.md     適用条件と反例を備えた技法カード 32 件
│   ├── source-index.md          技法カードで扱う作品の索引
│   ├── source-study.md          資料の評価と技法抽出の方法
│   └── ...
├── assets/templates/            任意で使える企画、シーン、選択肢、整合性のテンプレート
├── examples/                    オリジナルの分岐例、状態、経路、読み出し用本文
├── scripts/vnmd.py              任意の VNMD テキスト・経路チェックツール
├── tests/                       VNMD ツールの単体テスト
└── evals/                       執筆評価用プロンプトと起動境界
```

参考資料は必要に応じて読みます。`structure.md` は企画と構成、`scene-craft.md` はシーンと人物の行動、`interaction.md` は選択肢・状態・合流、`continuity.md` は知識と整合性、`direction.md` は演出、`quality.md` と `revision.md` は読み直しと改稿、`corpus-techniques.md` は文体規範ではなく条件付きの事例を扱います。

### 任意の VNMD ツール

通常の Markdown 執筆ではスクリプトは不要です。ノード、条件、選択肢を明示したい場合は、本パッケージの **VNMD-0.1** 形式と `scripts/vnmd.py` を使い、構造チェック、選択経路の追跡、状態のサンプリングを行えます。

VNMD は本プロジェクト独自の軽量テキスト形式で、業界標準やゲームエンジン形式ではありません。シーンの面白さを判定したり、特定エンジンとの互換性を保証したりするものではありません。ツールは Python 3.10 以上の標準ライブラリのみを使い、ネットワークや外部モデルにはアクセスしません。リポジトリのルートから実行してください。

```bash
python -m unittest discover -s tests -v
python scripts/vnmd.py lint examples/umbrella.vnm.md --state examples/umbrella.state.json
python scripts/vnmd.py trace examples/umbrella.vnm.md --state examples/umbrella.state.json --choices examples/umbrella.path.json
python scripts/vnmd.py sample examples/umbrella.vnm.md --state examples/umbrella.state.json --runs 200 --seed 17
```

ツールのチェックに通っても、物語の品質が保証されるわけではありません。

### 事例、評価、制約

技法カードはビジュアルノベルや他のナラティブゲームの一部のテキストを分析します。「テキストに実際に書かれていること」と「編集者が考える効果」を分け、適用条件、失敗例、新しい場面への応用練習を記録します。一つの場面を普遍的なルールとして扱いません。

このリポジトリには、ゲームの完全なスクリプト、画像、音声は含まれず、ホスティングもしていません。技法カードには必要最小限の短いテキスト参照、要約、批評のみを掲載しています。作品名とカード番号は [`references/source-index.md`](references/source-index.md) を参照してください。作品と知的財産は各権利者に帰属します。引用位置は特定のテキスト版に基づき、翻訳や抽出テキストだけでは原文の文体、ゲーム内演出、プレイヤー体験を立証できません。

リポジトリには執筆タスク 16 件と起動境界 6 件を評価用入力として収録しています。成績報告ではありません。本バージョンでは、独立したモデル比較、ブラインド評価、実際の読者テスト、ゲームエンジン上でのテストを行っていません。そのため、魅力的な出力や全作品での品質向上を保証するものではありません。実際のプロジェクト、プレイヤーが読む全経路、読者の反応を基に評価してください。

### コントリビューションとライセンス

具体的な執筆上の問題や参考資料の誤りについて、issue や pull request を歓迎します。再現可能な作業条件、期待結果、実際の問題を記載してください。技法カードを追加する場合は、出典、テキスト版、証拠の限界、応用条件、反例を示してください。ゲームの完全なスクリプト、ゲーム素材、許諾のない原稿、個人が特定できるプロジェクト資料は投稿しないでください。

本リポジトリで作成した Skill 指示、テンプレート、例、技法分析、ツールコードは [MIT License](LICENSE) で提供します。このライセンスは技法カード内で参照する第三者の短いテキストを再許諾せず、ゲーム、キャラクター、スクリプト、画像、音声、商標の権利も付与しません。
