# Git Strategy

`F:\aicar` 是总工作区，不一定作为一个大 git 仓库。当前阶段不要执行 `git init`。

## Recommended Repositories

- `aicar_sim` 后续可以单独作为一个 git 仓库。
- `vehicle_type_lab` 后续可以单独作为一个 git 仓库。
- `external_repos` 中的第三方仓库只作为参考，不纳入自己的 git。

## Do Not Commit By Default

以下内容默认不提交：

- `datasets`
- `models`
- `logs`
- `outputs`
- 大型图片、视频、模型权重、训练输出
- `external_repos` 里下载的第三方源码

这些目录可以只提交 `README.md` 或 `.gitkeep`，保留目录结构即可。

## GitHub Strategy

如果后续上传 GitHub，建议优先使用私有仓库。等技术路线、合作边界和知识产权归属明确后，再决定哪些内容可以公开。

