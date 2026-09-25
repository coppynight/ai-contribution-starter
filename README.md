# 让 AI 持续贡献：从现有项目补齐机制

[![退出码回归检查](https://github.com/coppynight/ai-contribution-starter/actions/workflows/verify-demo.yml/badge.svg?branch=main&event=push)](https://github.com/coppynight/ai-contribution-starter/actions/workflows/verify-demo.yml)
[![报名流程回归检查](https://github.com/coppynight/ai-contribution-starter/actions/workflows/verify-registration-demo.yml/badge.svg?branch=main&event=push)](https://github.com/coppynight/ai-contribution-starter/actions/workflows/verify-registration-demo.yml)

上面两个徽章表示当前 `main` 的自动检查状态。历史记录中有一次**故意制造的红灯演示**，不代表当前主分支检查失败；[下文](#历史上的真实红灯记录)保留了它的输入、日志与解释。现在所有工作流都验证教学结果是否符合预期，任何意外结果仍会让 CI 失败。

这里提供一份可以交给 coding agent 的启动指令，以及两个可运行的 before / after 教学示例。

核心想法是：把“让 AI 持续、稳定地为项目贡献”本身作为一个工程问题来设计。复用已有工程，先补齐一个真实缺口，再把验证入口留给下一次贡献。

## 先看一个报名工具的例子

**[活动报名 demo：两份改动都完成了，放在一起呢？](registration-demo/README.md)**

活动有 8 个名额，A 加入家庭报名，B 按原来的个人报名规则加入取消功能。各自的检查都通过，一家 3 人报名再取消时，名额却是 **8 → 5 → 6**。加入组合检查、根据失败反馈修复后，才变成 **8 → 5 → 8**。

这是可复现的构造教学样例。它用同一个小项目讲清楚：确认方向、划清责任、附上交付依据、检查组合结果、反馈修正、留下可复用入口，怎样连成一套持续接纳贡献的机制。

```sh
python registration-demo/verify.py
```

数字来自实际模型运行，[证据 JSON](registration-demo/evidence.json) 可以逐项核查。下面的退出码示例展示另一个更底层的缺口：测试失败如何可靠传到 CI。

## 在你的项目中使用

1. 打开 **[完整启动指令](prompts/maintainer.md)**，复制其中“可复制的完整指令”代码块。
2. 在你现有项目中，把它交给能够读写仓库、运行命令的 coding agent。
3. 让它先检查已有机制，再增量修改和验证。阅读它提供的实际改动、运行证据和未解决项，决定是否接纳。

指令默认止于本地可审阅状态；它不要求替换现有工具，也不会授权远程发布、合并或修改保护规则。你可以在指令后追加已明确的待办。

## 示例：让检查失败真正传到 CI

这是专门构造的教学工程，业务是生成待办任务视图。两个版本保留相同的业务代码和三个测试，只改变检查入口对失败的处理。

| 情况 | before | after |
| --- | --- | --- |
| 正常业务代码 | 3 个测试通过，退出码 0 | 3 个测试通过，退出码 0 |
| 临时移除“排除已完成任务”的过滤条件 | 2 个测试失败，但入口仍退出 0 | 2 个测试失败，入口退出 1 |
| 把这个入口交给 CI 执行 | 可能把失败显示为绿色 | 能将这类失败显示为红色 |

具体变化只有捕获与返回测试进程的状态：

```diff
-subprocess.run(
+result = subprocess.run(
     [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
     cwd=Path(__file__).resolve().parent,
     check=False,
 )
+sys.exit(result.returncode)
```

对照查看：[before/check.py](demo-before/check.py) → [after/check.py](demo-after/check.py)。这次修补没有新增业务功能，也没有删改测试。它让已经存在的测试成为调用方能够识别的检查门槛。

这演示的是“检查结果能够可靠传递到 CI”的一个具体缺口。测试覆盖范围、权限、审核、集成冲突和发布恢复仍需根据真实项目建设；这两行改动不等于完整的持续集成体系。

## 本地复现

需要 Python 3.10 或更新版本，不需要第三方依赖。在仓库根目录执行：

```sh
python scripts/verify_demo.py
```

验证脚本会在临时副本中依次执行 before 正常、before 负例、after 正常、after 负例和 after 恢复，断言每一步的真实退出码和测试结果，并检查源文件哈希保持不变。完整结果写入 [evidence/verification.json](evidence/verification.json)。负例是人为注入的演练，不是用户项目事故。

如果只想运行各版本的正常检查：

```sh
python demo-before/check.py
python demo-after/check.py
```

## 在 GitHub Actions 验证这套教学流程

本仓库有三个工作流，检查名称各不相同：

| 工作流 | 触发方式 | 验证什么 |
| --- | --- | --- |
| **CI — Exit-code regression checks** | push / pull request / 手动 | 正常、故障和恢复的五种对照情形；另用临时副本验证删检查、吞退出码等破坏能被发现。 |
| **CI — Registration regression checks** | push / pull request / 手动 | 独立检查、组合失败和修复；核对每个版本实际执行的检查项目、数量、预期值、实际值和退出码。 |
| **CI — Verify selected gate scenario** | 手动 | 运行选定的 before / after 场景，把真实结果与该场景的预期逐项比较，并在 Actions Summary 中展示。 |

在 Actions 中选择第三个工作流，点击 **Run workflow**：

| 输入 | 预期真实检查结果 | 场景验证工作流 |
| --- | --- | --- |
| `version=before`, `inject_fault=false` | 3 项通过，入口退出 0 | 符合预期才通过 |
| `version=before`, `inject_fault=true` | 2 项失败，旧入口却退出 0 | 验证出旧入口的缺陷才通过 |
| `version=after`, `inject_fault=true` | 2 项失败，新入口退出 1 | 验证出新入口正确传递失败才通过 |
| `version=after`, `inject_fault=false` | 3 项通过，入口退出 0 | 符合预期才通过 |

**教学验证通过，表示实际结果符合预期，不表示错误代码可以接纳。** 例如 after + 故障如果意外返回 0，或者少跑了检查，工作流必须失败。这里没有用 `continue-on-error` 忽略错误，而是显式核对真实退出码、测试数量和失败数量。

故障仅注入临时副本。要直接观察作为业务门槛的原始退出码，在本地运行：

```sh
python scripts/run_gate_demo.py --version before --inject-fault true
# 退出 0，展示旧入口掩盖失败的缺陷。
python scripts/run_gate_demo.py --version after --inject-fault true
# 退出 1，展示修复后的入口正确传递失败。
python scripts/run_gate_demo.py --version after --inject-fault false
# 退出 0，正常代码通过。
```

手动工作流在同一命令后增加 `--verify-expectation`，核对教学场景。**接入真实项目的业务检查时，应使用 `python demo-after/check.py` 这样的原始入口，保留失败退出码，不要把“预期故障演练”当作接纳门槛。**

验证“验证器本身不会漏报”的回归命令是：

```sh
python scripts/test_ci_contracts.py
```

它只在临时副本中制造破坏，原仓库不变。无故删掉家庭检查、把退出码固定为 0、用另一项失败冒充家庭取消失败，以及把修复退回旧行为，都必须被拒绝。

### 历史上的真实红灯记录

旧版手动工作流名为 **Gate demo — controlled failure**，直接返回原始检查退出码，因此曾刻意留下红色记录。现在改为上面的场景验证，保留原始命令和历史证据供核查。

以下是真实运行记录，均基于提交 `faa23dc2d4747856219b07b5d9e60305341a475f`：

- [完整对照自动验证：通过](https://github.com/coppynight/ai-contribution-starter/actions/runs/36099968800)。五种情形均符合预期，源文件哈希不变。
- [before + 受控故障：绿色](https://github.com/coppynight/ai-contribution-starter/actions/runs/36100006712)。实际有 2 个测试失败，检查入口却返回 0。
- [after + 同一受控故障：红色](https://github.com/coppynight/ai-contribution-starter/actions/runs/36100019823)。实际有 2 个测试失败，检查入口返回 1；**这是刻意保留的预期失败**。
- [after + 正常代码：绿色](https://github.com/coppynight/ai-contribution-starter/actions/runs/36100024622)。3 个测试通过，入口返回 0。

运行编号、提交、输入、实际结论与日志摘录保存在 [公开 Actions 证据](evidence/github-actions.json) 中。日志保留期由 GitHub 设置决定，脚本可用于重新复现。

**CI 能反馈失败，与仓库禁止合入失败代码是两件事。** 本仓库工作流不配置分支保护或 ruleset；接入自己项目时，由维护者决定哪些检查必须通过、谁有接纳权限。本示例也不声称验证了多分支合并队列或生产部署。

## 文件导航

- [prompts/maintainer.md](prompts/maintainer.md)：启动指令及完成标准。
- [demo-before/](demo-before/)：检查入口未传递失败状态。
- [demo-after/](demo-after/)：修补后的检查入口。
- [scripts/verify_demo.py](scripts/verify_demo.py)：五个情形的自动复现与证据输出。
- [scripts/run_gate_demo.py](scripts/run_gate_demo.py)：单次演示，原样返回检查入口状态。
- [scripts/test_ci_contracts.py](scripts/test_ci_contracts.py)：在临时副本中验证 CI 能发现检查缺失和错误结果。
- [.github/workflows/](.github/workflows/)：自动验证与手动演示工作流。

本仓库不包含文章全文或个人项目材料。示例用于说明机制如何落在已有工程上，不能替代真实项目的风险判断。
