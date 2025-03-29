import streamlit as st

from j_reit_finder import get_data
from j_reit_finder.stock_selector import JREITSelector, ScoringWeights


@st.cache_data(ttl=3600)  # 1時間キャッシュ
def fetch_data():
    """データを取得してキャッシュする関数"""
    return get_data()


def main():
    st.set_page_config(
        page_title="J-REIT銘柄選定アプリ",
        page_icon="🏢",
        layout="wide"
    )

    st.title("🏢 J-REIT銘柄選定アプリ")
    st.markdown("""
    このアプリケーションは、J-REIT銘柄を複数の指標に基づいて評価し、投資に適した銘柄を選定します。
    左側のサイドバーで各評価指標の重みを調整できます。
    """)

    # サイドバーで重みの設定
    st.sidebar.header("評価指標の重み設定")
    
    weights = ScoringWeights(
        distribution_yield=st.sidebar.slider(
            "分配金利回りの重み",
            min_value=0.0,
            max_value=1.0,
            value=0.25,
            step=0.05
        ),
        nav_ratio=st.sidebar.slider(
            "NAV倍率の重み",
            min_value=0.0,
            max_value=1.0,
            value=0.20,
            step=0.05
        ),
        portfolio_quality=st.sidebar.slider(
            "ポートフォリオ質の重み",
            min_value=0.0,
            max_value=1.0,
            value=0.15,
            step=0.05
        ),
        financial_health=st.sidebar.slider(
            "財務健全性の重み",
            min_value=0.0,
            max_value=1.0,
            value=0.20,
            step=0.05
        ),
        market_position=st.sidebar.slider(
            "市場ポジションの重み",
            min_value=0.0,
            max_value=1.0,
            value=0.20,
            step=0.05
        )
    )

    # 重みの合計が1になることを確認
    total_weight = sum([
        weights.distribution_yield,
        weights.nav_ratio,
        weights.portfolio_quality,
        weights.financial_health,
        weights.market_position
    ])

    if abs(total_weight - 1.0) > 0.0001:
        st.sidebar.error("重みの合計が1.0になるように調整してください")
        return

    # データの取得（キャッシュ付き）
    try:
        with st.spinner("データを取得中..."):
            df = fetch_data()
    except Exception as e:
        st.error(f"データの取得に失敗しました: {e}")
        return

    # 表示する銘柄数の設定
    st.sidebar.header("表示設定")
    top_n = st.sidebar.slider(
        "表示する銘柄数",
        min_value=1,
        max_value=20,
        value=5,
        step=1
    )

    # 銘柄選定の実行
    selector = JREITSelector(weights)
    selected_stocks = selector.select_stocks(df, top_n=top_n)

    # 結果の表示
    st.header("選定結果")
    
    # 上位銘柄の基本情報
    st.subheader(f"上位{top_n}銘柄の基本情報")
    basic_info = selected_stocks[[
        '証券コード', '投資法人名', '総合スコア',
        '分配金利回り', 'NAV倍率', '有利子負債比率',
        '時価総額(円)', '資産規模(円)'
    ]].copy()
    
    # 数値のフォーマット
    basic_info['時価総額(円)'] = basic_info['時価総額(円)'].apply(lambda x: f"{x:,.0f}")
    basic_info['資産規模(円)'] = basic_info['資産規模(円)'].apply(lambda x: f"{x:,.0f}")
    basic_info['総合スコア'] = basic_info['総合スコア'].apply(lambda x: f"{x:.3f}")
    basic_info['分配金利回り'] = basic_info['分配金利回り'].apply(lambda x: f"{x:.1%}")
    basic_info['NAV倍率'] = basic_info['NAV倍率'].apply(lambda x: f"{x:.2f}")
    basic_info['有利子負債比率'] = basic_info['有利子負債比率'].apply(lambda x: f"{x:.1%}")
    
    st.dataframe(basic_info, use_container_width=True)

    # スコアの詳細
    st.subheader("スコアの詳細")
    score_columns = [col for col in selected_stocks.columns if 'スコア' in col]
    score_info = selected_stocks[['証券コード', '投資法人名'] + score_columns].copy()
    
    # スコアのフォーマット
    for col in score_columns:
        score_info[col] = score_info[col].apply(lambda x: f"{x:.3f}")
    
    st.dataframe(score_info, use_container_width=True)

    # 評価指標の説明
    st.sidebar.markdown("""
    ### 評価指標の説明
    
    - **分配金利回り**: 投資収益率の指標
    - **NAV倍率**: 純資産価値に対する時価の割合
    - **ポートフォリオ質**: 築年数と棟数による評価
    - **財務健全性**: LTVとROEによる評価
    - **市場ポジション**: 時価総額と資産規模による評価
    """)

if __name__ == "__main__":
    main() 