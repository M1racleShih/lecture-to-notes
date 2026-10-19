# 提交课程 PDF

外部贡献通过 **Fork + Pull Request** 流程提交，维护者审核合并后才会发布到课程库网站：

```text
在自己的 Fork 中添加 PDF  →  发起 Pull Request  →  自动检查 + 维护者审核合并  →  网站发布
```

## 方法一：在 GitHub 网页提交

1. **Fork 仓库**：打开 <https://github.com/ysyecust/lecture-to-notes>，点击右上角 **Fork → Create fork**。
2. **上传 PDF**：在你的 Fork 中打开 `content/inbox/`，点击 **Add file → Upload files**，直接将 `.pdf` 文件上传到该目录下（不要新建子目录，也不要修改其他文件）。
3. **保存 commit**：填写简短提交说明（例如 `content: add CS336 lecture notes`），点击 **Commit changes**。
4. **创建 Pull Request**：点击 **Contribute → Open pull request**，确认 base repository 为 `ysyecust/lecture-to-notes`、base branch 为 `main`，选择 **PDF contribution** 模板，填写课程信息并勾选确认项后提交。

## 方法二：使用命令行提交

先在 GitHub 上 Fork 仓库，然后运行：

```bash
git clone https://github.com/<你的账号>/lecture-to-notes.git
cd lecture-to-notes
git switch -c contribute/<课程简称>
cp /本地路径/lecture.pdf content/inbox/
git add content/inbox/lecture.pdf
git commit -m "content: add <课程名称> lecture notes"
git push -u origin contribute/<课程简称>
```

随后在 GitHub 页面点击 **Compare & pull request**，目标选择 `ysyecust/lecture-to-notes:main`，并按 **PDF contribution** 模板填写课程信息。

## Pull Request 必填信息

- 课程或活动名称
- 学校或机构
- 学期或年份
- 讲次或主题
- 讲师
- 原始来源 URL
- 文件说明（如“前三讲分讲 PDF + 合集”）

来源信息不完整时请注明，不要猜测。

## 文件要求与自动检查

- 每个 Pull Request 仅在 `content/inbox/` 下添加 1–10 个小写 `.pdf` 文件。
- 单个 PDF ≤ 25 MiB，单次 PR 合计 ≤ 100 MiB（仅限单次 PR 自动扫描范围，不是课程库总容量上限）。
- 不得包含符号链接、压缩包、脚本，也不得修改或删除现有文件。
- 只提交你有权用于教育用途分享的资料。

提交后，GitHub Actions 会在断网、只读、非 root 的容器中检查 PDF 结构与活动内容，并提取页数与首页预览供维护者审核。
