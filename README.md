# 让 AI 持续贡献：从现有项目补齐机制

这里提供一份可以交给 coding agent 的启动指令，以及一个可运行的 before / after 教学工程。

核心想法是：把“让 AI 持续、稳定地为项目贡献”本身作为一个工程问题来设计。复用已有工程，先补齐一个真实缺口，再把验证入口留给下一次贡献。

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

## 在 GitHub Actions 看一次真实的绿灯与红灯

本仓库有两个工作流：

- **Verify demo behavior**：每次 push / pull request 运行整个对照验证。它确认“before 会掩盖负例、after 会正确失败”，所以预期为绿色；这不代表 before 的检查入口可靠。
- **Gate demo — controlled failure**：手动触发的单次演示，输入 `version` 和 `inject_fault`，直接返回对应检查入口的退出码，不把失败转成成功。

在仓库 Actions 页面选择第二个工作流，通过 **Run workflow** 分别运行：

| 输入 | 预期工作流结果 | 含义 |
| --- | --- | --- |
| `version=before`, `inject_fault=true` | 绿色 | 测试失败被旧入口掩盖，演示错误的绿灯 |
| `version=after`, `inject_fault=true` | 红色 | 新入口把失败传给 CI，演示有效反馈 |
| `version=after`, `inject_fault=false` | 绿色 | 正常代码通过检查 |

第二种组合故意失败，用于证明门槛有效。故障仅注入临时副本，不会修改提交中的业务代码。也可以在本地运行同一演示：

```sh
python scripts/run_gate_demo.py --version before --inject-fault true
python scripts/run_gate_demo.py --version after --inject-fault true
python scripts/run_gate_demo.py --version after --inject-fault false
```

**CI 能反馈失败，与仓库禁止合入失败代码是两件事。** 本仓库工作流不配置分支保护或 ruleset；接入自己项目时，由维护者决定哪些检查必须通过、谁有接纳权限。本示例也不声称验证了多分支合并队列或生产部署。

## 文件导航

- [prompts/maintainer.md](prompts/maintainer.md)：启动指令及完成标准。
- [demo-before/](demo-before/)：检查入口未传递失败状态。
- [demo-after/](demo-after/)：修补后的检查入口。
- [scripts/verify_demo.py](scripts/verify_demo.py)：五个情形的自动复现与证据输出。
- [scripts/run_gate_demo.py](scripts/run_gate_demo.py)：单次演示，原样返回检查入口状态。
- [.github/workflows/](.github/workflows/)：自动验证与手动演示工作流。

本仓库不包含文章全文或个人项目材料。示例用于说明机制如何落在已有工程上，不能替代真实项目的风险判断。
