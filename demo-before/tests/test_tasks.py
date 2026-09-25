import unittest

from tasks import pending_tasks


class TaskViewTests(unittest.TestCase):
    def test_pending_view_preserves_order(self):
        items = [
            {"id": 3, "title": "写初稿", "completed": False},
            {"id": 1, "title": "整理资料", "completed": True},
            {"id": 2, "title": "补充来源", "completed": False},
        ]
        self.assertEqual([item["id"] for item in pending_tasks(items)], [3, 2])

    def test_view_edits_do_not_change_source_records(self):
        items = [{"id": 1, "title": "原始任务", "completed": False}]
        result = pending_tasks(items)
        result[0]["title"] = "视图中的临时标题"
        self.assertEqual(items[0]["title"], "原始任务")

    def test_all_completed_yields_empty_view(self):
        self.assertEqual(pending_tasks([{"id": 1, "completed": True}]), [])


if __name__ == "__main__":
    unittest.main()
