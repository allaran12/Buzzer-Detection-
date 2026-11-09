#!/usr/bin/env python3
"""
Labeling Helper Script - Interactive CLI for buzzer account labeling
Usage: python labeling_helper.py [batch]
  python labeling_helper.py batch2
  python labeling_helper.py batch3
"""

import pandas as pd
import sys
import os

BATCH_CONFIG = {
    "batch2": {
        "top30": "../../data/labels/batch2_top30_for_review.csv",
        "random20": "../../data/labels/batch2_random20_for_review.csv",
        "posts": "../../data/features/batch2_posts_with_features.csv",
        "combined": "../../data/labels/batch2_labeled_combined.csv",
        "name": "Batch 2 (wowo2)",
    },
    "batch3": {
        "top30": "../../data/labels/batch3_top30_for_review.csv",
        "random20": "../../data/labels/batch3_random20_for_review.csv",
        "posts": "../../data/features/batch3_posts_with_features.csv",
        "combined": "../../data/labels/batch3_labeled_combined.csv",
        "name": "Batch 3 (RoySuryo)",
    },
}

class LabelingHelper:
    def __init__(self, batch_id):
        cfg = BATCH_CONFIG[batch_id]
        self.top30_path = cfg["top30"]
        self.random20_path = cfg["random20"]
        self.posts_path = cfg["posts"]
        self.combined_path = cfg["combined"]
        self.batch_name = cfg["name"]

        self.top30 = None
        self.random20 = None
        self.posts = None
        self.current_df = None

    def load_data(self):
        try:
            self.top30 = pd.read_csv(self.top30_path)
            self.random20 = pd.read_csv(self.random20_path)
            self.posts = pd.read_csv(self.posts_path)
            print("✓ Data loaded successfully\n")
            return True
        except FileNotFoundError as e:
            print(f"✗ Error: {e}")
            return False

    def show_account_detail(self, username):
        account = self.current_df[self.current_df["username"] == username].iloc[0]
        account_posts = self.posts[self.posts["username"] == username].sort_values("date")

        print("\n" + "="*70)
        print(f"ACCOUNT: @{username}")
        print("="*70)

        print(f"\n📊 METRICS:")
        print(f"  Buzzer Score: {account['buzzer_score']:.3f}")
        print(f"  Posts: {account['n_posts']}")
        print(f"  Post Rate: {account['post_rate']:.2f} posts/hour")
        print(f"  Avg Hashtags: {account['avg_tags']:.1f}")
        print(f"  Avg Body Length: {account['avg_body_len']:.0f} chars")
        if 'out_degree' in account.index:
            print(f"  Out-degree (replies/quotes): {account['out_degree']:.0f}")
        if 'follower_ratio' in account.index:
            print(f"  Follower Ratio: {account['follower_ratio']:.2f}")

        print(f"\n📝 SAMPLE POSTS (showing {min(5, len(account_posts))}):")
        for i, (_, post) in enumerate(account_posts.head(5).iterrows(), 1):
            date_str = pd.to_datetime(post['date']).strftime('%Y-%m-%d %H:%M')
            text_preview = str(post['text'])[:600].replace('\n', ' ')
            print(f"\n  {i}. [{date_str}]")
            print(f"     {text_preview}...")
            if post.get('relation_type') in ['reply', 'quote']:
                print(f"     → {post['relation_type'].upper()} to: {post.get('target_username', 'N/A')}")

        print("\n" + "="*70)

    def get_label_input(self, username):
        while True:
            print("\n🏷️  LABEL OPTIONS:")
            print("  1 = Buzzer (coordinated, spam, fake)")
            print("  0 = Organic (genuine user)")
            print("  s = Skip (review later)")
            print("  d = Show detail again")
            print("  q = Quit and save")

            choice = input("\nYour choice: ").strip().lower()

            if choice == '1':    return 1, ""
            elif choice == '0':  return 0, ""
            elif choice == 's':  return None, ""
            elif choice == 'd':
                self.show_account_detail(username)
                continue
            elif choice == 'q':  return 'quit', ""
            else: print("Invalid choice. Try again.")

    def label_batch(self, df, batch_name):
        self.current_df = df
        labeled_count = 0

        print(f"\n{'='*70}")
        print(f"LABELING: {batch_name}")
        print(f"{'='*70}")
        print(f"Total accounts: {len(df)}")
        print(f"Already labeled: {df['label'].notna().sum()}")
        print(f"Remaining: {df['label'].isna().sum()}\n")

        for idx, row in df.iterrows():
            username = row['username']
            if pd.notna(row['label']) and row['label'] != '':
                continue
            self.show_account_detail(username)
            label, notes = self.get_label_input(username)
            if label == 'quit':
                break
            elif label is None:
                print(f"⏭️  Skipped @{username}")
            else:
                df.at[idx, 'label'] = label
                df.at[idx, 'notes'] = notes
                labeled_count += 1
                print(f"✓ Labeled @{username} as {'BUZZER' if label == 1 else 'ORGANIC'}")

        return df, labeled_count

    def save_progress(self):
        if self.top30 is not None:
            self.top30.to_csv(self.top30_path, index=False)
            print(f"✓ Saved: {self.top30_path}")
        if self.random20 is not None:
            self.random20.to_csv(self.random20_path, index=False)
            print(f"✓ Saved: {self.random20_path}")

        if self.top30 is not None and self.random20 is not None:
            labeled_top = self.top30[self.top30['label'].notna()]
            labeled_random = self.random20[self.random20['label'].notna()]
            if len(labeled_top) > 0 or len(labeled_random) > 0:
                combined = pd.concat([labeled_top, labeled_random], ignore_index=True)
                combined.to_csv(self.combined_path, index=False)
                print(f"✓ Saved combined: {self.combined_path}")
                print(f"  Total labeled: {len(combined)}")
                print(f"    Buzzer: {(combined['label'] == 1).sum()}")
                print(f"    Organic: {(combined['label'] == 0).sum()}")

    def show_progress(self):
        total_top = len(self.top30)
        labeled_top = self.top30['label'].notna().sum()
        total_random = len(self.random20)
        labeled_random = self.random20['label'].notna().sum()
        total = total_top + total_random
        labeled = labeled_top + labeled_random

        print(f"\n{'='*70}")
        print(f"LABELING PROGRESS - {self.batch_name}")
        print(f"{'='*70}")
        print(f"Top 30: {labeled_top}/{total_top} ({labeled_top/total_top*100:.0f}%)")
        print(f"Random 20: {labeled_random}/{total_random} ({labeled_random/total_random*100:.0f}%)")
        print(f"TOTAL: {labeled}/{total} ({labeled/total*100:.0f}%)")

        if labeled >= 50:
            print("\n✓ All accounts labeled! Ready for training.")
        else:
            print(f"\n⏳ {total - labeled} accounts remaining")

    def run(self):
        print("="*70)
        print(f"BUZZER LABELING HELPER - {self.batch_name}")
        print("="*70)

        if not self.load_data():
            return

        while True:
            self.show_progress()
            print("\n📋 MENU:")
            print("  1. Label Top 30 (suspicious)")
            print("  2. Label Random 20 (baseline)")
            print("  3. Save progress")
            print("  4. Exit")

            choice = input("\nSelect: ").strip()
            if choice == '1':
                self.top30, count = self.label_batch(self.top30, "Top 30 Suspicious")
                if count > 0: self.save_progress()
            elif choice == '2':
                self.random20, count = self.label_batch(self.random20, "Random 20 Baseline")
                if count > 0: self.save_progress()
            elif choice == '3':
                self.save_progress()
            elif choice == '4':
                self.save_progress()
                print("\n✓ Progress saved. Goodbye!")
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    batch_id = sys.argv[1] if len(sys.argv) > 1 else None

    if batch_id not in BATCH_CONFIG:
        print("Usage: python labeling_helper.py [batch2|batch3]")
        print(f"Available: {list(BATCH_CONFIG.keys())}")
        sys.exit(1)

    helper = LabelingHelper(batch_id)
    try:
        helper.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted. Saving progress...")
        helper.save_progress()
        print("✓ Progress saved. Exit.")
        sys.exit(0)
