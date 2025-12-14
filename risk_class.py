class RiskDiagnosis:
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "あなたの年齢層は？",
                    "options": {
                        "A": {"text": "20-30代", "score": 10}, # 若い＝人的資本がありリスク取れる
                        "B": {"text": "40-50代", "score": 5},
                        "C": {"text": "60代以上", "score": 2},
                    },
                "weight": 0.3, # 重み付け
            },
            {
                "id": 2,
                "text": "保有資産が一時的に20%減りました。どうしますか？",
                "options": {
                    "A": {"text": "すべて売却する", "score": 0}, # 損失回避傾向が強い
                    "B": {"text": "何もしない", "score": 5},
                    "C": {"text": "買い増しする", "score": 10} # リスク選好
                },
                "weight": 0.7 # 心理的耐性は重要なので重くする
            }
        ]
    def calculate_score(self, answers):
        total_score = 0
        max_possible_score = 0

        for i, answer_key in enumerate(answers):
            question = self.questions[i]
            selected_option = question["options"][answer_key]
            total_score += selected_option["score"] * question["weight"]
            max_score_in_q = max(opt["score"] for opt in question["options"].values())
            max_possible_score += max_score_in_q * question["weight"]

            return total_score
    def determine_segment(self, total_score):
        if total_score >= 8.0:
            return {
                "type": "積極型",
                "mentor": "ジョージ・ソロス　/ キャシー・ウッド",
                "strategy": "グロース株・集中投資",
                "risk_tolerance_rate": 0.30
            }
        elif total_score >= 4.0:
            return {
                "type": "バランス型",
                "mentor": "レイ・ダリオ　/ 機関投資家",
                "strategy": "インデックス投資・分散投資",
                "risk_tolerance_rate": 0.15
            }
        else:
            return {
                "type": "保守型",
                "mentor": "ウォーレン・バフェット",
                "strategy": "高配当・債券・現金比率高め",
                "risk_tolerance_rate": 0.05
            }

engine = RiskDiagnosis()

user_answers = ["A", "C"]

score = engine.calculate_score(user_answers)
segment = engine.determine_segment(score)

print(f"スコア: {score}")
print(f"リスク診断結果: {segment['type']}")
print(f"参考メンター: {segment['mentor']}")
