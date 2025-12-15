# リファクタリング設計書

## フォルダ構成

```
Time-Leap-Trader/
├── domain/              # ドメイン層: ゲームルール・状態・純粋関数（UI非依存）
│   ├── __init__.py
│   ├── models.py        # 状態モデル（GameState, Portfolio, PlayerState）
│   ├── exp.py           # 経験値・レベルアップ計算
│   ├── trading.py       # 売買ロジック
│   └── chart.py         # チャート生成ロジック
│
├── application/         # アプリケーション層: ユースケース
│   ├── __init__.py
│   ├── game_service.py  # ゲーム進行のユースケース
│   └── trading_service.py  # 売買のユースケース
│
├── infra/              # インフラ層: DB・外部API
│   ├── __init__.py
│   ├── db.py           # SQLite操作
│   └── data_fetcher.py # yfinance操作
│
├── ui/                 # UI層: Streamlit
│   ├── __init__.py
│   └── level_up_handler.py  # レベルアップUI処理
│
└── app.py              # 既存のStreamlitアプリ（段階的移行用）
```

## レイヤー説明

### domain層（UI非依存）
- **models.py**: ゲームの状態を表すデータクラス
  - `GameState`: ゲーム進行状態
  - `Portfolio`: ポートフォリオ状態
  - `PlayerState`: プレイヤー状態

- **exp.py**: 経験値・レベルアップ計算（純粋関数）
  - `calc_exp_gain()`: 総資産変化から経験値計算
  - `calc_profit_bonus_exp()`: 利確ボーナス経験値計算
  - `check_level_up()`: レベルアップ判定

- **trading.py**: 売買ロジック（純粋関数）
  - `calculate_portfolio_value()`: ポートフォリオ総資産計算
  - `execute_buy()`: 買い注文実行
  - `execute_sell()`: 売り注文実行

- **chart.py**: チャート生成（Plotly、Streamlit非依存）
  - `create_candlestick_chart()`: チャート生成
  - `calculate_sma()`: 移動平均線計算

### application層（ユースケース）
- **game_service.py**: ゲーム進行のユースケース
  - `GameService.advance_date()`: 日付を進める
  - `GameService.reset_game()`: ゲームをリセット

- **trading_service.py**: 売買のユースケース
  - `TradingService.buy_stock()`: 株を購入
  - `TradingService.sell_stock()`: 株を売却

### infra層（DB・外部API）
- **db.py**: データベース操作
  - `DatabaseRepository`: SQLite操作を抽象化

- **data_fetcher.py**: 外部データ取得
  - `StockDataFetcher`: yfinance操作を抽象化

### ui層（Streamlit）
- **level_up_handler.py**: レベルアップ時のUI処理
  - `handle_level_up_ui()`: Streamlit依存のUI処理

## 移行計画

### 段階1: ドメイン層の分離（完了）
- ✅ 状態モデルの分離（models.py）
- ✅ 経験値計算の分離（exp.py）
- ✅ 売買ロジックの分離（trading.py）
- ✅ チャート生成の分離（chart.py）

### 段階2: インフラ層の分離（完了）
- ✅ データベース操作の抽象化（db.py）
- ✅ 外部データ取得の抽象化（data_fetcher.py）

### 段階3: アプリケーション層の分離（完了）
- ✅ ゲーム進行のユースケース（game_service.py）
- ✅ 売買のユースケース（trading_service.py）

### 段階4: UI層の分離（進行中）
- ✅ レベルアップUI処理の分離
- ⏳ 既存のapp.pyを新しいレイヤー構造に移行

### 段階5: FastAPI移行準備
- ⏳ APIエンドポイントの設計
- ⏳ JSON形式での状態管理
- ⏳ Reactフロントエンドとの連携

## 使用例

### 既存コードからの移行例

**変更前:**
```python
# 直接st.session_stateを操作
st.session_state.cash -= cost
st.session_state.shares += max_shares
```

**変更後:**
```python
# ドメインモデルを使用
from domain.models import Portfolio
from domain.trading import execute_buy

portfolio = Portfolio.from_dict(st.session_state.portfolio_state)
new_portfolio, shares, cost = execute_buy(portfolio, current_price, current_date)
st.session_state.portfolio_state = new_portfolio.to_dict()
```

### サービス層の使用例

```python
from infra.db import DatabaseRepository
from infra.data_fetcher import StockDataFetcher
from application.game_service import GameService
from application.trading_service import TradingService
from domain.models import GameState, Portfolio, PlayerState

# 初期化
db_repo = DatabaseRepository()
data_fetcher = StockDataFetcher()
game_service = GameService(db_repo)
trading_service = TradingService(db_repo)

# データ取得
data, start_date, end_date = data_fetcher.fetch_data("7203.T", 2024)

# 状態の復元
game_state = GameState.from_dict(st.session_state.game_state)
portfolio = Portfolio.from_dict(st.session_state.portfolio_state)

# 日付を進める
new_game_state, new_portfolio, level_up_result = game_service.advance_date(
    game_state, portfolio, days=1
)

# 状態を保存
st.session_state.game_state = new_game_state.to_dict()
st.session_state.portfolio_state = new_portfolio.to_dict()
```

## FastAPI移行時の利点

1. **domain層**: そのまま再利用可能（100%）
2. **application層**: サービス層をそのままAPIエンドポイントとして使用可能（90%）
3. **infra層**: データベース操作はそのまま、外部APIも抽象化済み（90%）
4. **ui層**: Streamlit依存部分のみ置き換え（10%）

## 注意事項

- 既存の`app.py`は段階的移行のため残しています
- `st.session_state`は状態保存先としてのみ使用
- 計算・判定ロジックは全て純粋関数またはクラスメソッドに分離
- 将来的にFastAPIからJSON APIとして呼び出せる設計
