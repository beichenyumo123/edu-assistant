# EduAssistant 转向企业入职培训分析报告

生成日期：2026-07-07  
参考论文：A Multi-agent Onboarding Assistant based on Large Language Models, Retrieval Augmented Generation, and Chain-of-Thought  
参考论文文件：`/Users/db/Downloads/3696630.3728611.pdf`  
参考实验手册：`/Users/db/Downloads/Onboarding Buddy Experiment.pdf`  
参考实验仓库：`/Users/db/Documents/Project/OnboardingBuddyExperiment`  
实验仓库来源：`https://github.com/andrei5090/OnboardingBuddyExperiment.git`  
当前项目：`/Users/db/Documents/Project/edu-assistant`

## 1. 结论先行

你们当前的 EduAssistant 已经具备转向“企业入职培训助手”的关键底座：用户体系、文件上传、RAG 检索、ChromaDB 向量库、来源引用、WebSocket 流式对话、Agent 思考步骤展示和在线 RAG 评价指标。相比从论文源码完全复刻，更合理的路线是：以现有 EduAssistant 为产品底座，吸收论文的“多 agent 编排、规划 scratchpad、代码库检索工具、答案增强与校验”思想，把教育/保研场景替换为企业知识、岗位任务和代码库入职场景。

论文的核心价值不在某个具体 UI 或代码实现，而在一个清晰的入职助手范式：

- 把新人的问题先改写为有上下文的问题。
- 由 Onboarding Agent 制定步骤化解决计划。
- 用检索工具查询代码、文档和项目知识。
- 用 Step Processor 并行细化每一步。
- 用 Message Enhancer 校验、整理、格式化最终答案。
- 用用户实验衡量“有用性、易上手程度、任务完成率和反馈”。

你们应该在此基础上做企业版增强：多租户与权限、企业知识源连接、角色化学习路径、任务看板、代码仓库/制度文档混合检索、来源行号、人工升级给 mentor、审计日志和真实入职任务评估。

## 2. 论文是怎么做的

### 2.1 论文要解决的问题

论文关注软件工程团队中新成员的 onboarding。传统入职方式依赖文档、工作坊和 mentor，但大项目里的文档容易过时，mentor 成本高，远程/分布式团队中新人更难快速理解项目上下文。论文提出 Onboarding Buddy，用 LLM、RAG 和自动 Chain-of-Thought 来降低 mentor 负担，帮助新人完成环境配置、代码理解和项目任务。

### 2.2 系统总体架构

论文采用 agent-centric 架构，而不是固定 chain。固定 chain 总是按预设流程执行，agent 则可以根据检索结果和中间状态动态决定下一步。

论文 Figure 1 的整体流程可以概括为：

1. 用户提出项目入职问题。
2. Contextualization Agent 结合历史对话改写问题，使提问具备上下文。
3. Onboarding Agent 生成初始步骤计划。
4. Step Processor 根据计划调用多个 Onboarding Agent，并行或递归地细化子任务。
5. 多个子任务产出被汇总。
6. Message Enhancer Agent 根据代码库再次检查答案，修正不准确处，并输出 Markdown 格式答案。

这套设计的重点是“规划 + 检索 + 分解 + 校验”，不是简单的一次 RAG 问答。

### 2.3 Onboarding Agent 的内部结构

论文 Figure 2 中，Onboarding Agent 由三个核心组件组成：

- Memory Storage：包含数据库和 blob storage。数据库保存用户与 LLM 的历史交互，blob storage 存放项目代码和文档上下文。
- Retrieval Tools：面向软件项目文件做语义检索和整文件拉取。
- Planning Scratchpad：记录中间推理、工具调用、检索结果和下一步计划，帮助 agent 避免重复查询，并在检索失败时改写 query。

Planning Scratchpad 的作用很关键。它既是 agent 的临时工作记忆，也是一种可解释性机制。论文强调，scratchpad 可以帮助定位 agent 哪里走偏、哪里发生了多余工具调用，也能让最终答案整合中间步骤。

### 2.4 RAG 的具体实现

论文中的 RAG 面向代码库和项目文档：

- 使用 GPT-4o 做推理和生成。
- 使用 text-embedding-3-large 做 embedding。
- 使用 FAISS 作为内存型 dense vector database。
- 文件和文档被切成 2000 字符的 chunk，重叠 200 字符。
- 每个 chunk 的 metadata 保存 GitHub URL、项目路径和文件唯一编号。
- 检索工具返回 top 5，设置相似度阈值 0.1。

论文定义了两个配合使用的工具：

- `retrieve_relevant_code_snippets`：用 query 到向量库查相关代码片段。若无结果或重复 query，会给 agent 反馈，促使它改写检索语句。
- `retrieve_missing_files`：根据文件名或上一步工具提示拉取完整源文件。论文把它视为更昂贵的工具，因为整文件拉取更容易引入噪声和成本。

这点对企业版很有启发：不要只做“文档问答”，要让 agent 有不同成本的工具选择。先查片段，再在必要时拉整文件、制度全文、流程页面或 runbook。

### 2.5 实验设计和结果

论文用 8 名程序员做 pilot study，让他们在一个不熟悉的闭源后端项目上完成 3 个入职任务：

1. Setup Task：克隆仓库、修改配置、注册 mock 用户、测试接口，完成开发环境设置。
2. New Payment Option Task：理解订阅支付流程，增加新的支付选项。
3. Questionnaire Duplication Task：新增问卷复制 API，并实现复制逻辑与集成测试。

评价方式包括项目 telemetry，例如代码编辑进展，以及问卷评分。评分范围是 0 到 4。结果为：

- 7/8 参与者完成全部任务。
- 只有 1 名参与者在一个任务中出现小的编码错误。
- 感知有用性均值 M=3.26，SD=0.86。
- 入职容易程度均值 M=3.0，SD=0.96。

用户反馈集中在 UX：希望提供更具体的代码片段和行号、多行输入、导航按钮，以及更快的响应速度。

论文也明确了局限：样本只有 8 人，只覆盖一个代码库，没有严谨 A/B benchmark。未来计划包括多团队、多技术栈、对比 GitHub Copilot 和 ChatGPT 插件、加入更强的幻觉校验和动态项目更新。

### 2.6 实验手册补充信息

新增的 `Onboarding Buddy Experiment.pdf` 是一份 13 页的实验手册，补充了论文中没有详细展开的实验操作流程。它说明该实验由 TU Delft 和 JetBrains Software Engineering Research Department 合作开展，参与者需要模拟新工程师加入一个新项目或新团队的 onboarding 流程。

手册中的关键补充如下：

- 实验工具是 IntelliJ IDEA 插件 Onboarding Buddy，参与者需要安装 IntelliJ、安装插件、接受 GitHub 邀请、输入 UserID，并在插件中完成 consent form。
- 插件中会展示任务入口、任务说明、`Start` 按钮、`Finish Task` 按钮，以及可选的无任务 custom chat。
- 实验任务在手册正文中列为 `Setup`、`New Payment Option`、`Implement Questionnaire Duplication`。不过后续截图里的任务列表显示第三项为 `Add Logging to AuthController`，说明实验材料可能存在版本差异或任务后续调整。产品和评估设计不应过度绑定某一个第三任务名称。
- 实验将参与者分成两组：Group A 使用 Onboarding Buddy 的 ChatGPT-like chat，且不允许使用其他资源或外部帮助；Group B 不提供 chat，可以使用任意工具、文档或外部帮助完成任务。
- Group A 的回答等待时间可能达到 180 秒，这解释了论文结果中用户反馈“希望更快响应”的来源。
- 插件提供 suggested steps/toolbox，用户可以点击建议步骤，例如项目设置，也可以自行输入问题。
- 参与者在完成任务前需要 commit 并 push 到自己的 branch，再点击完成任务并回答问卷。
- 手册强调 Onboarding Buddy 的定位是帮助新人理解 HOW，而不是替新人完成 DO；当用户问题不够具体，或更像让工具直接代做任务时，插件会要求用户重新表述问题。

这份手册对你们的企业入职产品很重要，因为它把论文方案从“技术架构”落到了“真实入职训练流程”：任务入口、实验分组、任务完成按钮、提交前 commit/push、任务后问卷、具体性不足提示、HOW/DO 边界，都可以直接转化为你们产品的任务陪跑和评估机制。

## 3. 实验源码仓库说明

你们 clone 的 `/Users/db/Documents/Project/OnboardingBuddyExperiment` 来源已确认为 `https://github.com/andrei5090/OnboardingBuddyExperiment.git`。本地 git remote 与该地址一致。这个仓库更像论文评估中“被 onboarding 的目标项目”，而不是完整的 Onboarding Buddy 智能体产品实现。

### 3.1 仓库技术栈

仓库 README 和 `build.gradle` 显示它是一个 Spring Boot 后端：

- Java 11。
- Spring Boot 2.5.5。
- Spring Security、OAuth2、JWT。
- Spring Data JPA。
- H2 内存数据库和 MySQL。
- iText PDF、AWS S3、Spring Mail。
- Gradle 构建。
- 集成测试使用 JUnit、MockMvc、Spring Security Test。

README 中写明本地运行方式是 `./gradlew bootRun`，测试方式是 `./gradlew test`，并提到有 65 个测试。

### 3.2 Graphify 结果说明

`graphify-out/GRAPH_REPORT.md` 给出的结构摘要：

- 1183 个节点，2993 条边，61 个 community。
- 核心节点包括 `User`、`Question`、`UserPrincipal`、`UserRepository`、`Questionnaire`。
- 主要社区包括用户、认证、OAuth2、PDF 与法规、题目、问卷、支付、AWS S3、缓存、测试等。
- 未发现 import cycle。
- 弱连接节点包括 servlet upload、JPA/Hibernate 配置、OAuth2 provider、AWS S3 等，说明有一些配置型能力未充分通过代码关系连接。

这说明该仓库是一个完整业务后端，而不是 LLM agent 项目。对你们最有价值的是把它当作“企业入职任务样例库”：新人需要理解配置、权限、业务实体、支付流程、测试流程，这些正是企业入职助手应该支持的任务。

### 3.3 与论文任务的对应关系

Setup Task 对应：

- `src/main/resources/application.yaml` 中 MySQL/H2 配置、邮件配置、OAuth2、S3、server port。
- README 中的本地启动、测试、Docker 部署说明。

New Payment Option Task 对应：

- `PaymentOption.java` 中多个订阅选项，如 30/60/120 天，RON/EUR。
- `PaymentController.java` 中 `/payments` 和 `/payments/confirm`。
- `PaymentsServices.java` 中支付请求生成、第三方回调验证、订阅角色发放。

Questionnaire Duplication Task 对应：

- `QuestionnaireController.java` 中问卷创建、编辑、添加题目、删除题目、查询接口。
- `QuestionnaireServices.java` 中问卷业务逻辑。
- `QuestionnaireControllerIntegrationTest.java` 中创建、编辑、添加/删除题目、删除问卷等集成测试。

注意：当前源码中没有找到论文中完整的 LLM agent orchestrator、FAISS 检索、scratchpad 或 IDE 插件实现。因此不要把这个仓库作为产品代码直接迁入 EduAssistant，它更适合作为测试和演示用的入职目标项目。

### 3.4 对实验手册和仓库的综合判断

结合论文、实验手册和源码仓库，可以把相关材料分成三层：

- 论文：说明 Onboarding Buddy 的 agent/RAG/CoT 架构和 pilot study 结果。
- 实验手册：说明参与者如何安装插件、接受 GitHub 邀请、进入任务、使用 chat、完成任务、提交代码和填写问卷。
- GitHub 仓库：提供被参与者 onboarding 的 Spring Boot 目标项目，用于设置环境、理解支付流程、修改业务逻辑和写测试。

因此，对你们来说最值得吸收的不是仓库里的业务功能，而是“任务化入职实验设计”。企业版可以把它产品化为：

- 新人被分配到一个 role/team/project。
- 系统展示当前阶段任务和完成按钮。
- 每个任务有专属 task chat。
- 支持无任务 custom chat，但默认围绕任务推进。
- 回答不直接代做，优先解释 HOW、指出要看的文件和验证方式。
- 任务完成时要求提交证据，例如截图、链接、commit、PR 或自评问卷。
- 任务结束后收集有用性、难度、卡点和文档缺口。

## 4. 你们当前 EduAssistant 的可复用基础

### 4.1 已有能力

当前项目已经有这些关键能力：

- FastAPI 后端和 Vue 3 前端。
- JWT 登录注册。
- 文件上传、解析、切分和向量化。
- ChromaDB 持久化向量库。
- 本地 BGE embedding，上传和查询共用同一个 embedding 空间。
- WebSocket 流式问答。
- `agent_steps` 持久化，前端可展示 Agent 思考过程。
- 来源引用和在线 RAG 评价指标。
- 资料勾选，可限制检索范围。
- 对话历史窗口。
- 离线 demo LLM fallback。

这些能力已经超过论文中的部分最小原型要求，尤其是你们已经有用户隔离、RAG 质量评估和前端可视化。

### 4.2 与论文相比的主要差距

当前 EduAssistant 仍然是教育场景下的一次式 RAG 问答，缺少企业入职所需的任务编排：

- Agent 类型仍是 `edu` 和 `baoyan`，领域不匹配。
- `edu_agent.py` 只做“检索 -> 拼 prompt -> 生成回答”，没有 Planner、Step Processor、Message Enhancer。
- `agent_steps` 是展示层步骤，不是可被 agent 反复读写的 scratchpad。
- 向量库 metadata 偏学习资料，没有企业知识所需的 team、role、source owner、confidentiality、updated_at、path、line range、commit hash。
- 上传只支持 PDF、docx、txt、md，暂不支持代码仓库、wiki API、issue、runbook、Slack/Teams FAQ 等企业源。
- 没有企业权限模型，例如组织、团队、岗位、文档 ACL、多租户隔离、SSO。
- 没有 onboarding plan、任务 checklist、学习进度和 mentor escalation。
- 没有代码仓库级检索工具，例如按路径拉文件、按符号检索、按依赖关系解释。

另一个小的工程债：`files.py` 里定义了 `infer_source_profile`，但上传流程当前硬编码为 `student_upload/medium`，没有真正使用这个推断结果。企业版需要把这种来源类型和可信等级做成显式元数据，而不是靠文件名临时推断。

## 5. 企业入职培训产品应该怎么改

### 5.1 产品定位

建议把产品从“学习资料问答助手”转为：

企业新人入职助手，面向新员工、mentor、HR、IT、团队负责人，提供公司知识问答、岗位学习路径、项目代码理解、入职任务陪跑和 mentor 分流。

核心用户场景：

- 新员工问：我第一周要完成什么？
- 新员工问：如何配置开发环境？
- 新员工问：这个仓库的模块职责和启动流程是什么？
- 新员工问：报销、请假、权限申请、安全培训在哪里？
- 新员工问：我现在卡在 CI 报错，下一步应该查哪里？
- mentor 问：这位新人还有哪些任务没完成，最近卡在哪？
- 管理员问：哪些入职问题反复出现，哪些文档过时？

### 5.2 推荐的新 Agent 架构

建议把现有双 agent 替换为企业入职多 agent 架构：

1. Contextualization Agent
   - 结合用户角色、团队、入职阶段、历史对话改写问题。
   - 示例：把“这个怎么跑”改写为“后端服务在本地如何配置依赖、环境变量和启动命令”。

2. Onboarding Planner Agent
   - 为复杂问题生成步骤计划。
   - 区分信息型问题、流程型问题、代码任务型问题和权限申请型问题。

3. Knowledge Retrieval Agent
   - 检索制度、HR、IT、流程、产品文档、FAQ。
   - 支持 source trust、owner、更新时间和适用范围过滤。

4. Codebase Retrieval Agent
   - 检索代码库、README、Graphify 报告、架构文档、测试文件。
   - 提供 `retrieve_relevant_code_snippets` 和 `retrieve_missing_files` 类似工具。
   - 输出应包含 repo、path、line range、commit hash。

5. Step Processor
   - 对 Planner 的步骤逐步执行。
   - 对不同步骤并行调用知识检索、代码检索和规则校验。
   - 汇总每个子步骤的证据和风险。

6. Compliance Guard Agent
   - 检查权限、敏感信息、PII、商业机密泄露风险。
   - 对无法回答的问题触发人工升级。

7. Message Enhancer Agent
   - 把子任务结果整理为新人能执行的答案。
   - 强制输出引用、下一步动作、相关联系人和不确定性说明。

8. Mentor Escalation Agent
   - 当资料不足、权限不够、系统报错或用户多次卡住时，把问题整理成 mentor 可接手的上下文。

### 5.3 数据模型建议

在现有 `User`、`Conversation`、`Message`、`Document` 基础上增加企业入职领域模型：

- `Organization`：公司或租户。
- `Team`：部门、业务线、项目组。
- `RoleProfile`：新人岗位，例如后端工程师、前端工程师、销售、客服、产品经理。
- `OnboardingPlan`：入职计划模板。
- `OnboardingTask`：具体任务，例如配置 VPN、跑通后端、阅读安全政策、完成第一张工单。
- `TaskProgress`：新人进度、状态、卡点、完成证据。
- `KnowledgeSource`：知识源连接器，例如上传文件、Git 仓库、Confluence、飞书/钉钉/Notion、Issue 系统。
- `DocumentChunk` 或扩展 Chroma metadata：source_id、source_type、team_id、role_id、confidentiality、owner、updated_at、path、line_start、line_end、commit_sha、trust_level。
- `AgentRun`：一次 agent 编排运行的计划、工具调用、检索证据、耗时和风险。
- `EscalationTicket`：升级给 mentor/HR/IT 的问题摘要和上下文。

### 5.4 检索策略建议

企业场景不建议只用单一向量检索。推荐混合检索：

- 向量检索：适合语义相近的制度、FAQ、概念解释。
- BM25/关键词检索：适合命令、错误码、配置项、类名、接口名。
- 结构化过滤：按团队、岗位、权限、文档类型、更新时间过滤。
- Parent-child chunk：小 chunk 命中后，返回其父文档段落或完整文件片段。
- 整文件工具：只有在片段不足时才拉取完整源文件或完整政策文档。
- 图谱/Graphify 辅助：把仓库依赖、社区、核心节点作为代码库理解的检索入口。

推荐企业版 chunk 策略：

- 制度文档：800 到 1200 中文字符，重叠 150 到 250。
- 技术文档：1000 到 1600 字符，保留标题层级。
- 代码文件：按函数、类、接口、测试用例切分，必要时再用 1200 到 2000 字符窗口。
- Graphify 报告：按 community、god node、suggested questions 切分。

### 5.5 答案格式建议

企业入职助手的答案不应只是解释，而要能驱动行动。建议统一输出：

```markdown
### 结论
一句话回答新人当前问题。

### 你现在要做的步骤
1. ...
2. ...

### 依据
- [来源1] 文档/代码路径/行号/更新时间
- [来源2] ...

### 可能的坑
- ...

### 需要找谁
- 角色或 owner，而不是只给人名。

### 我不确定的地方
- 如果知识库不足，明确说明缺口。
```

对代码任务，则额外输出：

- 涉及文件。
- 关键类/函数。
- 建议测试。
- 可能影响面。
- 可复制的命令。

## 6. 相比论文，你们应该做出的改进

### 6.1 从 IDE 插件扩展为企业工作台

论文主要面向开发者 IDE 内的代码 onboarding。你们可以做更宽的企业入职工作台：

- 入职首页：任务清单、进度、最近卡点。
- 聊天区：支持问制度、问项目、问流程。
- 证据区：展示引用文档、代码路径、行号。
- 任务区：把回答转成 checklist。
- Mentor 区：一键升级问题，带上上下文。
- 管理区：维护知识源、岗位模板、问题统计、文档过期提醒。

这样产品边界比论文更适合“公司的入职培训”，而不只是“工程师代码库理解”。

### 6.2 增加企业权限与安全

论文没有深入处理企业权限和数据治理。企业版必须内建：

- 组织/团队/岗位多租户隔离。
- 文档 ACL 和 source-level 权限过滤。
- SSO/OAuth/OIDC。
- 审计日志，记录谁问了什么、检索了哪些资料、答案引用了哪些来源。
- 敏感信息识别和脱敏。
- 禁止越权引用。例如 HR 薪酬政策不能被普通团队文档检索泄露。
- 数据保留和删除策略。

### 6.3 把 scratchpad 产品化

论文里的 scratchpad 是 agent 内部工作记忆。企业版不应暴露原始 chain-of-thought，但可以暴露结构化、可审计的“工作轨迹”：

- 已理解的问题。
- 拆解出的任务步骤。
- 调用过的知识源。
- 采用和放弃的证据。
- 当前不确定点。
- 下一步建议。

你们现有前端已有 Agent 思考过程折叠面板，可以把它升级成“执行轨迹”，而不是展示空泛的“正在检索/正在生成”。

### 6.4 强化评估体系

论文的评估规模较小，你们可以从一开始设计更可复用的 benchmark：

- 新人任务完成率。
- 平均完成时间。
- mentor 被打扰次数。
- 首次独立完成任务时间。
- RAG 命中率、引用有效率、幻觉风险。
- 文档缺口发现数。
- 用户满意度。
- 与普通 ChatGPT、Copilot、纯文档搜索的 A/B 对比。
- 分组实验：参考手册中的 Group A/Group B，但企业版可以改成“使用入职助手”和“只用传统文档/mentor”两组。
- 提交证据：参考手册中的 commit/push 要求，企业版可要求任务完成时提交 PR、工单链接、截图或问卷。
- HOW/DO 边界：统计用户要求代做任务、问题不够具体、被系统要求改写问题的次数。

你们现有 `evaluation.py` 已经有在线 RAG 指标，可以继续扩展为企业 dashboard。

### 6.5 支持动态知识更新

论文未来工作提到要减少对预编码项目数据的依赖。企业版建议优先实现增量同步：

- Git commit webhook 触发代码重新索引。
- 文档更新时间检查。
- 删除或归档过期 chunk。
- 显示资料 freshness。
- 对超过有效期的制度或 runbook 降低 trust level。

## 7. 建议落地路线图

### 阶段 1：MVP，2 到 3 周

目标：把 EduAssistant 改成“企业知识库 + 入职问答助手”。

后端：

- 新增 `onboarding_agent.py`，替换教育 prompt。
- 把 agent 类型从 `edu/baoyan` 调整为 `onboarding/general` 或 `onboarding/code/policy`。
- 扩展 Document metadata：source_type、team、role、owner、trust_level、updated_at。
- 使用 `infer_source_profile` 或更明确的上传表单，而不是硬编码来源类型。
- 增加 onboarding system prompt，要求回答含步骤、依据、风险和升级建议。

前端：

- 将“教育助手/保研助手”改成“入职助手/知识库/任务”。
- 文件抽屉改为“企业知识源”。
- 来源展示增加 owner、更新时间、适用团队、可信等级。
- Agent 思考过程改成“执行轨迹”。

验收标准：

- 新人上传公司制度和项目 README 后，能回答流程类、制度类、项目类问题。
- 回答必须带来源。
- 没有资料时明确拒答或给出补充资料建议。

### 阶段 2：任务化 onboarding，3 到 5 周

目标：从问答升级为入职任务陪跑。

新增能力：

- OnboardingPlan 和 OnboardingTask。
- 角色模板，例如后端工程师第一周、前端工程师第一周、销售第一周。
- 任务状态：未开始、进行中、卡住、待 mentor、完成。
- Agent 可以把问题转成 checklist。
- 卡住时生成 mentor escalation 摘要。

验收标准：

- 新人登录后能看到自己的第一周任务。
- 每个任务都能关联知识来源和问答历史。
- mentor 能看到新人卡点摘要。

### 阶段 3：代码库 onboarding，4 到 6 周

目标：实现论文中最有差异化的代码项目入职能力。

新增能力：

- Git 仓库导入和增量索引。
- 代码 chunk 按文件、类、函数、测试分块。
- metadata 增加 repo、path、line_start、line_end、commit_sha。
- 实现两个代码工具：片段检索和整文件拉取。
- 将 Graphify 报告作为代码图谱摘要导入知识库。
- 回答中提供文件路径和行号。

验收标准：

- 对一个陌生仓库，用户能问“如何启动”“某功能在哪里实现”“新增一个选项要改哪些文件”。
- 答案能给出文件路径、相关测试和风险。
- 至少复现论文的三类任务评估：环境设置、增加配置/业务选项、新增 API 与测试。

### 阶段 4：多 agent 编排，4 到 8 周

目标：从单 agent RAG 升级到论文式规划和校验。

新增能力：

- Contextualization Agent。
- Planner Agent。
- Step Processor。
- Knowledge Retrieval Agent。
- Codebase Retrieval Agent。
- Message Enhancer Agent。
- Compliance Guard Agent。
- `AgentRun` 持久化工具调用和中间证据。

验收标准：

- 复杂问题会先生成执行计划。
- 每一步能独立检索、返回证据和耗时。
- 最终答案由 Message Enhancer 统一格式化。
- 对低置信度答案能提示不确定性或升级给 mentor。

### 阶段 5：企业级治理和评估，持续迭代

目标：达到真实公司可试点的稳定性。

新增能力：

- 多租户和 RBAC。
- SSO。
- 审计日志。
- PII 和敏感信息治理。
- 文档 freshness。
- 管理员知识缺口看板。
- A/B 评估和任务完成率统计。

## 8. 推荐的最小技术改造清单

优先级 P0：

- 新建企业入职版系统 prompt。
- 新建 `onboarding_agent.py`，复用现有 RAG。
- 前端文案和 agent 类型从教育场景切换到入职场景。
- 扩展上传元数据，至少支持 source_type、team、role、trust_level。
- 答案强制包含来源、下一步动作和不确定性说明。

优先级 P1：

- 增加 OnboardingTask、OnboardingPlan、TaskProgress。
- Agent 输出结构化 checklist。
- 保存更细粒度的 `agent_steps`，包括 query、命中文档、检索耗时。
- 支持 Graphify 报告导入和问答。
- 给来源增加 path/line 信息。

优先级 P2：

- Git 仓库导入。
- 混合检索。
- Step Processor。
- Message Enhancer。
- Mentor escalation。

优先级 P3：

- 企业连接器。
- SSO、多租户、RBAC。
- 审计和安全策略。
- A/B benchmark dashboard。

## 9. 企业入职版 Prompt 草案

```text
你是企业入职助手，帮助新员工理解公司制度、团队流程、项目代码和当前入职任务。

回答规则：
1. 优先基于检索到的企业知识、代码、流程文档和任务模板回答。
2. 关键结论必须标注来源。
3. 如果资料不足，明确说明缺口，不要编造。
4. 对流程类问题，输出可执行步骤。
5. 对代码类问题，输出涉及文件、函数、测试和风险。
6. 对权限、薪酬、合规、隐私、生产操作等高风险问题，提示按公司制度执行，并建议找对应 owner 确认。
7. 回答结尾给出下一步行动。

输出结构：
- 结论
- 操作步骤
- 依据
- 风险或注意事项
- 需要找谁
- 下一步
```

## 10. 对当前项目的具体改造建议

### 10.1 后端目录建议

建议逐步形成如下模块：

```text
backend/app/agents/
  onboarding_agent.py
  contextualization_agent.py
  planner_agent.py
  step_processor.py
  message_enhancer.py
  compliance_guard.py

backend/app/rag/
  retriever.py
  code_retriever.py
  hybrid_retriever.py
  source_indexer.py

backend/app/models/
  organization.py
  team.py
  role_profile.py
  onboarding_plan.py
  onboarding_task.py
  task_progress.py
  knowledge_source.py
  agent_run.py
```

### 10.2 现有模块迁移方式

- `edu_agent.py`：保留为参考，复制并改造成 `onboarding_agent.py`。
- `baoyan_agent.py`：企业版初期可以删除或隐藏，不作为主产品能力。
- `files.py`：从“学习资料上传”改为“知识源上传”，增加来源类型和适用范围。
- `retriever.py`：保留格式化来源能力，扩展企业 metadata。
- `evaluation.py`：保留并扩展，增加 task completion、mentor escalation、source freshness。
- `ChatView.vue`：保留聊天和来源面板，重做信息架构。

### 10.3 数据隔离建议

当前向量库按 user_id 隔离，这适合个人学习，但不适合公司知识库。企业版建议改为：

- organization 级公共知识库。
- team/project 级知识库。
- user 私有知识库。
- 检索时按用户权限合并可见范围。

也就是说，collection 可以从 `user_{user_id}` 演进为：

- `org_{org_id}_public`
- `team_{team_id}`
- `project_{project_id}`
- `user_{user_id}_private`

检索时需要带 ACL filter，而不是只按 user_id 查。

## 11. 建议的 Demo 设计

为了快速展示企业入职转型，建议做一个小型 demo：

### Demo 数据

- 公司员工手册：请假、报销、安全规范。
- IT 入职文档：VPN、邮箱、代码权限。
- 项目 README：如何启动后端和前端。
- Graphify 生成的目标项目报告。
- 一份“后端工程师第一周入职任务清单”。
- 一份“实验手册式任务说明”，包含任务开始、任务完成、提交证据、任务后问卷。
- `OnboardingBuddyExperiment` 仓库作为代码入职样例项目。

### Demo 问题

- 我第一天要完成哪些任务？
- 后端项目怎么在本地跑起来？
- 如果我要新增一个支付套餐，应该看哪些文件？
- 问卷相关接口在哪里？
- 我需要找谁开通生产日志权限？
- 当前资料里有没有说明报销截止时间？
- 我这个问题是不是太像让你直接帮我做任务了？我应该怎么改问？

### Demo 成功标准

- 每个回答都有来源。
- 代码问题能返回路径和测试建议。
- 资料不足时不乱编。
- 能把回答转换成 checklist。
- 能把卡点升级为 mentor 问题摘要。
- 对任务型问题能够解释 HOW，但不直接替新人完成 DO。
- 完成任务时能收集提交证据和任务后反馈。

## 12. 最终建议

不要直接照搬论文源码，也不要把当前 EduAssistant 简单改名。最优路线是：

1. 用当前 EduAssistant 作为工程底座。
2. 用论文作为多 agent onboarding 架构蓝图。
3. 用实验手册作为任务化入职流程和 A/B 评估参考。
4. 用 OnboardingBuddyExperiment 仓库作为代码入职评估样例。
5. 先做“企业知识问答 + 入职任务清单”MVP。
6. 再做“代码库检索 + Step Processor + Message Enhancer”。
7. 最后补齐企业权限、安全、审计和评估体系。

这样既能快速演示价值，又能逐步接近论文中更强的 multi-agent onboarding assistant。
