from pathlib import Path

import pandas as pd


def percent_to_float(text: str) -> float:
    return float(text.replace("%", "")) * 0.01


def get_raw_data() -> pd.DataFrame:
    price = pd.read_html(
        "https://www.japan-reit.com/ranking/all#price", encoding="cp932"
    )[0].set_index("証券コード", drop=False)
    asset = pd.read_html(
        "https://www.japan-reit.com/ranking/all#asset", encoding="cp932"
    )[0].set_index("証券コード", drop=False)
    bunpai = pd.read_html(
        "https://www.japan-reit.com/ranking/all#bunpai", encoding="cp932"
    )[0].set_index("証券コード", drop=False)
    return price, asset, bunpai


def get_data() -> pd.DataFrame:
    assert_dict = {
        1: "事業所主体型",
        2: "住居主体型",
        3: "商業施設主体型",
        4: "ホテル主体型",
        5: "物流施設主体型",
        7: "総合型",
        8: "複合型",
        9: "ヘルスケア施設主体型",
    }
    price, asset, bunpai = get_raw_data()
    return pd.concat(
        [
            price.loc[:, "証券コード"],
            price.loc[:, "投資法人名"],
            price.loc[:, "運用資産"].map(lambda x: assert_dict[x]),
            price.loc[:, "分配金利回り"].map(percent_to_float),
            price.loc[:, "NAV倍率"],
            price.loc[:, "時価総額(百万円)"].rename("時価総額(円)") * 1000000,
            asset.loc[:, "資産規模(億円)"].rename("資産規模(円)") * 100000000,
            asset.loc[:, "棟数"],
            asset.loc[:, "平均築年数"],
            asset.loc[:, "NOI利回り"].map(percent_to_float),
            asset.loc[:, "含み損益率"].map(percent_to_float),
            bunpai.loc[:, "年額分配金(円)"],
            bunpai.loc[:, "自己資本利益率（ROE）"].map(percent_to_float),
            bunpai.loc[:, "有利子負債比率"].map(percent_to_float),
        ],
        axis=1,
    )


def store_data() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    data = get_data()
    data.to_parquet(data_dir / "summary.parquet")


if __name__ == "__main__":
    store_data() 