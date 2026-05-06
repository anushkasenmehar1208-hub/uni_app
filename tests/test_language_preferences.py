import unittest

from uni_app import uni_app as app_module


class LanguagePreferenceTests(unittest.TestCase):
    def test_reply_language_defaults_to_auto_for_unknown_values(self) -> None:
        self.assertEqual(app_module._normalize_reply_language(""), app_module.LANGUAGE_AUTO)
        self.assertEqual(app_module._normalize_reply_language("Klingon"), app_module.LANGUAGE_AUTO)

    def test_voice_language_can_follow_chat_replies(self) -> None:
        self.assertEqual(
            app_module._normalize_voice_language(""),
            app_module.VOICE_LANGUAGE_SAME_AS_REPLY,
        )
        self.assertEqual(app_module._normalize_voice_language("Sinhala"), "Sinhala")

    def test_language_cache_suffix_separates_answer_cache_entries(self) -> None:
        self.assertNotEqual(
            app_module._language_cache_suffix("English"),
            app_module._language_cache_suffix("Tamil"),
        )

    def test_detects_temporary_reply_language_instruction(self) -> None:
        self.assertEqual(
            app_module._detect_language_directive("reply in Tamil"),
            {"language": "Tamil", "persist": False, "target": "reply"},
        )

    def test_detects_persistent_reply_language_instruction(self) -> None:
        self.assertEqual(
            app_module._detect_language_directive("from now reply in Sinhala"),
            {"language": "Sinhala", "persist": True, "target": "reply"},
        )

    def test_detects_voice_language_instruction(self) -> None:
        self.assertEqual(
            app_module._detect_language_directive("speak in English", default_target="voice"),
            {"language": "English", "persist": False, "target": "voice"},
        )

    def test_language_questions_are_not_treated_as_settings(self) -> None:
        self.assertEqual(app_module._detect_language_directive("what is Tamil language"), {})
        self.assertEqual(app_module._detect_language_directive("Tamil language history"), {})

    def test_everything_language_instruction_targets_chat_and_voice(self) -> None:
        self.assertEqual(
            app_module._detect_language_directive("from now everything in Tamil"),
            {"language": "Tamil", "persist": True, "target": "all"},
        )


if __name__ == "__main__":
    unittest.main()
