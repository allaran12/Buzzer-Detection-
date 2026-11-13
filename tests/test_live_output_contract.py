import unittest

import pandas as pd

from services.inference_api.main import _catalog_account
from src.inference.live_model_inference import (
    _build_graph,
    _sentiment_summary,
    _similarity_evidence,
    prepare_live_posts,
)


class LiveOutputContractTests(unittest.TestCase):
    def _posts(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "post_id": "1",
                    "account_id": "10",
                    "username": "alpha",
                    "name": "Alpha News",
                    "text": "Dukung solusi baik untuk Roy Suryo",
                    "date": "2026-11-12T10:00:00Z",
                    "created": "2020-01-01T00:00:00Z",
                    "avatar": "https://pbs.twimg.com/profile_images/a/avatar_normal.jpg",
                },
                {
                    "post_id": "2",
                    "account_id": "11",
                    "username": "beta",
                    "name": "Beta News",
                    "text": "Dukung solusi baik untuk Roy Suryo",
                    "date": "2026-11-12T10:01:00Z",
                    "created": "2020-01-01T00:00:00Z",
                    "avatar": "https://pbs.twimg.com/profile_images/b/avatar_normal.jpg",
                    "relation_type": "reply",
                    "target_account_id": "10",
                    "target_username": "alpha",
                },
                {
                    "post_id": "3",
                    "account_id": "12",
                    "username": "gamma",
                    "name": "Gamma News",
                    "text": "Berita buruk dan masalah ini harus ditolak",
                    "date": "2026-11-12T10:02:00Z",
                    "created": "2020-01-01T00:00:00Z",
                    "avatar": "https://pbs.twimg.com/profile_images/c/avatar_normal.jpg",
                    "relation_type": "quote",
                    "target_account_id": "10",
                    "target_username": "alpha",
                },
            ]
        )

    def test_live_contract_contains_graph_sentiment_evidence_and_x_avatar(self):
        posts = prepare_live_posts(self._posts(), dataset_id="fixture", issue_id="test")
        interactions, graph_frame, graph_stats = _build_graph(posts)
        similarities, repeated_phrases = _similarity_evidence(posts)
        sentiment, by_account = _sentiment_summary(posts)

        self.assertEqual(len(interactions), 2)
        self.assertEqual(graph_stats["valid_edge_events"], 2)
        self.assertGreaterEqual(graph_stats["graph_edges"], 2)
        self.assertEqual(len(graph_frame), 3)
        self.assertEqual(len(similarities), 3)
        self.assertTrue(repeated_phrases)
        self.assertEqual(repeated_phrases[0]["accountCount"], 2)
        self.assertLessEqual(repeated_phrases[0]["count"], len(posts))
        self.assertEqual(sentiment["total_posts"], 3)
        self.assertIn("positive", sentiment["counts"])
        self.assertIn("fixture:10", by_account)
        self.assertTrue(posts.loc[0, "avatar"].endswith("_400x400.jpg"))

    def test_catalog_handles_missing_optional_values(self):
        account = _catalog_account(
            {
                "account_id": pd.NA,
                "username": "alpha",
                "probability_buzzer": pd.NA,
                "n_posts": pd.NA,
                "followers": pd.NA,
            }
        )

        self.assertEqual(account["id"], "alpha")
        self.assertEqual(account["buzzerScore"], 0)
        self.assertEqual(account["nPostsInDataset"], 0)
        self.assertEqual(account["followers"], 0)


if __name__ == "__main__":
    unittest.main()
