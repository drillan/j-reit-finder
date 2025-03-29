from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class ScoringWeights:
    """各評価指標の重み付けを定義するクラス"""
    distribution_yield: float = 0.25  # 分配金利回り
    nav_ratio: float = 0.20          # NAV倍率
    portfolio_quality: float = 0.15   # ポートフォリオ質（築年数、棟数など）
    financial_health: float = 0.20    # 財務健全性（LTV、ROEなど）
    market_position: float = 0.20     # 市場ポジション（時価総額、資産規模など）

class JREITSelector:
    def __init__(self, weights: ScoringWeights = ScoringWeights()):
        self.weights = weights

    def normalize_column(self, df: pd.DataFrame, column: str, ascending: bool = True) -> pd.Series:
        """列の値を0-1の範囲に正規化"""
        return (df[column] - df[column].min()) / (df[column].max() - df[column].min())

    def calculate_distribution_yield_score(self, df: pd.DataFrame) -> pd.Series:
        """分配金利回りのスコアを計算"""
        return self.normalize_column(df, '分配金利回り', ascending=False)

    def calculate_nav_ratio_score(self, df: pd.DataFrame) -> pd.Series:
        """NAV倍率のスコアを計算（1倍に近いほど高スコア）"""
        nav_ratio = df['NAV倍率']
        ideal_ratio = 1.0
        return 1 - abs(nav_ratio - ideal_ratio) / nav_ratio.max()

    def calculate_portfolio_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """ポートフォリオ質のスコアを計算"""
        # 築年数（若いほど高スコア）
        age_score = 1 - self.normalize_column(df, '平均築年数')
        # 棟数（多いほど高スコア）
        building_score = self.normalize_column(df, '棟数')
        return (age_score + building_score) / 2

    def calculate_financial_health_score(self, df: pd.DataFrame) -> pd.Series:
        """財務健全性のスコアを計算"""
        # LTV（低いほど高スコア）
        ltv_score = 1 - self.normalize_column(df, '有利子負債比率')
        # ROE（高いほど高スコア）
        roe_score = self.normalize_column(df, '自己資本利益率（ROE）')
        return (ltv_score + roe_score) / 2

    def calculate_market_position_score(self, df: pd.DataFrame) -> pd.Series:
        """市場ポジションのスコアを計算"""
        # 時価総額（大きいほど高スコア）
        market_cap_score = self.normalize_column(df, '時価総額(円)')
        # 資産規模（大きいほど高スコア）
        asset_size_score = self.normalize_column(df, '資産規模(円)')
        return (market_cap_score + asset_size_score) / 2

    def select_stocks(self, df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """銘柄を評価し、上位銘柄を選定"""
        # 各評価指標のスコアを計算
        scores = pd.DataFrame(index=df.index)
        
        scores['分配金利回りスコア'] = self.calculate_distribution_yield_score(df)
        scores['NAV倍率スコア'] = self.calculate_nav_ratio_score(df)
        scores['ポートフォリオ質スコア'] = self.calculate_portfolio_quality_score(df)
        scores['財務健全性スコア'] = self.calculate_financial_health_score(df)
        scores['市場ポジションスコア'] = self.calculate_market_position_score(df)

        # 総合スコアを計算
        scores['総合スコア'] = (
            scores['分配金利回りスコア'] * self.weights.distribution_yield +
            scores['NAV倍率スコア'] * self.weights.nav_ratio +
            scores['ポートフォリオ質スコア'] * self.weights.portfolio_quality +
            scores['財務健全性スコア'] * self.weights.financial_health +
            scores['市場ポジションスコア'] * self.weights.market_position
        )

        # 結果を元のデータフレームと結合
        result = df.copy()
        result['総合スコア'] = scores['総合スコア']
        
        # スコアの詳細も追加
        for col in scores.columns:
            if col != '総合スコア':
                result[col] = scores[col]

        # 総合スコアでソートして上位銘柄を返す
        return result.sort_values('総合スコア', ascending=False).head(top_n) 