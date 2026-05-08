import unittest

from uni_app import uni_app as app_module


class VoiceMarkdownFallbackTests(unittest.TestCase):
    def test_fallback_renders_basic_markdown(self) -> None:
        html = app_module._render_voice_markdown_fallback(
            "Key areas:\n\n"
            "1. **What is OS Scheduling?** Define it.\n"
            "2. **Scheduling Criteria:** CPU utilization.\n\n"
            "Use `RR` for Round Robin."
        )

        self.assertIn("<ol>", html)
        self.assertIn("<strong>What is OS Scheduling?</strong>", html)
        self.assertIn("<code>RR</code>", html)
        self.assertNotIn("**What is OS Scheduling?**", html)

    def test_fallback_escapes_user_supplied_html(self) -> None:
        html = app_module._render_voice_markdown_fallback("<script>alert(1)</script> **safe**")

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("<strong>safe</strong>", html)


if __name__ == "__main__":
    unittest.main()
