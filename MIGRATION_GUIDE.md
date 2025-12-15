# 移行ガイド

## 段階的移行の手順

### ステップ1: 新しいレイヤー構造の確認

新しいフォルダ構成が作成されていることを確認：
```
domain/
application/
infra/
ui/
```

### ステップ2: 既存コードの部分的な置き換え

既存の`app.py`から、以下の部分を新しい構造に置き換えます：

#### 2-1. インポート部分の追加

```python
# 既存のインポート
import streamlit as st
import yfinance as yf
# ...

# 新しいレイヤー構造を追加
from infra.db import DatabaseRepository
from infra.data_fetcher import StockDataFetcher
from application.game_service import GameService
from application.trading_service import TradingService
from domain.models import GameState, Portfolio, PlayerState
```

#### 2-2. 初期化部分の置き換え

**変更前:**
```python
if "db_conn" not in st.session_state:
    st.session_state.db_conn = init_db()
```

**変更後:**
```python
if "db_repo" not in st.session_state:
    st.session_state.db_repo = DatabaseRepository()
```

#### 2-3. データ取得部分の置き換え

**変更前:**
```python
if st.session_state.stock_data is None:
    with st.spinner("データを取得中..."):
        # yfinance直接呼び出し
        data = yf.download(ticker, start=start, end=end)
        # ...
```

**変更後:**
```python
if "data_fetcher" not in st.session_state:
    st.session_state.data_fetcher = StockDataFetcher()

if st.session_state.game_state.get("stock_data") is None:
    with st.spinner("データを取得中..."):
        data, start_date, end_date = st.session_state.data_fetcher.fetch_data(ticker, year)
        # ...
```

#### 2-4. 日付進行部分の置き換え

**変更前:**
```python
# 次の営業日を探す
next_data = data[data.index.date > current_date]
if not next_data.empty:
    st.session_state.current_date = next_data.index[0].date()
    # 経験値計算...
    result = update_exp(st.session_state.db_conn, exp_to_add)
```

**変更後:**
```python
# 状態をドメインモデルに復元
game_state = GameState.from_dict(st.session_state.game_state)
portfolio = Portfolio.from_dict(st.session_state.portfolio_state)

# サービス層を使用
new_game_state, new_portfolio, level_up_result = st.session_state.game_service.advance_date(
    game_state, portfolio, days=1
)

# 状態を保存
st.session_state.game_state = new_game_state.to_dict()
st.session_state.portfolio_state = new_portfolio.to_dict()
```

#### 2-5. 売買処理の置き換え

**変更前:**
```python
if st.button("買い"):
    current_price = display_data.loc[display_data.index[-1], 'Close']
    max_shares = int(st.session_state.cash / current_price)
    if max_shares > 0:
        cost = max_shares * current_price
        st.session_state.cash -= cost
        st.session_state.shares += max_shares
```

**変更後:**
```python
if st.button("買い"):
    current_price = display_data.loc[display_data.index[-1], 'Close']
    portfolio = Portfolio.from_dict(st.session_state.portfolio_state)

    new_portfolio, shares, cost, success = st.session_state.trading_service.buy_stock(
        portfolio, current_price, current_date
    )

    if success:
        st.session_state.portfolio_state = new_portfolio.to_dict()
        st.session_state.cash = new_portfolio.cash
        st.session_state.shares = new_portfolio.shares
```

#### 2-6. チャート生成の置き換え

**変更前:**
```python
# Plotlyチャートを直接生成
fig = go.Figure(data=[go.Candlestick(...)])
# ...
```

**変更後:**
```python
from domain.chart import create_candlestick_chart, calculate_sma

# SMA計算
sma_25_full, sma_75_full = calculate_sma(sma_calc_data)
sma_25 = sma_25_full[sma_25_full.index.isin(display_data.index)]
sma_75 = sma_75_full[sma_75_full.index.isin(display_data.index)]

# チャート生成
fig = create_candlestick_chart(
    display_data=display_data,
    buy_dates=portfolio.buy_dates,
    sma_25_data=sma_25 if sma_25_enabled else None,
    sma_75_data=sma_75 if sma_75_enabled else None,
    player_level=player_level,
    current_date=current_date,
    year=year,
    ticker=ticker
)
```

### ステップ3: 後方互換性の維持

既存の`st.session_state`変数へのアクセスも維持（段階的移行のため）：

```python
# 新しい方法
portfolio = Portfolio.from_dict(st.session_state.portfolio_state)
new_portfolio = ...
st.session_state.portfolio_state = new_portfolio.to_dict()

# 既存の方法も動作（後方互換性）
st.session_state.cash = new_portfolio.cash
st.session_state.shares = new_portfolio.shares
```

### ステップ4: テスト

各機能をテストして、既存の挙動が維持されていることを確認：

1. データ取得
2. 日付進行
3. 売買処理
4. レベルアップ
5. チャート表示

## FastAPI移行時の利点

### 1. domain層（100%再利用可能）

```python
# FastAPIでもそのまま使用可能
from domain.models import Portfolio
from domain.trading import execute_buy

@app.post("/api/buy")
def buy_stock(request: BuyRequest):
    portfolio = Portfolio.from_dict(request.portfolio)
    new_portfolio, shares, cost = execute_buy(portfolio, request.price, request.date)
    return {"portfolio": new_portfolio.to_dict(), "shares": shares, "cost": cost}
```

### 2. application層（90%再利用可能）

```python
# サービス層をそのままAPIエンドポイントとして使用
from application.game_service import GameService
from application.trading_service import TradingService

game_service = GameService(db_repo)
trading_service = TradingService(db_repo)

@app.post("/api/advance-date")
def advance_date(request: AdvanceDateRequest):
    game_state = GameState.from_dict(request.game_state)
    portfolio = Portfolio.from_dict(request.portfolio)
    new_game_state, new_portfolio, level_up = game_service.advance_date(game_state, portfolio)
    return {
        "game_state": new_game_state.to_dict(),
        "portfolio": new_portfolio.to_dict(),
        "level_up": level_up
    }
```

### 3. infra層（90%再利用可能）

```python
# データベース操作はそのまま使用可能
from infra.db import DatabaseRepository

db_repo = DatabaseRepository()
player_stats = db_repo.get_player_stats()
```

### 4. ui層（10%のみ置き換え）

Streamlit依存部分のみ、Reactコンポーネントに置き換え：

```typescript
// React側
const handleLevelUp = (result: LevelUpResult) => {
  if (result.level_up) {
    showToast(result.message);
    if (result.level === 2) {
      unlockCandlestick();
    }
    // ...
  }
};
```

## 注意事項

- 段階的移行のため、既存の`app.py`は残しています
- 新しい構造と既存の構造が混在する期間があります
- 完全移行後は、既存の`app.py`を削除できます
- `st.session_state`は状態保存先としてのみ使用し、計算ロジックは含めない
