import streamlit as st
from datetime import datetime
import pandas as pd

from modules.database import (
    add_health_record,
    get_health_records
)

from modules.health_score import health_score



def health_record(username):


    st.subheader(
        "📈 今日の健康記録"
    )


    # ==========================
    # セッション初期化
    # ==========================

    if "health_saved" not in st.session_state:

        st.session_state.health_saved = False


    if "today_health_result" not in st.session_state:

        st.session_state.today_health_result = None



    # ==========================
    # 入力
    # ==========================


    weight = st.number_input(

        "体重(kg)",

        30.0,

        120.0,

        55.0,

        step=0.1,

        key="health_weight"

    )



    high = st.number_input(

        "最高血圧",

        80,

        220,

        120,

        key="health_high"

    )



    low = st.number_input(

        "最低血圧",

        40,

        150,

        80,

        key="health_low"

    )



    st.metric(
        "💧 今日の水分量",
        f"{st.session_state.water_today} mL"
    )

    water = st.session_state.water_today



    medicine = st.checkbox(

        "今日は薬を飲みました",

        key="health_medicine"

    )





    # ==========================
    # 保存
    # ==========================


    if st.button(

        "💾 健康記録を保存",

        key="save_health"

    ):



        # 健康スコア計算

        score, star, advice = health_score(

            water,

            medicine,

            high,

            low

        )



        today = datetime.now().strftime(

            "%Y-%m-%d"

        )



        # データベース保存

        add_health_record(

            username,

            today,

            weight,

            high,

            low,

            water,

            medicine,

            score

        )



        # 表示用保存

        st.session_state.today_health_result = {

            "score": score,

            "star": star,

            "advice": advice

        }



        st.session_state.health_saved = True



        st.success(

            "健康記録を保存しました😊"

        )





    # ==========================
    # 今日の結果表示
    # ==========================


    if st.session_state.health_saved:


        result = st.session_state.today_health_result


        st.write("---")


        st.subheader(

            "🌟 今日の健康スコア"

        )



        st.metric(

            "健康スコア",

            f"{result['score']}点"

        )



        st.write(

            result["star"]

        )



        st.subheader(

            "🤖 AI健康アドバイス"

        )



        if result["advice"]:


            for text in result["advice"]:

                st.warning(text)


        else:

            st.success(

                "今日は健康的な生活です😊"

            )





    # ==========================
    # 過去履歴
    # ==========================


    st.write("---")


    st.subheader(

        "📅 過去の健康記録"

    )



    records = get_health_records(

        username

    )



    if records:



        df = pd.DataFrame(

            records,

            columns=[

                "日付",

                "体重",

                "最高血圧",

                "最低血圧",

                "水分",

                "健康スコア"

            ]

        )



        st.dataframe(

            df,

            width="stretch"

        )



        # ======================
        # 体重推移
        # ======================


        st.subheader(

            "⚖️ 体重推移"

        )


        chart_df = df.sort_values(

            "日付"

        )


        st.line_chart(

            chart_df.set_index(

                "日付"

            )[

                "体重"

            ]

        )



        # ======================
        # 血圧推移
        # ======================


        st.subheader(

            "❤️ 血圧推移"

        )


        st.line_chart(

            chart_df.set_index(

                "日付"

            )[

                [

                    "最高血圧",

                    "最低血圧"

                ]

            ]

        )



        # ======================
        # 健康スコア推移
        # ======================


        st.subheader(

            "🌟 健康スコア推移"

        )


        st.line_chart(

            chart_df.set_index(

                "日付"

            )[

                "健康スコア"

            ]

        )



    else:


        st.info(

            "まだ健康記録がありません"

        )