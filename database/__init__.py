"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class MetalPrice(Base):
    """金属价格记录表"""
    __tablename__ = "metal_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metal_type = Column(String(50), nullable=False, index=True)  # 金属类型（铜/铝/锌等）
    metal_symbol = Column(String(20), nullable=False)            # 金属代号
    price = Column(Float, nullable=False)                        # 当前价格
    change_pct = Column(Float, default=0.0)                      # 涨跌幅%
    high = Column(Float, default=0.0)                            # 日内最高
    low = Column(Float, default=0.0)                             # 日内最低
    volume = Column(Float, default=0.0)                          # 成交量
    source = Column(String(50), default="模拟")                   # 数据来源
    timestamp = Column(DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f"<MetalPrice {self.metal_type}: ¥{self.price} ({self.change_pct:+.2f}%)>"


class Inventory(Base):
    """库存管理表"""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metal_type = Column(String(50), nullable=False, index=True)
    metal_symbol = Column(String(20), nullable=False)
    quantity_kg = Column(Float, nullable=False)         # 库存数量（公斤）
    avg_cost_price = Column(Float, nullable=False)      # 平均进货成本（元/公斤）
    current_market_price = Column(Float, default=0.0)   # 当前市场价（元/公斤）
    total_cost = Column(Float, default=0.0)             # 总成本
    current_value = Column(Float, default=0.0)          # 当前市值
    profit_loss = Column(Float, default=0.0)            # 浮动盈亏
    profit_loss_pct = Column(Float, default=0.0)        # 盈亏百分比
    storage_location = Column(String(100), default="主仓库")
    quality_grade = Column(String(20), default="一级")   # 品质等级
    status = Column(String(20), default="持有")          # 状态：持有/已售出
    purchase_date = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    notes = Column(Text, default="")

    def __repr__(self):
        return f"<Inventory {self.metal_type}: {self.quantity_kg}kg @ ¥{self.avg_cost_price}>"


class Transaction(Base):
    """交易记录表"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String(10), nullable=False)  # 买入/卖出
    metal_type = Column(String(50), nullable=False, index=True)
    metal_symbol = Column(String(20), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    counterparty = Column(String(100), default="")         # 交易对手
    profit = Column(Float, default=0.0)                    # 利润（仅卖出时）
    profit_pct = Column(Float, default=0.0)                # 利润率
    transaction_date = Column(DateTime, default=datetime.now, index=True)
    notes = Column(Text, default="")

    def __repr__(self):
        return f"<Transaction {self.transaction_type} {self.metal_type}: {self.quantity_kg}kg @ ¥{self.price_per_kg}>"


class Recommendation(Base):
    """AI推荐记录表"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metal_type = Column(String(50), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    confidence = Column(Float, default=0.0)
    suggested_quantity_kg = Column(Float, default=0.0)
    suggested_price = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    expected_profit_pct = Column(Float, default=0.0)
    reason = Column(Text, default="")
    trend_analysis = Column(Text, default="")
    risk_level = Column(String(10), default="中")
    created_at = Column(DateTime, default=datetime.now, index=True)
    is_executed = Column(Boolean, default=False)
    executed_at = Column(DateTime, nullable=True)
    # 🆕 回测字段
    outcome_checked = Column(Boolean, default=False)    # 是否已检查结果
    outcome_3d_pct = Column(Float, nullable=True)       # 3日后涨跌%
    outcome_7d_pct = Column(Float, nullable=True)       # 7日后涨跌%
    outcome_30d_pct = Column(Float, nullable=True)      # 30日后涨跌%
    was_correct = Column(Boolean, nullable=True)        # 方向是否正确

    def __repr__(self):
        return f"<Recommendation {self.metal_type}: {self.action} (信心:{self.confidence:.0%})>"


class PriceAlert(Base):
    """价格预警表"""
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metal_type = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(10), nullable=False)          # 高于/低于
    trigger_price = Column(Float, nullable=False)
    current_price = Column(Float, default=0.0)
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    message = Column(Text, default="")
    notified = Column(Boolean, default=False)

    def __repr__(self):
        return f"<PriceAlert {self.metal_type}: {self.alert_type} ¥{self.trigger_price}>"


class Supplier(Base):
    """供应商表"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    contact = Column(String(50), default="")
    phone = Column(String(30), default="")
    address = Column(String(200), default="")
    metal_types = Column(String(200), default="")            # 供应的金属类型
    reliability = Column(Integer, default=3)                 # 信誉评级 1-5
    total_transactions = Column(Integer, default=0)
    total_volume_kg = Column(Float, default=0.0)
    last_transaction_date = Column(DateTime, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)


class Customer(Base):
    """客户表"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    contact = Column(String(50), default="")
    phone = Column(String(30), default="")
    address = Column(String(200), default="")
    metal_types = Column(String(200), default="")
    credit_rating = Column(Integer, default=3)               # 信用评级 1-5
    total_transactions = Column(Integer, default=0)
    total_volume_kg = Column(Float, default=0.0)
    last_transaction_date = Column(DateTime, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(engine)
    # 自动迁移：为已存在的表添加缺失列
    _migrate_add_columns()


def _migrate_add_columns():
    """自动检测并添加缺失的列"""
    from sqlalchemy import text, inspect
    inspector = inspect(engine)
    migrations = {
        "recommendations": [
            ("outcome_checked", "BOOLEAN", "0"),
            ("outcome_3d_pct", "FLOAT", None),
            ("outcome_7d_pct", "FLOAT", None),
            ("outcome_30d_pct", "FLOAT", None),
            ("was_correct", "BOOLEAN", None),
        ],
    }
    with engine.connect() as conn:
        for table_name, columns in migrations.items():
            try:
                existing = {c["name"] for c in inspector.get_columns(table_name)}
                for col_name, col_type, default_val in columns:
                    if col_name not in existing:
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                        if default_val is not None:
                            sql += f" DEFAULT {default_val}"
                        conn.execute(text(sql))
                        conn.commit()
            except Exception:
                pass
