# Stage 4: AI Report Generation (Manual Submission Mode)

このフォルダは、`aggregator.py` によって生成された作業ストーリー（YAML）を、外部の LLM（ChatGPT, Claude, Gemini等）に渡して高品質な日報を生成するためのリソースを管理します。

## 使い方

1. `nippo_system/reports/nsl_story_YYYY-MM-DD.yaml` を開いて内容をコピーします。
2. [PROMPT_TEMPLATE.md](./PROMPT_TEMPLATE.md) の内容をコピーし、末尾にコピーした YAML を貼り付けます。
3. 任意の LLM に送信します。

## 目的
- **プライバシー**: 生の個人データや認証情報を直接 API に送るのではなく、集計済みのセマンティック・データを手動で精査して送信できます。
- **文脈の最大化**: クリック・タイピングのリズムや、アイドル時間（思考時間）といった「行間の文脈」を AI に伝えることで、表層的ではない深い日報を生成させます。
