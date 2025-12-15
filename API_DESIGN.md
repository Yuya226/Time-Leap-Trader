# FastAPI移行時のAPI設計

## APIエンドポイント設計

### 1. ゲーム状態取得

```python
# GET /api/game/state
{
  "game_state": {
    "current_date": "2024-01-15",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "portfolio": {
    "cash": 1000000,
    "shares": 100,
    "buy_dates": ["2024-01-10"],
    "prev_total_value": 1050000
  },
  "player_state": {
    "initial_capital": 1000000
  },
  "player_stats": {
    "level": 3,
    "exp": 150
  }
}
```

### 2. 日付進行

```python
# POST /api/game/advance-date
Request:
{
  "days": 1
}

Response:
{
  "game_state": {...},
  "portfolio": {...},
  "level_up": {
    "level_up": true,
    "level": 4,
    "old_level": 3,
    "exp": 50
  }
}
```

### 3. 株を購入

```python
# POST /api/trading/buy
Request:
{
  "price": 3000.0,
  "date": "2024-01-15"
}

Response:
{
  "portfolio": {...},
  "shares": 333,
  "cost": 999000.0,
  "success": true
}
```

### 4. 株を売却

```python
# POST /api/trading/sell
Request:
{
  "price": 3100.0
}

Response:
{
  "portfolio": {...},
  "sold_shares": 100,
  "proceeds": 310000.0,
  "profit": 10000.0,
  "level_up": {...}
}
```

### 5. チャートデータ取得

```python
# GET /api/chart/data?start_date=2024-01-01&end_date=2024-01-31
Response:
{
  "chart_data": [...],  # Plotly JSON形式
  "sma_25": [...],
  "sma_75": [...]
}
```

## FastAPI実装例

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import date

from infra.db import DatabaseRepository
from infra.data_fetcher import StockDataFetcher
from application.game_service import GameService
from application.trading_service import TradingService
from domain.models import GameState, Portfolio, PlayerState
from domain.chart import create_candlestick_chart

app = FastAPI()

# 依存性注入
db_repo = DatabaseRepository()
data_fetcher = StockDataFetcher()
game_service = GameService(db_repo)
trading_service = TradingService(db_repo)

# リクエスト/レスポンスモデル
class AdvanceDateRequest(BaseModel):
    days: int = 1

class BuyRequest(BaseModel):
    price: float
    date: date

class SellRequest(BaseModel):
    price: float

# APIエンドポイント
@app.get("/api/game/state")
async def get_game_state():
    """ゲーム状態を取得"""
    # セッション管理（Redis等）から状態を取得
    game_state = GameState.from_dict(session.get("game_state"))
    portfolio = Portfolio.from_dict(session.get("portfolio"))
    player_stats = db_repo.get_player_stats()

    return {
        "game_state": game_state.to_dict(),
        "portfolio": portfolio.to_dict(),
        "player_stats": player_stats
    }

@app.post("/api/game/advance-date")
async def advance_date(request: AdvanceDateRequest):
    """日付を進める"""
    game_state = GameState.from_dict(session.get("game_state"))
    portfolio = Portfolio.from_dict(session.get("portfolio"))

    new_game_state, new_portfolio, level_up = game_service.advance_date(
        game_state, portfolio, request.days
    )

    # セッションに保存
    session["game_state"] = new_game_state.to_dict()
    session["portfolio"] = new_portfolio.to_dict()

    return {
        "game_state": new_game_state.to_dict(),
        "portfolio": new_portfolio.to_dict(),
        "level_up": level_up
    }

@app.post("/api/trading/buy")
async def buy_stock(request: BuyRequest):
    """株を購入"""
    portfolio = Portfolio.from_dict(session.get("portfolio"))

    new_portfolio, shares, cost, success = trading_service.buy_stock(
        portfolio, request.price, request.date
    )

    session["portfolio"] = new_portfolio.to_dict()

    return {
        "portfolio": new_portfolio.to_dict(),
        "shares": shares,
        "cost": cost,
        "success": success
    }

@app.post("/api/trading/sell")
async def sell_stock(request: SellRequest):
    """株を売却"""
    portfolio = Portfolio.from_dict(session.get("portfolio"))

    new_portfolio, sold_shares, proceeds, profit, level_up = trading_service.sell_stock(
        portfolio, request.price
    )

    session["portfolio"] = new_portfolio.to_dict()

    return {
        "portfolio": new_portfolio.to_dict(),
        "sold_shares": sold_shares,
        "proceeds": proceeds,
        "profit": profit,
        "level_up": level_up
    }

@app.get("/api/chart/data")
async def get_chart_data(start_date: date, end_date: date):
    """チャートデータを取得"""
    game_state = GameState.from_dict(session.get("game_state"))
    portfolio = Portfolio.from_dict(session.get("portfolio"))
    player_stats = db_repo.get_player_stats()

    # 表示データの準備
    data = game_state.stock_data
    display_data = data[
        (data.index.date >= start_date) &
        (data.index.date <= end_date)
    ]

    # チャート生成
    fig = create_candlestick_chart(
        display_data=display_data,
        buy_dates=portfolio.buy_dates,
        player_level=player_stats['level'],
        current_date=game_state.current_date
    )

    # Plotly FigureをJSONに変換
    chart_json = fig.to_json()

    return {"chart_data": chart_json}
```

## React側の実装例

```typescript
// services/api.ts
export const gameAPI = {
  async getState() {
    const response = await fetch('/api/game/state');
    return response.json();
  },

  async advanceDate(days: number) {
    const response = await fetch('/api/game/advance-date', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ days })
    });
    return response.json();
  },

  async buyStock(price: number, date: string) {
    const response = await fetch('/api/trading/buy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ price, date })
    });
    return response.json();
  },

  async sellStock(price: number) {
    const response = await fetch('/api/trading/sell', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ price })
    });
    return response.json();
  }
};

// components/TradingPanel.tsx
const TradingPanel = () => {
  const [portfolio, setPortfolio] = useState(null);

  const handleBuy = async () => {
    const result = await gameAPI.buyStock(currentPrice, currentDate);
    setPortfolio(result.portfolio);
    if (result.level_up) {
      showLevelUpNotification(result.level_up);
    }
  };

  return (
    <div>
      <button onClick={handleBuy}>買い</button>
      <button onClick={handleSell}>売り</button>
    </div>
  );
};
```

## セッション管理

FastAPI移行時は、`st.session_state`の代わりに以下を使用：

1. **Redis**: セッション状態の保存
2. **JWT**: 認証・セッション管理
3. **データベース**: 永続化が必要な状態

```python
# Redis使用例
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_session(session_id: str):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else {}

def save_session(session_id: str, data: dict):
    redis_client.setex(
        f"session:{session_id}",
        3600,  # 1時間
        json.dumps(data)
    )
```

## まとめ

- **domain層**: 100%再利用可能（そのまま使用）
- **application層**: 90%再利用可能（APIエンドポイントとして使用）
- **infra層**: 90%再利用可能（そのまま使用）
- **ui層**: 10%のみ置き換え（Reactコンポーネントに）

この設計により、Streamlitを捨てても8割以上のコードが再利用可能です。
