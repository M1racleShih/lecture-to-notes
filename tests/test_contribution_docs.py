from pathlib import Path
import unittest

from scripts.validate_contribution import RIGHTS_MARKER


ROOT = Path(__file__).resolve().parents[1]


class ContributionDocsTests(unittest.TestCase):
    def test_pull_request_template_matches_enforced_policy(self):
        template = (ROOT / ".github/PULL_REQUEST_TEMPLATE/pdf-contribution.md").read_text()
        self.assertIn(RIGHTS_MARKER.replace("[x]", "[ ]"), template)
        self.assertIn("`content/inbox/` 目录下直接添加", template)
        self.assertIn("25 MiB", template)
        self.assertIn("最多包含 10 个 PDF", template)
        for field in (
            "课程或活动名称",
            "学校或机构",
            "学期或年份",
            "讲次或主题",
            "讲师",
            "原始来源 URL",
            "文件说明",
        ):
            self.assertIn(field, template)

    def test_contributor_guide_explains_trusted_publish_boundary(self):
        guide = (ROOT / "CONTRIBUTING.md").read_text()
        normalized = " ".join(guide.split())
        for fragment in (
            "Fork + Pull Request",
            "维护者审核合并后才会发布",
            "content/inbox/",
            "ysyecust/lecture-to-notes",
            "断网、只读、非 root 的容器",
            "不是课程库总容量上限",
        ):
            self.assertIn(fragment, normalized)

    def test_inbox_and_issue_template_point_to_the_full_guide(self):
        inbox = (ROOT / "content/inbox/README.md").read_text()
        issue = (ROOT / ".github/ISSUE_TEMPLATE/pdf-contribution.yml").read_text()
        self.assertIn("先 Fork 仓库", inbox)
        self.assertIn("CONTRIBUTING.md", inbox)
        self.assertIn("自己的 Fork 中 commit", issue)
        self.assertIn("CONTRIBUTING.md", issue)


if __name__ == "__main__":
    unittest.main()
