# 团队部署与协作说明（中文）

## 1. 快速回答
- 任意组员只需 **fork/clone 本仓库**，配置好 AWS 凭证与 OpenAI Key 后，执行 `scripts/team_deploy.sh` 即可在自己的 AWS 账户里完成全量部署与测试。
- 部署脚本会自动创建虚拟环境、安装依赖、执行 `cdk bootstrap`（可跳过）以及 `cdk deploy SmartDocProcessingStack`，无需手动逐个配置服务。

## 2. 仓库关键结构
```
├── frontend/                  # 静态站点（S3 + CloudFront 托管）
├── services/                  # 8–12 个 Lambda 微服务
├── infra/cdk/                 # 主 CDK 应用（SmartDocProcessingStack）
├── scripts/team_deploy.sh     # 一键部署脚本
└── TEAM_DEPLOY_GUIDE_ZH.md    # 本文档
```
所有 Lambda 代码、层依赖与前端资源均已包含在仓库内，clone 之后即可直接打包部署。

## 3. 前置条件
1. **AWS 账户 & 权限**：需具备在目标区域（默认 `us-east-1`）创建 S3、Lambda、DynamoDB、SQS、SNS、API Gateway 等服务的权限。
2. **AWS CLI**：安装并运行 `aws configure`，或设置 `AWS_PROFILE` 让脚本可以调用 `aws sts get-caller-identity` 成功。
3. **Python 3.11+ 与 pip**：CDK Python 项目需要 Python 环境；脚本会自动创建 `infra/cdk/.venv`。
4. **OpenAI API Key**：通过环境变量 `OPENAI_API_KEY` 提供，可直接 `export OPENAI_API_KEY=sk-xxxx`，也可在脚本运行时输入。
5. **CDK Bootstrap**：脚本默认执行 `cdk bootstrap`，首次在某个账户/区域使用 CDK 时必需，如已完成可以设置 `SKIP_BOOTSTRAP=1` 跳过。

## 4. 一键部署脚本使用方法
```bash
# 1. Clone 仓库
$ git clone https://github.com/<your-org>/<repo>.git
$ cd 6620_Final\ Project

# 2. （推荐）提前设置 Key
$ export OPENAI_API_KEY=sk-xxxx

# 3. 执行脚本（自动创建 venv、安装依赖、部署 CDK）
$ bash scripts/team_deploy.sh
```
脚本主要流程：
1. 校验 AWS CLI / Python / pip 是否可用，并确认已经登录 AWS。
2. 检查或创建 `infra/cdk/.venv`，安装 `requirements.txt`。
3. 执行 `cdk bootstrap`（可通过 `SKIP_BOOTSTRAP=1` 跳过）。
4. 以当前 `OPENAI_API_KEY` 作为环境变量运行 `cdk deploy SmartDocProcessingStack --require-approval never`。
5. 完成后在终端输出 API Gateway 与前端网站 URL，供测试使用。

## 5. 手动部署备选流程（脚本失败时可参考）
1. `cd infra/cdk && python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `export OPENAI_API_KEY=sk-xxxx`
4. 若首次使用：`cdk bootstrap`
5. `cdk deploy SmartDocProcessingStack --require-approval never`

## 6. 部署完成后的验证
- 终端会打印三项 `CfnOutput`：`ApiBaseUrl`、`FrontendUrl`、`SmartDocApiEndpoint`，复制 `FrontendUrl` 即可访问 UI 进行上传/搜索测试。
- 可在 AWS 控制台 CloudFormation 中查看 `SmartDocProcessingStack` 是否 `CREATE_COMPLETE/UPDATE_COMPLETE`。
- 如果需要重新部署，只需再次运行脚本；CDK 会自动对比并更新资源。

## 7. 组员协作注意事项
- **环境隔离**：每位同学在自己 AWS 账户运行脚本即可，CloudFormation 会自动生成唯一资源名称，互不干扰。
- **OpenAI Key**：不要把 Key 写入代码或提交仓库，运行脚本前通过环境变量或交互输入。
- **成本控制**：本架构主要使用按量计费的无服务器资源，测试结束后可执行 `cd infra/cdk && source .venv/bin/activate && cdk destroy SmartDocProcessingStack` 回收资源。
- **地区一致性**：脚本默认使用当前 AWS CLI 的区域（建议 `us-east-1`），如需其他区域请在执行前设置 `AWS_REGION`/`AWS_DEFAULT_REGION`。
- **权限问题**：若遇到 `AccessDenied`，请确认 IAM 角色是否具备创建/更新所有相关服务的权限，或由管理员预先分配。

按照以上说明，所有组员都可以通过下载 GitHub 仓库并执行脚本，在自己的 AWS 环境中部署、调试和修复该智能文档处理系统。
